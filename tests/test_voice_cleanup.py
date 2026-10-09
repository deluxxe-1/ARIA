import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.admin.cleanup import cleanup_expired_voice_outputs
from app.main import create_app


def test_cleanup_expired_voice_outputs_tmpdir(tmp_path: Path) -> None:
    outputs = Path(tmp_path)

    new_wav = outputs / "new.wav"
    new_wav.write_bytes(b"0" * 100)

    old_wav = outputs / "old.wav"
    old_wav.write_bytes(b"0" * 200)
    t_old = time.time() - 48 * 3600
    os.utime(old_wav, (t_old, t_old))

    not_wav = outputs / "not_wav.txt"
    not_wav.write_text("este archivo no se borra")

    deleted, freed = cleanup_expired_voice_outputs(outputs, ttl_hours=24)

    assert deleted == 1
    assert freed >= 200
    assert "old.wav" not in os.listdir(outputs)
    assert "new.wav" in os.listdir(outputs)
    assert "not_wav.txt" in os.listdir(outputs)


def test_post_admin_cleanup_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_WORKSPACE_DIR", str(tmp_path / "workspaces" / "projects"))
    monkeypatch.setenv("ARIA_SQLITE_PATH", str(tmp_path / "storage" / "aria.db"))
    monkeypatch.setenv("ARIA_VOICE_PROFILES_DIR", str(tmp_path / "storage" / "voice_profiles"))
    monkeypatch.setenv("ARIA_VOICE_OUTPUTS_DIR", str(tmp_path / "storage" / "voice_outputs"))
    monkeypatch.setenv("ARIA_ENABLE_RATE_LIMIT", "false")
    monkeypatch.setenv("ARIA_AUTO_CLEANUP_ON_STARTUP", "false")

    from app.core.settings import get_settings
    get_settings.cache_clear()

    app = create_app()
    voice_outputs_dir = app.state.settings.voice_outputs_dir_abs
    voice_outputs_dir.mkdir(parents=True, exist_ok=True)

    old_wav = voice_outputs_dir / "expired.wav"
    old_wav.write_bytes(b"0" * 300)
    t_old = time.time() - 48 * 3600
    os.utime(old_wav, (t_old, t_old))

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/admin/cleanup")

    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data
    assert "space_freed_bytes" in data
    assert "ttl_hours" in data
    assert isinstance(data["deleted"], int)
    assert isinstance(data["space_freed_bytes"], int)
    assert isinstance(data["ttl_hours"], int)
