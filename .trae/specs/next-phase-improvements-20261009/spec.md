# Especificación: Siguiente Fase de Mejoras en ARIA (Paso 1-14 sugeridos)

## Problema

Tras corregir los issues de alta prioridad, el proyecto mantiene 14 puntos pendientes que afectan a: estabilidad asíncrona en tools (subprocess), seguridad (shell=True, uploads sin límite), rendimiento (httpx sin pooling), capacidad LAN (CORS, auth, rate-limit), mantenibilidad (interfaces Protocol, gestión de estado Flutter), completitud features (reproducción audio, streaming tokens), limpieza storage, ciclo de vida build (pyproject + pre-commit), migraciones y trazabilidad (request_id).

El usuario solicita **implementar todos los pasos siguientes sugeridos** y luego **elaborar una nueva lista de mejoras/añadidos/cambios**.

## Usuarios

- Usuario final de ARIA (backend + app Flutter)
- Operador del servidor en LAN / escritorio
- Desarrollador que mantiene / extiende el proyecto

## Objetivos

1. Eliminar event-loop blocking de `shell_tool.py` y `git_tool.py` (pasar a async subprocess sin `shell=True`).
2. Limitar tamaño de UploadFile de audio + metadata sanitaria (tipos MIME).
3. `httpx.AsyncClient` singleton poolizado en `OllamaClient`.
4. Añadir `typing.Protocol` / `ABC` para `ChatMemory`, `LLMProvider` (planner/coder). Mantener backcompat.
5. CORS configurable via Settings (`cors_origins` lista) + middleware en create_app.
6. API Key opcional: Settings `api_key` + middleware. Toggle `enable_api_key`.
7. Rate limit por IP configurable + Request ID middleware (inyectado a structlog).
8. Gestión de estado Flutter con `provider` + `SessionIdService` compartido.
9. Reproducción de audio sintetizado con `audioplayers` (ya importado).
10. Limpieza TTL de `storage/voice_outputs/*.wav` > 24h configurable, ejecutada en lifespan startup y por endpoint de mantenimiento.
11. Refactor MemoryStore a **SQLAlchemy 2.0 async** + directorio `migrations/` Alembic con revisión inicial `0001_init_messages_index`.
12. Streaming SSE en endpoint nuevo `POST /chat/stream` con tokens progresivos.
13. Migrar `requirements.txt` a `pyproject.toml` PEP 621 (grupos de dependencias core/voice/dev).
14. Configuración `ruff` + `mypy` strict + archivo `.pre-commit-config.yaml` básico.
15. Elaborar al final una nueva lista priorizada de mejoras/cambios/añadidos de próxima fase.

## No Objetivos

- Cambiar de framework IA, modelo o runtime Ollama.
- Cambiar lenguaje del cliente Flutter.
- Añadir panel web.
- Añadir features de usuario no listadas (ej. gestión de usuarios multiusuario).
- Reescribir la app Flutter a otro state mgmt distinto de `provider` (mantenemos mínima invasión).

## Requisitos Funcionales

### RF-1 Subprocess asíncrono sin shell=True
- `shell_tool.run_shell_command()` usa `asyncio.create_subprocess_exec(*args, cwd=..., timeout=20, stdout=..., stderr=...)` con argumentos pasados como **lista**, **nunca `shell=True`**.
- `git_tool.git_status()` idem.
- Se conserva la política `allow_shell` y `ensure_within_workspace`.

### RF-2 Límite tamaño upload audio
- En `routes_voice.py`, al recibir `UploadFile` se valida que:
  - Extensión permitida: `.wav`, `.mp3`, `.m4a`, `.ogg` (coincidencia case-insensitive).
  - Tamaño ≤ `settings.voice_max_upload_mb` (default 50, configurable Settings).
- Si no cumple, se eleva excepción `ARIAError` → HTTP 413 / 400 según caso.

### RF-3 OllamaClient: httpx AsyncClient singleton
- `OllamaClient` construye **una sola vez** `httpx.AsyncClient(limits=httpx.Limits(max_connections=50, max_keepalive_connections=10), timeout=httpx.Timeout(connect=10, read=120, write=10, pool=5))` como atributo `self._client` en `__init__`.
- Método `aclose()` asíncrono en OllamaClient que cierra `self._client.aclose()`.
- Lifespan de FastAPI: `yield` cierra `await client.aclose()`.

