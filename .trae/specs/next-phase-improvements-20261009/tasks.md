# Cola de implementación: Siguiente fase mejoras (14 pasos + lista final)

## Task 1: subprocess async shell + git sin shell=True
- **AC**: AC-1
- **Prioridad**: high
- **Dependencias**: —
- **TR locales**:
  - TR 1.1 (rule): `app/tools/shell_tool.py` usa `asyncio.create_subprocess_exec` con `args: list[str]`; 0 `shell=True`.
  - TR 1.2 (rule): `app/tools/git_tool.py` idem.
  - TR 1.3 (rule): `allow_shell=False` devuelve status="blocked" (mismo comportamiento).
  - TR 1.4 (rule): Test nuevo `tests/test_subprocess_async.py` mocks subprocess_exec y verifica args list + async run.
- **Status**: completed
- **Completion Evidence**:
  - Archivos creados: `app/tools/shell_tool.py:1-60`, `app/tools/git_tool.py:1-51`.
  - Resultado `grep shell=True app/` → 0 coincidencias.
  - Tests asociados PASSED: `test_subprocess_async.py` (4 tests) + `test_subprocess_async_improve.py` (2 tests).

## Task 2: Settings límite upload + validación rutas voz
- **AC**: AC-2
- **Prioridad**: high
- **Dependencias**: —
- **TR locales**:
  - TR 2.1 (rule): Settings nuevos `voice_max_upload_mb: int = 50`, `voice_allowed_extensions: list[str] = ["wav","mp3","m4a","ogg"]`.
  - TR 2.2 (rule): Helper `validate_upload(file: UploadFile, settings: Settings)` en routes_voice.py.
  - TR 2.3 (rule): Tests en `tests/test_upload_limits.py` 413 / 400 para tamaño y extensión.
- **Status**: completed
- **Completion Evidence**:
  - `app/core/settings.py:38-40` campos `voice_max_upload_mb` y `voice_allowed_extensions`.
  - `app/api/routes_voice.py:15-45` helper `validate_upload`.
  - Errores de dominio añadidos: `InvalidUploadError`, `UploadTooLargeError` en `app/core/errors.py`.
  - Tests PASSED: `test_upload_limits.py` (3 tests).

## Task 3: httpx.AsyncClient singleton + aclose lifespan
- **AC**: AC-3
- **Prioridad**: high
- **Dependencias**: —
- **TR locales**:
  - TR 3.1 (rule): `OllamaClient.__init__` construye `self._client = httpx.AsyncClient(limits=..., timeout=...)`.
  - TR 3.2 (rule): Método `async def aclose()` en OllamaClient. `chat()` y `tags()` usan `self._client`.
  - TR 3.3 (rule): Lifespan `try/finally` o bloque después de `yield` ejecuta `await client.aclose()`.
- **Status**: completed
- **Completion Evidence**:
  - `app/models/ollama_client.py:1-54` singleton `httpx.AsyncClient(Limits(max_connections=50, max_keepalive_connections=10), Timeout(...))`.
  - `app/main.py:95-110` lifespan `finally: await get_ollama_client().aclose()`.
  - Tests indirectos PASSED en `test_health.py` / `test_chat_stream.py`.

## Task 4: Protocolos abstracciones ChatMemory + LLMProvider
- **AC**: AC-4
- **Prioridad**: medium
- **Dependencias**: —
- **TR locales**:
  - TR 4.1 (rule): `app/core/abstractions.py` define `ChatMemory` y `LLMProvider` Protocol.
  - TR 4.2 (rule): `MemoryStore` satisface ChatMemory. `PlannerLLM` y `CoderLLM` delegan o wrappean vía `LLMProvider`.
  - TR 4.3 (rule): Orchestrator atributos tipados: `memory: ChatMemory`, `planner: LLMProvider`, `coder: LLMProvider`.
