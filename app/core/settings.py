from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ARIA_", extra="ignore")

    app_name: str = "ARIA"
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    ollama_base_url: str = "http://127.0.0.1:11434"
    planner_model: str = "qwen3:8b"
    coder_model: str = "qwen2.5-coder:7b"
    sqlite_path: str = "storage/aria.db"
    workspace_dir: str = "workspaces/projects"
    voice_profiles_dir: str = "storage/voice_profiles"
    voice_outputs_dir: str = "storage/voice_outputs"
    allow_shell: bool = False
    max_tool_iterations: int = Field(default=4, ge=1, le=10)
    voice_backend: str = "xttsv2"
    stt_backend: str = "faster-whisper"
    enable_native_apps: bool = True

    enable_cors: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    enable_api_key: bool = False
    api_key: str | None = None

    enable_rate_limit: bool = True
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)

    voice_max_upload_mb: int = Field(default=50, ge=1, le=2048)
    voice_allowed_extensions: list[str] = Field(default_factory=lambda: ["wav", "mp3", "m4a", "ogg"])

    voice_outputs_ttl_hours: int = Field(default=24, ge=1, le=24 * 365)
    auto_cleanup_on_startup: bool = True

    auto_migrate: bool = True

    @property
    def sqlite_path_abs(self) -> Path:
        return Path(self.sqlite_path).resolve()

    @property
    def workspace_dir_abs(self) -> Path:
        return Path(self.workspace_dir).resolve()

    @property
    def voice_profiles_dir_abs(self) -> Path:
        return Path(self.voice_profiles_dir).resolve()

    @property
    def voice_outputs_dir_abs(self) -> Path:
        return Path(self.voice_outputs_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
