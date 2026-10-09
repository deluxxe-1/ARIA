from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import UploadFile

from app.core.settings import Settings
from app.api.routes_voice import _validate_upload
from app.core.errors import InvalidUploadError, UploadTooLargeError


def _make_upload(filename: str, content: bytes, size: int | None = None) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        size=len(content) if size is None else size,
        headers={"content-type": "application/octet-stream"},
    )


@pytest.mark.asyncio
async def test_validate_upload_rejects_bad_extension() -> None:
    settings = Settings()
    upload = _make_upload("virus.exe", b"X")
    with pytest.raises(InvalidUploadError):
        await _validate_upload(upload, settings)


@pytest.mark.asyncio
async def test_validate_upload_allows_allowed_extension_case_insensitive() -> None:
    settings = Settings()
    upload = _make_upload("AUDIO.WAV", b"RIFF....")
    await _validate_upload(upload, settings)


@pytest.mark.asyncio
async def test_validate_upload_rejects_oversize_via_file_size_attribute() -> None:
    settings = Settings(voice_max_upload_mb=1)
    big_size = 2 * 1024 * 1024 + 1
    upload = _make_upload("song.mp3", b"", size=big_size)
    with pytest.raises(UploadTooLargeError):
        await _validate_upload(upload, settings)
