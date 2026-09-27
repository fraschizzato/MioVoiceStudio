from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    title: str = Field(default="New session", max_length=200)
    main_text: str = Field(min_length=1)
    cue_text: str = ""
    generate_now: bool = True

class SessionUpdate(BaseModel):
    title: str | None = None
    main_text: str | None = None
    cue_text: str | None = None

class SessionOut(BaseModel):
    id: str
    title: str
    main_text: str
    cue_text: str
    status: str
    error: str
    duration_s: float
    cue_duration_s: float
    voice_name: str
    published: bool
    created_at: str
    updated_at: str
    main_url: str | None = None
    cue_url: str | None = None