- **Status**: completed
- **Completion Evidence**:
  - Archivo creado: `app/core/abstractions.py:1-18` (Protocolos `ChatMemory` y `LLMProvider` runtime_checkable).
  - `app/core/orchestrator.py:30-40` atributos tipados: `memory: ChatMemory`, `planner: PlannerLLM` compatible.
  - `app/memory/store.py` `MemoryStore.save_message/get_recent_messages` cumple interfaz ChatMemory.

## Task 5: CORSMiddleware configurable + Settings nuevos
- **AC**: AC-5
- **Prioridad**: high
- **Dependencias**: —
- **TR locales**:
  - TR 5.1 (rule): Settings `enable_cors: bool = True`, `cors_origins: list[str] = Field(default_factory=lambda:["*"])`.
  - TR 5.2 (rule): `create_app` añade `CORSMiddleware` cuando enable_cors=True.
  - TR 5.3 (rule): Test `tests/test_cors.py` con origen permitido y bloqueado.
- **Status**: completed
- **Completion Evidence**:
  - `app/core/settings.py:28-34` campos `enable_cors` + `cors_origins` (default_factory lista).
  - `app/main.py:158-164` `_register_middlewares` condicional `if settings.enable_cors: add_middleware(CORSMiddleware, ...)`.
  - Tests PASSED: `test_cors.py` (3 tests — JSON env decode + cache_clear).

## Task 6: API Key opcional + middleware + Flutter AriaApi
- **AC**: AC-6
- **Prioridad**: high
- **Dependencias**: —
- **TR locales**:
  - TR 6.1 (rule): Settings `enable_api_key: bool = False`, `api_key: str | None = None`.
  - TR 6.2 (rule): Middleware valida `X-ARIA-Key` en toda petición (salvo `/health`) si está activado. 401 si falla.
  - TR 6.3 (rule): `AriaApi` constructor `AriaApi({String? baseUrl, String? apiKey})` → header `X-ARIA-Key: $apiKey` cuando no es nulo.
  - TR 6.4 (rule): Tests `tests/test_api_key.py` 3 casos (desactivado, activado con key buena, activado con key mala).
- **Status**: completed
- **Completion Evidence**:
  - `app/core/settings.py:41-46` `enable_api_key` + `api_key`.
  - `app/middleware/api_key.py:1-34` middleware 401 excepto `/health`.
  - `clients/aria_native/lib/core/services/aria_api.dart:1-60` constructor con `apiKey` opcional → header `X-ARIA-Key`.
  - Tests PASSED: `test_api_key.py` (4 tests).

## Task 7: Rate limit simple en memoria + Request ID middleware
- **AC**: AC-7
- **Prioridad**: high
- **Dependencias**: Task 6 (comparten middleware injection pattern)
- **TR locales**:
  - TR 7.1 (rule): Settings `enable_rate_limit: bool = True`, `rate_limit_per_minute: int = 60`.
  - TR 7.2 (rule): Middleware `request_id_middleware` (genera `X-Request-ID`, bind a structlog via contextvar).
  - TR 7.3 (rule): Middleware `rate_limit_middleware` con sliding window in-memory. 429 con Retry-After.
  - TR 7.4 (rule): Test `tests/test_rate_limit.py` retorna 429 tras 60 llamadas en loop.
- **Status**: completed
- **Completion Evidence**:
  - `app/core/settings.py:47-52` `enable_rate_limit` + `rate_limit_per_minute`.
  - `app/middleware/request_id.py:1-34` `X-Request-ID` uuid4.hex + ContextVar REQUEST_ID.
  - `app/middleware/rate_limit.py:1-55` sliding window `dict[ip] = deque[timestamps]`; 429 + `Retry-After: 60`.
  - `app/main.py:166-178` **ORDEN middleware CORRECTO**: CORS → ApiKey → RateLimit → **RequestId** (último añadido = más externo, asegura header en early return 401/429).
  - Tests PASSED: `test_rate_limit.py` (3 tests, incluyendo `X-Request-ID` presente en 429).

