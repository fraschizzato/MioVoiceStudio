from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Float, Boolean, DateTime
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class VoiceSession(Base):
    __tablename__ = "voice_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="Session")
    main_text: Mapped[str] = mapped_column(Text)
    cue_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="DRAFT", index=True)
    error: Mapped[str] = mapped_column(Text, default="")
    main_file: Mapped[str] = mapped_column(String(500), default="")
    cue_file: Mapped[str] = mapped_column(String(500), default="")
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    cue_duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    voice_name: Mapped[str] = mapped_column(String(100), default="reference")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
