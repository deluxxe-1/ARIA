from contextlib import asynccontextmanager

from app.admin.cleanup import cleanup_expired_voice_outputs_async
from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_projects import router as projects_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_voice import router as voice_router
from app.core.errors import (
    ARIAError,
    InvalidUploadError,
    ProfileNotFoundError,
    RateLimitError,
    ToolNotSupportedError,
    UnauthorizedError,
    UploadTooLargeError,
    VoiceBackendError,
    WorkspaceBoundaryError,
)
from app.core.logger import configure_logging, get_logger
from app.core.orchestrator import Orchestrator
from app.core.router import TaskRouter
from app.core.settings import get_settings
from app.core.tool_gateway import ToolGateway
from app.memory.store import MemoryStore
from app.middleware.api_key import ApiKeyMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.models.coder_llm import CoderLLM
from app.models.ollama_client import OllamaClient
from app.models.planner_llm import PlannerLLM
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.voice_service import VoiceService
from app.voice.profile_store import VoiceProfileStore
from app.voice.speech_service import SpeechService
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.workspace_dir_abs.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path_abs.parent.mkdir(parents=True, exist_ok=True)
    settings.voice_profiles_dir_abs.mkdir(parents=True, exist_ok=True)
    settings.voice_outputs_dir_abs.mkdir(parents=True, exist_ok=True)

    if settings.auto_cleanup_on_startup:
        try:
            deleted, freed = await cleanup_expired_voice_outputs_async(
                outputs_dir=settings.voice_outputs_dir_abs,
                ttl_hours=settings.voice_outputs_ttl_hours,
            )
            _logger.info(
                "voice_outputs_startup_cleanup_done",
                deleted=deleted,
                space_freed_bytes=freed,
            )
        except Exception as exc:
            _logger.warning("voice_outputs_startup_cleanup_failed", exc=str(exc))

    memory = MemoryStore(settings.sqlite_path_abs)
    if settings.auto_migrate:
        await memory._init_db()
    router = TaskRouter()
    client = OllamaClient(settings.ollama_base_url)
    planner = PlannerLLM(client=client, model_name=settings.planner_model)
    coder = CoderLLM(client=client, model_name=settings.coder_model)
    tool_gateway = ToolGateway(settings=settings)
    orchestrator = Orchestrator(
        settings=settings,
        memory=memory,
        router=router,
        planner=planner,
        coder=coder,
        tool_gateway=tool_gateway,
    )
    project_service = ProjectService(settings=settings)
    task_service = TaskService(orchestrator=orchestrator)
    voice_profile_store = VoiceProfileStore(
        profiles_dir=settings.voice_profiles_dir_abs,
        default_engine=settings.voice_backend,
    )
    speech_service = SpeechService(
        outputs_dir=settings.voice_outputs_dir_abs,
        stt_backend=settings.stt_backend,
        voice_backend=settings.voice_backend,
    )
    voice_service = VoiceService(
        profile_store=voice_profile_store,
        speech_service=speech_service,
        orchestrator=orchestrator,
    )

    app.state.settings = settings
    app.state.orchestrator = orchestrator
    app.state.project_service = project_service
    app.state.task_service = task_service
    app.state.voice_service = voice_service
    app.state.ollama_client = client

    try:
        yield
    finally:
        try:
            await client.aclose()
        except Exception as exc:
            _logger.warning("ollama_client_close_failed", exc=str(exc))


async def _workspace_boundary_handler(request: Request, exc: WorkspaceBoundaryError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


async def _profile_not_found_handler(request: Request, exc: ProfileNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def _tool_not_supported_handler(request: Request, exc: ToolNotSupportedError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def _voice_backend_handler(request: Request, exc: VoiceBackendError) -> JSONResponse:
    _logger.error("voice_backend_error", message=str(exc))
    return JSONResponse(status_code=503, content={"detail": "Backend de voz no disponible temporalmente."})


async def _upload_too_large_handler(request: Request, exc: UploadTooLargeError) -> JSONResponse:
    return JSONResponse(status_code=413, content={"detail": str(exc)})


async def _invalid_upload_handler(request: Request, exc: InvalidUploadError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def _unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc) or "No autorizado."})


async def _rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": str(exc) or "Demasiadas peticiones en poco tiempo."},
        headers={"Retry-After": "60"},
    )


async def _aria_error_handler(request: Request, exc: ARIAError) -> JSONResponse:
    _logger.warning("aria_error", error_type=type(exc).__name__, message=str(exc))
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _logger.exception("unhandled_exception", path=str(request.url), error_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrio un error interno procesando la solicitud."},
    )


def _register_middlewares(app: FastAPI) -> None:
    settings = app.state.settings if hasattr(app.state, "settings") else get_settings()

    if settings.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    app.add_middleware(ApiKeyMiddleware, settings=settings)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(RequestIdMiddleware)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings

    _register_middlewares(app)

    app.add_exception_handler(WorkspaceBoundaryError, _workspace_boundary_handler)
    app.add_exception_handler(ProfileNotFoundError, _profile_not_found_handler)
    app.add_exception_handler(ToolNotSupportedError, _tool_not_supported_handler)
    app.add_exception_handler(VoiceBackendError, _voice_backend_handler)
    app.add_exception_handler(UploadTooLargeError, _upload_too_large_handler)
    app.add_exception_handler(InvalidUploadError, _invalid_upload_handler)
    app.add_exception_handler(UnauthorizedError, _unauthorized_handler)
    app.add_exception_handler(RateLimitError, _rate_limit_handler)
    app.add_exception_handler(ARIAError, _aria_error_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(tasks_router)
    app.include_router(projects_router)
    app.include_router(voice_router)
    try:
        from app.api.routes_chat_stream import router as chat_stream_router
        app.include_router(chat_stream_router)
    except ImportError:
        pass
    app.include_router(admin_router)
    return app


app = create_app()
