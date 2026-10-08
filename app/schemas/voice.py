from pydantic import BaseModel, Field


class VoiceProfileResponse(BaseModel):
    voice_id: str
    name: str
    sample_path: str
    language: str
    transcript_hint: str | None = None
    engine: str


class VoiceProfileListResponse(BaseModel):
    items: list[VoiceProfileResponse]


class VoiceTranscriptionResponse(BaseModel):
    text: str
    backend: str
    source_path: str


class VoiceSynthesizeRequest(BaseModel):
    text: str = Field(min_length=1)
    voice_id: str = Field(min_length=1)
    language: str = "es"


class VoiceSynthesizeResponse(BaseModel):
    output_path: str
    backend: str
    voice_id: str
    message: str


class AudioChatResponse(BaseModel):
    session_id: str
    transcript: str
    answer: str
    synthesized_audio_path: str | None = None
    voice_id: str | None = None
