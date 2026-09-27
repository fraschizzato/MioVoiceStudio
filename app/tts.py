from __future__ import annotations
import re, subprocess, threading
from pathlib import Path
import numpy as np
import soundfile as sf
from .config import settings

_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")

def split_text(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[str] = []
    buf = ""
    def push(piece: str):
        nonlocal buf
        if not buf:
            buf = piece
        elif len(buf) + 2 + len(piece) <= max_chars:
            buf += "\n\n" + piece
        else:
            out.append(buf)
            buf = piece
    for p in paragraphs:
        if len(p) <= max_chars:
            push(p)
            continue
        for s in _SENTENCE_RE.split(p):
            s=s.strip()
            if not s: continue
            if len(s) <= max_chars:
                push(s)
            else:
                words=s.split()
                cur=""
                for w in words:
                    candidate=(cur+" "+w).strip()
                    if len(candidate) > max_chars and cur:
                        push(cur); cur=w
                    else: cur=candidate
                if cur: push(cur)
    if buf: out.append(buf)
    return out

class QwenCloneEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._model = None
        self._clone_prompt = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        if not settings.reference_wav.exists():
            raise RuntimeError(f"Reference voice missing: {settings.reference_wav}. Upload a reference WAV or FLAC file from the Studio UI.")
        if not settings.reference_text.exists():
            raise RuntimeError(f"Reference transcript missing: {settings.reference_text}")
        import torch
        from qwen_tts import Qwen3TTSModel
        dtype = torch.bfloat16 if settings.tts_device.startswith("cuda") else torch.float32
        self._model = Qwen3TTSModel.from_pretrained(
            settings.tts_model,
            device_map=settings.tts_device,
            dtype=dtype,
        )
        ref_text = settings.reference_text.read_text(encoding="utf-8").strip()
        self._clone_prompt = self._model.create_voice_clone_prompt(
            ref_audio=str(settings.reference_wav),
            ref_text=ref_text,
            x_vector_only_mode=False,
        )

    def invalidate_reference(self):
        with self._lock:
            self._clone_prompt = None
            self._model = None

    def synthesize(self, text: str, out_base: Path) -> tuple[Path, float]:
        with self._lock:
            self._ensure_loaded()
            chunks = split_text(text, settings.chunk_chars)
            wave_parts=[]; sr=None
            for i, chunk in enumerate(chunks):
                wavs, chunk_sr = self._model.generate_voice_clone(
                    text=chunk,
                    language=settings.tts_language,
                    voice_clone_prompt=self._clone_prompt,
                    do_sample=True,
                    top_k=50,
                    top_p=1.0,
                    temperature=0.85,
                    repetition_penalty=1.05,
                )
                arr=np.asarray(wavs[0], dtype=np.float32)
                if sr is None: sr=chunk_sr
                wave_parts.append(arr)
                if i != len(chunks)-1:
                    wave_parts.append(np.zeros(int(sr*0.32), dtype=np.float32))
            merged=np.concatenate(wave_parts) if wave_parts else np.zeros(1,dtype=np.float32)
            wav_path=out_base.with_suffix('.wav')
            m4a_path=out_base.with_suffix('.m4a')
            sf.write(wav_path, merged, sr)
            speed=max(0.5,min(2.0,settings.tts_speed))
            cmd=['ffmpeg','-y','-loglevel','error','-i',str(wav_path),'-filter:a',f'atempo={speed}','-c:a','aac','-b:a','128k',str(m4a_path)]
            subprocess.run(cmd,check=True)
            try: wav_path.unlink()
            except OSError: pass
            duration=(len(merged)/sr)/speed
            return m4a_path,duration

engine = QwenCloneEngine()
