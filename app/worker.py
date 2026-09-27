from __future__ import annotations
import queue, threading, shutil
from pathlib import Path
from .db import SessionLocal
from .models import VoiceSession
from .config import settings
from .tts import engine

_jobs: queue.Queue[str] = queue.Queue()
_started=False
_lock=threading.Lock()

def enqueue(session_id: str):
    _jobs.put(session_id)


def _run_one(session_id: str):
    with SessionLocal() as db:
        s=db.get(VoiceSession, session_id)
        if not s: return
        s.status='GENERATING'; s.error=''; db.commit()
        folder=settings.media_dir/session_id
        folder.mkdir(parents=True,exist_ok=True)
        try:
            main_path,main_dur=engine.synthesize(s.main_text,folder/'main')
            cue_path=None; cue_dur=0.0
            if s.cue_text.strip():
                cue_path,cue_dur=engine.synthesize(s.cue_text,folder/'cue')
            s.main_file=str(main_path)
            s.cue_file=str(cue_path) if cue_path else ''
            s.duration_s=main_dur; s.cue_duration_s=cue_dur
            s.status='READY'; s.error=''
        except Exception as e:
            s.status='ERROR'; s.error=f'{type(e).__name__}: {e}'
        db.commit()


def _loop():
    while True:
        sid=_jobs.get()
        try: _run_one(sid)
        finally: _jobs.task_done()


def start_worker():
    global _started
    with _lock:
        if _started: return
        _started=True
        t=threading.Thread(target=_loop,name='tts-worker',daemon=True)
        t.start()
        with SessionLocal() as db:
            for s in db.query(VoiceSession).filter(VoiceSession.status.in_(['PENDING','GENERATING'])).all():
                s.status='PENDING'; db.commit(); enqueue(s.id)