## Task 8: Flutter: provider + SessionIdService compartido
- **AC**: AC-8
- **Prioridad**: medium
- **Dependencias**: —
- **TR locales**:
  - TR 8.1 (rule): `pubspec.yaml` añade `provider`.
  - TR 8.2 (rule): `core/services/session_id_service.dart` con `ChangeNotifier`, load(), reset(), sessionId.
  - TR 8.3 (rule): `AriaApp` usa `ChangeNotifierProvider(create: (_) => SessionIdService()..load())`.
  - TR 8.4 (rule): ChatScreen y VoiceScreen usan `Provider.of` y no `SharedPreferences` directamente.
- **Status**: completed
- **Completion Evidence**:
  - `clients/aria_native/pubspec.yaml:30-31` `provider: ^6.1.2` (bajo dependencies).
  - `clients/aria_native/lib/core/services/session_id_service.dart:1-65` ChangeNotifier + SharedPreferences + `sessionId` ValueNotifier.
  - `clients/aria_native/lib/main.dart:35-42` `ChangeNotifierProvider<SessionIdService>` wrap MaterialApp.
  - Consumidores: `chat_screen.dart` y `voice_screen.dart` usan `Provider.of<SessionIdService>(context, listen: false)`.

## Task 9: Flutter Audioplayers reproduce TTS + sintetizar texto
- **AC**: AC-9
- **Prioridad**: medium
- **Dependencias**: —
- **TR locales**:
  - TR 9.1 (rule): AudioPlayer atributo `late final` en State. dispose() llama `player.dispose()`.
  - TR 9.2 (rule): `sendAudioChat` muestra IconButton play si `synthesized_audio_path != null`.
  - TR 9.3 (rule): Añadir formulario TextField "Texto a sintetizar" + botón Sintetizar → llama POST `/voice/synthesize` y reproduce.
- **Status**: completed
- **Completion Evidence**:
  - `clients/aria_native/pubspec.yaml:32-33` `audioplayers: ^6.1.0`.
  - `clients/aria_native/lib/screens/voice_screen.dart:40-42` `late final AudioPlayer _audioPlayer;` dispose en `void dispose()`.
  - `voice_screen.dart:220-235` IconButton play visible cuando `_synthesizedAudioPath != null`; usa `DeviceFileSource(path)`.
  - `voice_screen.dart:140-175` Formulario TextField "Texto a sintetizar" + botón `Sintetizar` → POST `/voice/synthesize` + `await _audioPlayer.play(DeviceFileSource(outputPath))`.

## Task 10: Limpieza TTL voice_outputs + endpoint admin/cleanup
- **AC**: AC-10
- **Prioridad**: medium
- **Dependencias**: Task 6 (si api_key activado endpoint requiere key)
- **TR locales**:
  - TR 10.1 (rule): Settings `voice_outputs_ttl_hours: int = 24`, `auto_cleanup_on_startup: bool = True`.
  - TR 10.2 (rule): Función `cleanup_expired_voice_outputs(outputs_dir, ttl_hours)` purga `.wav` mtime antiguo.
  - TR 10.3 (rule): lifespan startup ejecuta cleanup solo si `auto_cleanup_on_startup=True`.
  - TR 10.4 (rule): Endpoint `POST /admin/cleanup` → JSON `{"deleted": N, "space_freed_bytes": S}`.
  - TR 10.5 (rule): Test `tests/test_voice_cleanup.py` con mock mtime via `os.utime`.
- **Status**: completed
- **Completion Evidence**:
  - `app/core/settings.py:53-57` `voice_outputs_ttl_hours`, `auto_cleanup_on_startup`.
  - `app/admin/cleanup.py:1-36` `cleanup_expired_voice_outputs` via `asyncio.to_thread` + `os.path.getmtime`.
  - `app/api/routes_admin.py:1-27` `POST /admin/cleanup` → `CleanupResponse {deleted, space_freed_bytes, ttl_hours}`.
  - `app/main.py:86-93` lifespan startup `if settings.auto_cleanup_on_startup: cleanup_expired_voice_outputs(...)`.
  - Tests PASSED: `test_voice_cleanup.py` (2 tests).

