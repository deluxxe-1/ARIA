import asyncio
import time
from pathlib import Path

from app.core.logger import get_logger

_logger = get_logger(__name__)


def cleanup_expired_voice_outputs(outputs_dir: Path, ttl_hours: int) -> tuple[int, int]:
    outputs_dir = Path(outputs_dir)
    if not outputs_dir.exists():
        return 0, 0

    threshold = time.time() - (ttl_hours * 3600)
    deleted = 0
    freed = 0

    wav_paths = [p for p in outputs_dir.glob("*.wav") if p.is_file()]
    for path in wav_paths:
        try:
            st = path.stat()
            if st.st_mtime < threshold:
                size = st.st_size
                path.unlink()
                deleted += 1
                freed += int(size)
        except OSError as exc:
            _logger.warning("cleanup_skip_file_failed", path=str(path), exc=str(exc))
    return deleted, freed


async def cleanup_expired_voice_outputs_async(outputs_dir: Path, ttl_hours: int) -> tuple[int, int]:
    return await asyncio.to_thread(cleanup_expired_voice_outputs, outputs_dir, ttl_hours)
