from pathlib import Path
from uuid import uuid4

from app.core.orchestrator import Orchestrator
from app.schemas.chat import ChatRequest
from app.schemas.voice import (
    AudioChatResponse,
    VoiceProfileListResponse,
    VoiceProfileResponse,
    VoiceSynthesizeResponse,
    VoiceTranscriptionResponse,
)
from app.voice.profile_store import VoiceProfileStore
from app.voice.speech_service import SpeechService


class VoiceService:
    def __init__(
        self,
        profile_store: VoiceProfileStore,
        speech_service: SpeechService,
        orchestrator: Orchestrator,
    ) -> None:
        self.profile_store = profile_store
        self.speech_service = speech_service
        self.orchestrator = orchestrator

    def create_profile(
        self,
        *,
        name: str,
        language: str,
        transcript_hint: str | None,
        audio_bytes: bytes,
        filename: str,
    ) -> VoiceProfileResponse:
        return self.profile_store.create_profile(
            name=name,
            language=language,
            transcript_hint=transcript_hint,
            audio_bytes=audio_bytes,
            original_filename=filename,
        )

    def list_profiles(self) -> VoiceProfileListResponse:
        return VoiceProfileListResponse(items=self.profile_store.list_profiles())

    async def transcribe_upload(self, audio_bytes: bytes, filename: str) -> VoiceTranscriptionResponse:
        temp_path = self.speech_service.outputs_dir / f"transcribe_{uuid4().hex}_{filename}"
        temp_path.write_bytes(audio_bytes)
        try:
            return await self.speech_service.transcribe_audio(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

    async def synthesize_text(
        self,
        *,
        text: str,
        voice_id: str,
        language: str,
    ) -> VoiceSynthesizeResponse:
        profile = self.profile_store.get_profile(voice_id)
        return await self.speech_service.synthesize(text=text, profile=profile, language=language)

    async def audio_chat(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        session_id: str | None,
        voice_id: str | None,
    ) -> AudioChatResponse:
        transcript = await self.transcribe_upload(audio_bytes=audio_bytes, filename=filename)
        chat_result = await self.orchestrator.handle_chat(
            ChatRequest(
                prompt=transcript.text,
                session_id=session_id,
                allow_tools=True,
            )
        )

        synthesized_audio_path: str | None = None
        if voice_id:
            synthesis = await self.synthesize_text(
                text=chat_result.answer,
                voice_id=voice_id,
                language="es",
            )
            synthesized_audio_path = synthesis.output_path

        return AudioChatResponse(
            session_id=chat_result.session_id,
            transcript=transcript.text,
            answer=chat_result.answer,
            synthesized_audio_path=synthesized_audio_path,
            voice_id=voice_id,
        )
