import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.errors import VoiceBackendError
from app.voice.speech_service import SpeechService


class _FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeWhisperModel:
    INSTANCES_CREATED = 0

    def __init__(self, *args: object, **kwargs: object) -> None:
        _FakeWhisperModel.INSTANCES_CREATED += 1

    def transcribe(self, audio_path: str, language: str):  # type: ignore[override]
        return (
            [_FakeSegment(f" transcribed-{Path(audio_path).name} with lang {language} ")],
            {"language": language},
        )


@pytest.fixture(autouse=True)
def _reset_instance_counter() -> None:
    _FakeWhisperModel.INSTANCES_CREATED = 0


def _patch_faster_whisper(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = _FakeWhisperModel  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)


def test_whisper_model_is_singleton(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_faster_whisper(monkeypatch)
    service = SpeechService(outputs_dir=tmp_path, stt_backend="faster-whisper", voice_backend="xttsv2")
    audio_1 = tmp_path / "a.wav"
    audio_1.write_bytes(b"fake")
    audio_2 = tmp_path / "b.wav"
    audio_2.write_bytes(b"fake2")

    import asyncio

    asyncio.run(service.transcribe_audio(audio_1))
    asyncio.run(service.transcribe_audio(audio_2))

    assert _FakeWhisperModel.INSTANCES_CREATED == 1


def test_missing_faster_whisper_raises_voice_backend_error(tmp_path: Path) -> None:
    service = SpeechService(outputs_dir=tmp_path, stt_backend="faster-whisper", voice_backend="xttsv2")
    audio = tmp_path / "x.wav"
    audio.write_bytes(b"x")
    import asyncio

    with pytest.raises(VoiceBackendError):
        asyncio.run(service.transcribe_audio(audio))


def test_unknown_stt_backend_raises_voice_backend_error(tmp_path: Path) -> None:
    service = SpeechService(outputs_dir=tmp_path, stt_backend="no-existo", voice_backend="xttsv2")
    audio = tmp_path / "x.wav"
    audio.write_bytes(b"x")
    import asyncio

    with pytest.raises(VoiceBackendError):
        asyncio.run(service.transcribe_audio(audio))