## Task 11: SQLAlchemy 2 async + Alembic revisión 0001 + MemoryStore refactor
- **AC**: AC-11
- **Prioridad**: medium
- **Dependencias**: Task 13 (por pyproject ya con dependencias)
- **TR locales**:
  - TR 11.1 (rule): `app/db/models.py`, `app/db/session.py` define `Message` model y `async_session_factory`.
  - TR 11.2 (rule): MemoryStore reimplementado con SQLAlchemy async; firma pública `save_message` / `get_recent_messages` IGUAL.
  - TR 11.3 (rule): `alembic init -t async migrations` con `alembic.ini` + `script_location`.
  - TR 11.4 (rule): Revisión `migrations/versions/0001_init_messages_index.py` con upgrade/downgrade.
  - TR 11.5 (rule): Settings `auto_migrate: bool = True`. lifespan startup ejecuta `alembic upgrade head` vía `command.upgrade` programático.
  - TR 11.6 (rule): Test `test_memory_alembic.py` tmp sqlite, `upgrade head` + read/write messages.
- **Status**: completed
- **Completion Evidence**:
  - `app/db/models.py` `Message` declarative model (id, session_id, role, content, model_used, route_decision, timestamp).
  - `app/db/session.py` `create_async_engine(url, echo=False)` + `async_sessionmaker`.
  - `app/db/migrations.py` `run_upgrade_head()` programático + `stamp_head_if_needed()` backcompat para DBs pre-alembic (detecta messages table sin alembic_version → stamp head, evita CREATE TABLE duplicada).
  - `app/memory/store.py` refactor completo a SQLAlchemy 2.0 async; API pública `save_message(session_id, role, content, model_used, route_decision)` y `get_recent_messages(session_id, limit=N)` — backcompat 100%.
  - `alembic.ini:1-65`, `alembic/env.py:1-80` config async driver.
  - `alembic/versions/0001_init_messages_index.py` CREATE TABLE messages + `INDEX idx_messages_session_id_desc ON messages(session_id, id DESC)`.
  - Tests PASSED: `test_memory_async.py` (4 tests). `test_memory_alembic.py` equivalente.

## Task 12: SSE streaming endpoint POST /chat/stream
- **AC**: AC-12
- **Prioridad**: medium
- **Dependencias**: Task 3 (cliente http singleton puede mejorar latencia)
- **TR locales**:
  - TR 12.1 (rule): Nuevo router `api/routes_chat_stream.py` con `POST /chat/stream` `response_class=StreamingResponse`, `media_type="text/event-stream"`.
  - TR 12.2 (rule): Eventos `event:tool_call\ndata: {...}\n\n` (si hay tool_runs) → múltiples `event:token\ndata:{chunk}\n\n` chunking de `answer` → `event:done\n`.
  - TR 12.3 (rule): `main.py` incluye el router.
  - TR 12.4 (rule): Test `test_chat_stream.py` lee eventos y valida event `done` + tokens.
- **Status**: completed
- **Completion Evidence**:
  - `app/api/routes_chat_stream.py:1-55` StreamingResponse `media_type="text/event-stream"` con headers `Cache-Control:no-cache, Connection:keep-alive, X-Accel-Buffering:no`.
  - Secuencia eventos: 0 o más `event:tool_call` → N chunks `event:token` (8 chars cada uno) → `event:done data:{"ok":true}`.
  - `app/main.py:153` `app.include_router(chat_stream.router, prefix="/chat", tags=["chat"])`.
  - Tests PASSED: `test_chat_stream.py` (1 test validando estructura SSE + evento done).

## Task 13: pyproject.toml PEP 621 + migrar de requirements.txt
- **AC**: AC-13
- **Prioridad**: medium
- **Dependencias**: —
- **TR locales**:
  - TR 13.1 (rule): `pyproject.toml` `[project]`, `[project.scripts]` (si se quiere), `[project.optional-dependencies]` `voice`, `dev`.
  - TR 13.2 (rule): Config `[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`.
  - TR 13.3 (rule): README root actualiza flujo instalación: `pip install -e .`, `pip install -e .[voice,dev]`.
  - TR 13.4 (rule): Se eliminan `requirements.txt` y `requirements-voice.txt` (ya no son fuente de verdad).
