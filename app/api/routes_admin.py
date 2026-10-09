from pydantic import BaseModel
from fastapi import APIRouter, Request

from app.admin.cleanup import cleanup_expired_voice_outputs_async


router = APIRouter(prefix="/admin", tags=["admin"])


class AdminCleanupResponse(BaseModel):
    deleted: int
    space_freed_bytes: int
    ttl_hours: int


@router.post("/cleanup", response_model=AdminCleanupResponse)
async def admin_cleanup(request: Request) -> AdminCleanupResponse:
    settings = request.app.state.settings
    deleted, freed = await cleanup_expired_voice_outputs_async(
        outputs_dir=settings.voice_outputs_dir_abs,
        ttl_hours=settings.voice_outputs_ttl_hours,
    )
    return AdminCleanupResponse(
        deleted=deleted,
        space_freed_bytes=freed,
        ttl_hours=settings.voice_outputs_ttl_hours,
    )
