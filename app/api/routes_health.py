from fastapi import APIRouter, Request


router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "app": settings.app_name,
        "planner_model": settings.planner_model,
        "coder_model": settings.coder_model,
        "voice_backend": settings.voice_backend,
        "stt_backend": settings.stt_backend,
    }