### RF-4 Protocolos: ChatMemory y LLMProvider
- Crear `app/core/abstractions.py`:
  - `class ChatMemory(Protocol): async def save_message(...), async def get_recent_messages(...)`
  - `class LLMProvider(Protocol): async def chat(messages, tools, temperature) -> dict`
- `MemoryStore` sigue funcionando; Orchestrator tipa atributos via Protocol (no cambio de firma público).
- `PlannerLLM` y `CoderLLM` delegan en `LLMProvider` wrapper sobre `OllamaClient`.

### RF-5 CORS configurable
- Settings: `cors_origins: list[str] = Field(default_factory=lambda: ["*"])`
- Settings: `enable_cors: bool = True`
- En `create_app()`, si `enable_cors=True` → `CORSMiddleware(allow_origins=cors_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)`.

### RF-6 API Key opcional
- Settings: `api_key: str | None = None` (desactivado por defecto).
- Middleware: si `api_key` no es None/empty, toda petición (salvo `/health`) requiere header `X-ARIA-Key: <key>`. Si no coincide → 401 `{"detail": "API key invalida."}`.
- Afecta también Flutter: `AriaApi` acepta `apiKey` opcional en constructor y envía header `X-ARIA-Key`.

### RF-7 Rate limit + Request ID middleware
- Settings: `enable_rate_limit: bool = True`, `rate_limit_per_minute: int = 60`.
- Implementación simple en middleware propio (dict `ip -> [timestamps]`, no usa Redis porque es MVP local; limitado a single-worker).
- Request ID: middleware genera `X-Request-ID` uuid4hex si no viene; inyectar en `structlog` via `contextvars` / bind `request_id`.
- Exceder rate limit → HTTP 429 `{"detail": "Demasiadas peticiones en poco tiempo."}`.

### RF-8 Flutter provider + SessionIdService común
- Añadir dependencia `provider` a `pubspec.yaml`.
- Crear `core/services/session_id_service.dart` con `ChangeNotifier`: `sessionId`, `Future<void> load()`, `Future<void> reset()`, persiste en `SharedPreferences` (misma clave `aria_session_id`).
- Envolver `AriaApp` en `ChangeNotifierProvider`. `ChatScreen` y `VoiceScreen` leen `SessionIdService` via `Provider.of<SessionIdService>(context)`; ya no duplican lógica.

### RF-9 Audioplayers reproducción TTS
- `VoiceScreen` recibe `synthesized_audio_path` de `sendAudioChat`; también existe acción separada "Sintetizar texto" que llama `POST /voice/synthesize`.
- Usar `audioplayers` `AudioPlayer` como atributo Stateful; método `_play(String localPathOrUrl)`.
- UI: botón ▶️ reproducir al lado de la respuesta sintetizada y cuando el payload trae `synthesized_audio_path`.

### RF-10 Limpieza TTL archivos voice_outputs
- Settings: `voice_outputs_ttl_hours: int = 24`.
- En lifespan startup, ejecutar limpieza inicial asíncrona.
- Función `cleanup_expired_voice_outputs(outputs_dir: Path, ttl_hours: int)`: elimina archivos `.wav` con mtime > ttl.
- Endpoint nuevo `POST /admin/cleanup` (solo accesible con API key si está activada) que fuerza limpieza y devuelve `{"deleted": N, "space_freed_bytes": total}`.

### RF-11 SQLAlchemy async + Alembic
- Añadir `sqlalchemy[asyncio]>=2.0.36`, `alembic>=1.14` a dev dependencies.
- Crear `app/db/__init__.py`, `app/db/models.py` con `Message` declarative model, `app/db/session.py` `async_sessionmaker`.
- Refactor `MemoryStore` internamente a SQLAlchemy async. API pública `save_message` / `get_recent_messages` **sin cambios**.
- `alembic init migrations` con `async` template. Revisión `0001_init_messages_index` con CREATE TABLE + índice idéntico al actual.
- Script `alembic upgrade head` se ejecuta ahora en lifespan (opcional: toggle `auto_migrate=True` default).

### RF-12 Streaming SSE POST /chat/stream
- Endpoint nuevo: `POST /chat/stream` request body igual `ChatRequest`; respuesta `text/event-stream`.
- Eventos SSE: `event: token\ndata: {text}\n\n`, `event: tool_call\n...`, `event: done`.
- **Nota de alcance MVP**: Dado que Ollama se usa sin `stream=True` actualmente, implementamos el endpoint con **streaming chunked de respuesta final** (chunk size 8 chars) más evento tool_call si existen tool_runs y un evento done. Esto deja abierta la evolución futura a streaming token real.

