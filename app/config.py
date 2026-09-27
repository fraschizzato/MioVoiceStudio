from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("DATA_DIR", "/data"))
    app_token: str = os.getenv("APP_TOKEN", "").strip()
    tts_device: str = os.getenv("TTS_DEVICE", "cuda:0")
    tts_model: str = os.getenv("TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")
    tts_language: str = os.getenv("TTS_LANGUAGE", "Italian")
    tts_speed: float = float(os.getenv("TTS_SPEED", "0.94"))
    chunk_chars: int = int(os.getenv("TTS_CHUNK_CHARS", "850"))
    reference_wav: Path = Path(os.getenv("TTS_REFERENCE_WAV", "/data/voices/reference.wav"))
    reference_text: Path = Path(os.getenv("TTS_REFERENCE_TEXT", "/data/voices/reference.txt"))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "mio_voice.sqlite3"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.media_dir.mkdir(parents=True, exist_ok=True)
settings.reference_wav.parent.mkdir(parents=True, exist_ok=True)
