from __future__ import annotations
import shutil, uuid
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from .config import settings
from .db import init_db, SessionLocal
from .models import VoiceSession
from .schemas import SessionCreate, SessionUpdate
from .auth import require_token, require_media_token
from .worker import start_worker, enqueue
from .tts import engine

app=FastAPI(title='Mio Voice Studio',version='0.2.0')
STATIC=Path(__file__).parent/'static'

@app.on_event('startup')
def startup():
    init_db(); start_worker()


def to_dict(s: VoiceSession):
    return {
        'id':s.id,'title':s.title,'main_text':s.main_text,'cue_text':s.cue_text,
        'status':s.status,'error':s.error,'duration_s':s.duration_s,'cue_duration_s':s.cue_duration_s,
        'voice_name':s.voice_name,'published':s.published,
        'created_at':s.created_at.isoformat(),'updated_at':s.updated_at.isoformat(),
        'main_url':f'/media/{s.id}/main' if s.main_file else None,
        'cue_url':f'/media/{s.id}/cue' if s.cue_file else None,
        'manifest_url':f'/api/sessions/{s.id}/manifest',
    }

@app.get('/health')
def health():
    return {'ok':True,'reference_voice':settings.reference_wav.exists()}

@app.get('/api/config/public')
def public_config():
    return {'voice':'reference','model':settings.tts_model,'language':settings.tts_language,
            'reference_voice_ready':settings.reference_wav.exists(),'speed':settings.tts_speed}

@app.get('/api/sessions')
def list_sessions(_:None=Depends(require_token)):
    with SessionLocal() as db:
        rows=db.scalars(select(VoiceSession).order_by(VoiceSession.created_at.desc())).all()
        return [to_dict(x) for x in rows]

@app.post('/api/sessions')
def create_session(body:SessionCreate,_:None=Depends(require_token)):
    sid=str(uuid.uuid4())
    s=VoiceSession(id=sid,title=body.title.strip() or 'Session',main_text=body.main_text.strip(),cue_text=body.cue_text.strip(),status='PENDING' if body.generate_now else 'DRAFT')
    with SessionLocal() as db:
        db.add(s); db.commit(); db.refresh(s)
    if body.generate_now: enqueue(sid)
    return to_dict(s)

@app.get('/api/sessions/{sid}')
def get_session(sid:str,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        return to_dict(s)

@app.put('/api/sessions/{sid}')
def update_session(sid:str,body:SessionUpdate,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        if s.status=='GENERATING': raise HTTPException(409,'Generation in progress')
        for k,v in body.model_dump(exclude_none=True).items(): setattr(s,k,v)
        s.status='DRAFT'; s.published=False; db.commit(); db.refresh(s); return to_dict(s)

@app.post('/api/sessions/{sid}/generate')
def generate(sid:str,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        if s.status in ('PENDING','GENERATING'): return to_dict(s)
        s.status='PENDING'; s.error=''; s.published=False; db.commit(); db.refresh(s)
    enqueue(sid); return to_dict(s)

@app.post('/api/sessions/{sid}/publish')
def publish(sid:str,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        if s.status!='READY': raise HTTPException(409,'Session is not ready')
        s.published=True; db.commit(); db.refresh(s); return to_dict(s)

@app.get('/api/sessions/{sid}/manifest')
def manifest(sid:str,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        return {
            'id':s.id,'title':s.title,'status':s.status,'published':s.published,
            'duration_s':s.duration_s,'main_url':f'/media/{s.id}/main' if s.main_file else None,
            'cue': {
                'text':s.cue_text,'duration_s':s.cue_duration_s,
                'url':f'/media/{s.id}/cue' if s.cue_file else None,
                'defaults':{'first_delay_minutes':60,'interval_minutes':90,'max_plays':4,'volume':0.18,'require_headphones':True}
            }
        }

@app.delete('/api/sessions/{sid}')
def delete_session(sid:str,_:None=Depends(require_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        if s.status=='GENERATING': raise HTTPException(409,'Generation in progress')
        db.delete(s); db.commit()
    shutil.rmtree(settings.media_dir/sid,ignore_errors=True)
    return {'ok':True}

@app.post('/api/voice/reference')
def upload_reference(file:UploadFile=File(...),reference_text:str|None=Form(default=None),_:None=Depends(require_token)):
    filename=(file.filename or '').lower()
    if not filename.endswith('.wav'):
        raise HTTPException(400,'Use a WAV reference file')
    settings.reference_wav.parent.mkdir(parents=True,exist_ok=True)
    with settings.reference_wav.open('wb') as out: shutil.copyfileobj(file.file,out)
    if reference_text and reference_text.strip(): settings.reference_text.write_text(reference_text.strip(),encoding='utf-8')
    engine.invalidate_reference()
    return {'ok':True,'path':str(settings.reference_wav)}

@app.post('/api/sessions/{sid}/upload/{kind}')
def upload_audio(sid:str,kind:str,file:UploadFile=File(...),_:None=Depends(require_token)):
    if kind not in ('main','cue'): raise HTTPException(400,'kind must be main or cue')
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        ext=Path(file.filename or '').suffix.lower() or '.m4a'
        dest=settings.media_dir/sid/f'{kind}{ext}'; dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('wb') as out: shutil.copyfileobj(file.file,out)
        if kind=='main': s.main_file=str(dest)
        else: s.cue_file=str(dest)
        s.published=False
        if s.main_file: s.status='READY'
        db.commit(); db.refresh(s); return to_dict(s)

@app.get('/media/{sid}/{kind}')
def media(sid:str,kind:str,_:None=Depends(require_media_token)):
    with SessionLocal() as db:
        s=db.get(VoiceSession,sid)
        if not s: raise HTTPException(404,'Session not found')
        path=s.main_file if kind=='main' else s.cue_file if kind=='cue' else ''
    if not path or not Path(path).exists(): raise HTTPException(404,'Audio not found')
    return FileResponse(path,media_type='audio/mp4',filename=Path(path).name)

app.mount('/static',StaticFiles(directory=STATIC),name='static')

@app.get('/')
def root():
    return FileResponse(STATIC/'index.html')