### RF-13 pyproject.toml PEP 621
- Reemplazar `requirements.txt`, `requirements-voice.txt`, `README.md` metadata por único `pyproject.toml` con:
  - `[project]` nombre, versión 0.1.0, descripción, requires-python=">=3.12", authors.
  - `[project.optional-dependencies]` `voice = ["faster-whisper..."]`, `dev = ["pytest", "pytest-asyncio", "ruff", "mypy", "sqlalchemy[asyncio]", "alembic"]`.
  - `[tool.ruff]`, `[tool.mypy]`.
- Mantener `requirements.txt` generado backward-compatible? **No objetivo**: documentar paso a paso nuevo flujo `pip install -e .[dev]` y eliminar archivos duplicados (mantener uno solo pyproject.toml).

### RF-14 ruff + mypy + pre-commit
- Archivo `.pre-commit-config.yaml`: `pre-commit-hooks` (trailing-whitespace, end-of-file-fixer, check-json), `ruff` (format + check), `mypy`.
- Documentación mínima en README root: `pre-commit install`.

## Requisitos No Funcionales

### RNF-1 Compatibilidad hacia atrás (crítico)
- Todos los endpoints actuales (`/health`, `/chat`, `/task/run`, `/project/create`, `/voice/*`) deben seguir funcionando sin cambios en el request/response schema.
- Flutter sin `apiKey` y sin `--dart-define=...` debe seguir conectándose a local (defaults sin breaking).

### RNF-2 Rendimiento
- Tras RF-1: shell/git ya no bloquean asyncio.
- Tras RF-3: `httpx.AsyncClient` reutiliza conexiones TCP keep-alive → reducir time-to-first-token.
- RF-14: ruff/mypy deben ejecutarse en < 5s sobre el repo (config mínima, no excesivamente estricta).

### RNF-3 Seguridad
- shell=False obligatorio (nunca shell=True).
- límite tamaño upload configurable y activado por defecto.
- API key opcional con 401 claro; CORS cerrado solo a orígenes configurados.

### RNF-4 Sin deuda técnica nueva
- Todo nuevo código con typing estricto.
- Todo endpoint nuevo con test mínimo (al menos 1 test unitario/integrado).
- 0 TODO/FIXME introducidos.

### RNF-5 Sin dependencias no justificadas
- Cada nueva dependencia en pyproject tiene que tener justificación explícita.
- Flutter solo nuevas dependencias: `provider` (minimal, oficial).

## Restricciones y Suposiciones

- Suposición: El usuario acepta añadir sqlalchemy+alembic, httpx limits, slowapi no — rate limit simple en memoria.
- Suposición: single-process uvicorn (el rate limit es in-memory).
- Restricción: Alembic configurado pero upgrade head hecho solo si `auto_migrate=True`.
- Suposición: Streaming real por tokens de Ollama se deja como mejora futura; se entrega SSE con chunking y estructura de eventos lista.
- Restricción: provider es el gestor de estado elegido (mínimo cambio y soporte oficial Flutter).

## Preguntas Abiertas (resueltas por suposición)

1. ¿RF-11 Alembic/SQLAlchemy vale la pena ahora? → Sí, pero manteniendo API pública MemoryStore idéntica.
2. ¿SSE chunking o streaming Ollama real? → SSE con chunking MVP (menor riesgo, misma interfaz de eventos).
3. ¿Rate limit con `slowapi`/`limits` o custom? → Custom en memoria (sin dependencias extra).
4. State management Flutter: ¿Riverpod o Provider? → `provider` (más simple, menos invasivo, menos dependencias transitive).
5. ¿Eliminar `.txt` de requirements al pasar a pyproject? → Sí, pyproject es origen único y documentamos nuevo flujo.

---

## Criterios de Aceptación

### AC-1 (rule) shell/git subprocess async sin shell=True
- Pasos: grep `shell=True` y `subprocess.run` en `shell_tool.py`, `git_tool.py`.
- Prueba: 0 matches de `shell=True`; 0 matches de `subprocess.run`. Archivos usan `asyncio.create_subprocess_exec`.
- Evidencia: Código fuente + test que mockea `create_subprocess_exec` y valida args tipo lista.

### AC-2 (rule) Límite upload audio y extensión
- Pasos: POST `/voice/chat` y `/voice/profiles` con audio > 50MB vs audio con extensión `.exe`.
- Prueba: Status 413/400 según caso; respuesta JSON `{"detail": "..."}`.
- Evidencia: Tests `tests/test_upload_limits.py`.

