from fastapi import APIRouter, File, Form, Request, UploadFile

from app.schemas.voice import (
    AudioChatResponse,
    VoiceProfileListResponse,
    VoiceProfileResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTranscriptionResponse,
)


router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/profiles", response_model=VoiceProfileListResponse)
async def list_profiles(request: Request) -> VoiceProfileListResponse:
    voice_service = request.app.state.voice_service
    return voice_service.list_profiles()


@router.post("/profiles", response_model=VoiceProfileResponse)
async def create_profile(
    request: Request,
    name: str = Form(...),
    language: str = Form("es"),
    transcript_hint: str | None = Form(None),
    sample: UploadFile = File(...),
) -> VoiceProfileResponse:
    voice_service = request.app.state.voice_service
    audio_bytes = await sample.read()
    return voice_service.create_profile(
        name=name,
        language=language,
        transcript_hint=transcript_hint,
        audio_bytes=audio_bytes,
        filename=sample.filename or "sample.wav",
    )


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
) -> VoiceTranscriptionResponse:
    voice_service = request.app.state.voice_service
    audio_bytes = await audio.read()
    return await voice_service.transcribe_upload(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.wav",
    )


@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
async def synthesize(
    payload: VoiceSynthesizeRequest,
    request: Request,
) -> VoiceSynthesizeResponse:
    voice_service = request.app.state.voice_service
    return await voice_service.synthesize_text(
        text=payload.text,
        voice_id=payload.voice_id,
        language=payload.language,
    )


@router.post("/chat", response_model=AudioChatResponse)
async def audio_chat(
    request: Request,
    audio: UploadFile = File(...),
    session_id: str | None = Form(None),
    voice_id: str | None = Form(None),
) -> AudioChatResponse:
    voice_service = request.app.state.voice_service
    audio_bytes = await audio.read()
    return await voice_service.audio_chat(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.wav",
        session_id=session_id,
        voice_id=voice_id,
    )
