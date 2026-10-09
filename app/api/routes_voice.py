from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.errors import InvalidUploadError, UploadTooLargeError
from app.core.settings import Settings
from app.schemas.voice import (
    AudioChatResponse,
    VoiceProfileListResponse,
    VoiceProfileResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTranscriptionResponse,
)


router = APIRouter(prefix="/voice", tags=["voice"])


async def _validate_upload(file: UploadFile, settings: Settings) -> None:
    filename = (file.filename or "file").lower()
    suffix = Path(filename).suffix.lstrip(".")
    allowed = {ext.lower() for ext in settings.voice_allowed_extensions}
    if suffix not in allowed:
        raise InvalidUploadError(
            f"Extension no permitida. Extensiones admitidas: {', '.join(sorted(allowed))}"
        )

    if file.size is not None and file.size > settings.voice_max_upload_mb * 1024 * 1024:
        raise UploadTooLargeError(
            f"Archivo demasiado grande. Limite: {settings.voice_max_upload_mb} MB."
        )


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
    settings: Settings = request.app.state.settings
    await _validate_upload(sample, settings)
    voice_service = request.app.state.voice_service
    audio_bytes = await sample.read()
    size_limit = settings.voice_max_upload_mb * 1024 * 1024
    if len(audio_bytes) > size_limit:
        raise UploadTooLargeError(
            f"Archivo demasiado grande. Limite: {settings.voice_max_upload_mb} MB."
        )
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
    settings: Settings = request.app.state.settings
    await _validate_upload(audio, settings)
    voice_service = request.app.state.voice_service
    audio_bytes = await audio.read()
    size_limit = settings.voice_max_upload_mb * 1024 * 1024
    if len(audio_bytes) > size_limit:
        raise UploadTooLargeError(
            f"Archivo demasiado grande. Limite: {settings.voice_max_upload_mb} MB."
        )
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
    settings: Settings = request.app.state.settings
    await _validate_upload(audio, settings)
    voice_service = request.app.state.voice_service
    audio_bytes = await audio.read()
    size_limit = settings.voice_max_upload_mb * 1024 * 1024
    if len(audio_bytes) > size_limit:
        raise UploadTooLargeError(
            f"Archivo demasiado grande. Limite: {settings.voice_max_upload_mb} MB."
        )
    return await voice_service.audio_chat(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.wav",
        session_id=session_id,
        voice_id=voice_id,
    )