### AC-3 (rule) OllamaClient httpx singleton
- Prueba: Existe `self._client = httpx.AsyncClient(...)` en `__init__`; una instancia por `OllamaClient`; método `aclose()`; lifespan espera `await client.aclose()` después del `yield`.
- Evidencia: Código fuente.

### AC-4 (rule) Protocol ChatMemory y LLMProvider
- Prueba: `app/core/abstractions.py` define `ChatMemory` y `LLMProvider` Protocol; `Orchestrator` tipa atributos con estos Protocol; tipado mypy pasa.
- Evidencia: Código fuente + mypy en CI (o ejecución local mypy OK).

### AC-5 (rule) CORS configurable
- Prueba: Settings `cors_origins = ["http://example.com"]` y petición con `Origin: http://evil.com` → headers CORS no presentes. Origin `http://example.com` → `Access-Control-Allow-Origin: http://example.com`.
- Evidencia: Test `tests/test_cors.py`.

### AC-6 (rule) API Key opcional
- Prueba: Settings `api_key = "secret"`; petición sin header → 401; con `X-ARIA-Key: secret` → pasa. Flutter AriaApi acepta apiKey en constructor y envía header.
- Evidencia: Tests `tests/test_api_key.py` + diff `aria_api.dart`.

### AC-7 (rule) Rate limit 429 + Request ID header
- Prueba: 61 peticiones en < 1 min → última retorna 429. Toda respuesta contiene header `X-Request-ID`.
- Evidencia: Tests `tests/test_rate_limit.py`.

### AC-8 (rule) Flutter Provider SessionIdService
- Prueba: ChatScreen y VoiceScreen NO leen SharedPreferences directamente; ambos usan `Provider.of<SessionIdService>`. Botón Nueva Conversación invoca `service.reset()` y ambas pantallas reciben actualización.
- Evidencia: Código fuente de pantallas + SessionIdService + pubspec.yaml provider.

### AC-9 (rule) Audioplayers reproduce sintetizado
- Prueba: `audioplayers` `AudioPlayer` atributo de State; cuando la respuesta trae `synthesized_audio_path` existe IconButton ▶️ reproducir que invoca `player.play(DeviceFileSource(path))`.
- Evidencia: Diff VoiceScreen / ChatScreen (si corresponde) y widget botón visible.

### AC-10 (rule) Limpieza TTL voice_outputs
- Prueba: Crear un `.wav` viejo (mockear mtime 48h); ejecutar cleanup; archivo no existe; `POST /admin/cleanup` retorna `deleted>=1`; lifespan startup lo realiza una vez.
- Evidencia: Test `tests/test_voice_cleanup.py`.

### AC-11 (rule) SQLAlchemy async + Alembic 0001
- Prueba: `alembic upgrade head` crea tabla `messages` y `idx_messages_session_id_id`. MemoryStore salva y lee mensajes vía SQLAlchemy; API pública idéntica (tipos, firmas).
- Evidencia: Migrations folder + test que ejecuta upgrade head y usa MemoryStore contra sqlite tmp.

### AC-12 (rule) Streaming SSE /chat/stream
- Prueba: `POST /chat/stream` con TestClient `stream=True`. Respuesta Content-Type `text/event-stream`. Al menos un evento `event: token\n` y `event: done`.
- Evidencia: Test `tests/test_chat_stream.py`.

### AC-13 (rule) pyproject.toml PEP 621 único origen metadata
- Prueba: `pyproject.toml` contiene `[project]`, `[project.optional-dependencies]` core/voice/dev. `pip install -e .[voice,dev]` instala todo. No existen `requirements.txt` duplicados (salvo README doc).
- Evidencia: Archivo pyproject y README root actualizado.

### AC-14 (rule) ruff + mypy + pre-commit config
- Prueba: `.pre-commit-config.yaml` con 3 hooks; `ruff check` y `mypy` corren sin errores graves sobre el código nuevo.
- Evidencia: Archivos de configuración + ejecución ruff/mypy OK.

### AC-15 (rubric) Calidad nueva lista de mejoras (0-2, ≥2)
- Dimensión: Pertinencia, priorización clara, ordenada por criticidad, basada en los gaps que queden tras implementar 1-14.
- Escala 0-2: 0 genérica / repetitiva; 1 razonable; 2 exhaustiva priorizada y accionable.
- Umbral: ≥2.
- Evidencia: Lista final entregada al usuario.

### AC-16 (rule) Tests totales pasan
- Prueba: `pytest -v` exit code 0.
- Evidencia: Log pytest final.
