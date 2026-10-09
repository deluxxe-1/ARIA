from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.errors import VoiceBackendError
from app.schemas.voice import (
    VoiceProfileResponse,
    VoiceSynthesizeResponse,
    VoiceTranscriptionResponse,
)


class SpeechService:
    def __init__(self, outputs_dir: Path, stt_backend: str, voice_backend: str) -> None:
        self.outputs_dir = outputs_dir
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.stt_backend = stt_backend
        self.voice_backend = voice_backend
        self._whisper_model: Any | None = None

    def _get_whisper_model(self) -> Any:
        if self._whisper_model is not None:
            return self._whisper_model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise VoiceBackendError("Para transcribir audio instala 'pip install -r requirements-voice.txt'.") from exc

        self._whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
        return self._whisper_model

    async def transcribe_audio(self, audio_path: Path) -> VoiceTranscriptionResponse:
        if self.stt_backend == "faster-whisper":
            model = self._get_whisper_model()
            segments, _ = model.transcribe(str(audio_path), language="es")
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return VoiceTranscriptionResponse(
                text=text or "No se ha podido extraer texto del audio.",
                backend=self.stt_backend,
                source_path=str(audio_path),
            )

        raise VoiceBackendError(f"Backend STT no soportado: {self.stt_backend}")

    async def synthesize(
        self,
        *,
        text: str,
        profile: VoiceProfileResponse,
        language: str,
    ) -> VoiceSynthesizeResponse:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        output_path = self.outputs_dir / f"{profile.voice_id}_{timestamp}_{uuid4().hex[:8]}.wav"

        if self.voice_backend == "xttsv2":
            message = "Perfil listo para clonacion con XTTS v2. Conecta un runtime de TTS local para generar el wav definitivo."
            output_path.write_bytes(b"")
            return VoiceSynthesizeResponse(
                output_path=str(output_path),
                backend=self.voice_backend,
                voice_id=profile.voice_id,
                message=message,
            )

        raise VoiceBackendError(f"Backend de voz no soportado: {self.voice_backend}")