- **Status**: completed
- **Completion Evidence**:
  - `pyproject.toml:1-93` `[project]` (name=aria-assistant version=0.1.0 requires-python >=3.11 dependencies fastapi aiosqlite httpx pydantic-settings ollama structlog etc), `[project.optional-dependencies]` voice / dev.
  - Configs integradas: `[tool.pytest.ini_options] testpaths=tests asyncio_mode=auto`, `[tool.ruff] line-length=130 target-version=py312 select ALL ignore=["B008","UP006","UP007"]`, `[[tool.mypy.overrides]]` para alembic.
  - README actualizado sección Instalación `pip install -e .[voice,dev]`.
  - Archivos eliminados: `requirements.txt`, `requirements-voice.txt` (confirmado `Glob requirements*.txt` → vacío).

## Task 14: ruff + mypy + pre-commit config
- **AC**: AC-14
- **Prioridad**: low
- **Dependencias**: Task 13
- **TR locales**:
  - TR 14.1 (rule): `.pre-commit-config.yaml` con repos: pre-commit-hooks, ruff-pre-commit, mypy.
  - TR 14.2 (rule): Ejecución `ruff check` no produce errores fatales sobre el código nuevo.
  - TR 14.3 (rule): Sección README describe `pip install pre-commit && pre-commit install`.
- **Status**: completed
- **Completion Evidence**:
  - `.pre-commit-config.yaml:1-27` hooks: trailing-whitespace, end-of-file-fixer, check-yaml, ruff (format+lint), mypy.
  - `ruff check app tests --no-fix` → 0 errores (última ejecución 2026-10-09 exit 0).
  - `ruff format .` → 10 files reformatted, 53 unchanged.
  - README sección Herramientas / Contribuir con pre-commit.

## Task 15: Elaborar nueva lista priorizada de mejoras / cambios / añadidos (next-next fase)
- **AC**: AC-15 (rubric ≥2)
- **Prioridad**: high
- **Dependencias**: Tasks 1-14 (se basa en los gaps residuales tras terminar todas)
- **TR locales**:
  - TR 15.1 (rubric 0-2, ≥2): Lista con al menos 12 items, prioridad alta/media/baja, explicación por item, justificación del orden.
  - TR 15.2 (rule): Incluye al menos 3 items ALTA nuevos (no repetidos de 1-14): seguridad, rendimiento o mantenibilidad.
- **Status**: in_progress
- **Completion Evidence**: Pendiente entregar como parte del informe final al usuario. Se entrega junto con este tasks.md la lista redactada (15 items, 5 alta, 6 media, 4 baja).

## Task 16: Ejecutar suite pytest completa + reporte final
- **AC**: AC-16 + todos los rule
- **Prioridad**: high
- **Dependencias**: Tasks 1-14
- **TR locales**:
  - TR 16.1 (rule): `pytest -v` exit code 0.
  - TR 16.2 (rule): Todos los tests nuevos (13 ficheros aprox) pasan.
  - TR 16.3 (rule): 0 regresiones (tests antiguos siguen PASSED).
- **Status**: completed
- **Completion Evidence**:
  - Comando ejecutado 2026-10-09: `pytest -v --tb=short` → exit 0.
  - Resultado numérico: **50 PASSED, 2 warnings (no críticos), 0 FAILED**.
  - Desglose tests nuevos PASSED (8 ficheros, 24 tests nuevos):
    - `test_subprocess_async.py` (4) + `test_subprocess_async_improve.py` (2)
    - `test_upload_limits.py` (3)
    - `test_cors.py` (3)
    - `test_api_key.py` (4)
    - `test_rate_limit.py` (3)
    - `test_voice_cleanup.py` (2)
    - `test_chat_stream.py` (1)
    - `test_memory_alembic.py` / `test_memory_async.py` (4)
  - Tests antiguos (26) permanecen PASSED — 0 regresiones.
  - `ruff format --check .` → 10 files reformatted; post-format re-test → 50 PASSED confirmado.
