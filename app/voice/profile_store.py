import json
from pathlib import Path

from slugify import slugify

from app.core.errors import ProfileNotFoundError
from app.schemas.voice import VoiceProfileResponse


class VoiceProfileStore:
    def __init__(self, profiles_dir: Path, default_engine: str) -> None:
        self.profiles_dir = profiles_dir
        self.default_engine = default_engine
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def create_profile(
        self,
        *,
        name: str,
        language: str,
        transcript_hint: str | None,
        audio_bytes: bytes,
        original_filename: str,
    ) -> VoiceProfileResponse:
        voice_id = slugify(name) or "voz"
        profile_dir = self.profiles_dir / voice_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(original_filename).suffix or ".wav"
        sample_path = profile_dir / f"sample{suffix}"
        sample_path.write_bytes(audio_bytes)

        metadata_path = profile_dir / "profile.json"
        metadata = {
            "voice_id": voice_id,
            "name": name,
            "sample_path": str(sample_path),
            "language": language,
            "transcript_hint": transcript_hint,
            "engine": self.default_engine,
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return VoiceProfileResponse(**metadata)

    def list_profiles(self) -> list[VoiceProfileResponse]:
        items: list[VoiceProfileResponse] = []
        for metadata_path in sorted(self.profiles_dir.glob("*/profile.json")):
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            items.append(VoiceProfileResponse(**data))
        return items

    def get_profile(self, voice_id: str) -> VoiceProfileResponse:
        metadata_path = self.profiles_dir / voice_id / "profile.json"
        if not metadata_path.exists():
            raise ProfileNotFoundError(f"No existe el perfil de voz '{voice_id}'.")
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        return VoiceProfileResponse(**data)
