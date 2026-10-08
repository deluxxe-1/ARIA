# Cola de implementación: Corrección problemas alta prioridad

## Task 1: Añadir dependencias y crear módulo de errores de dominio
- **Prioridad**: high
- **AC cubiertos**: AC-4 (parcial)
- **Dependencias**: —
- **Status**: completed

### Completion Evidence
- TR 1.1 (rule): [requirements.txt](file:///c:/Users/deluxXe/Documents/ARIA/requirements.txt#L1-L13) → línea 11: `aiosqlite==0.20.0`, línea 13: `pytest-asyncio==0.24.0`.
- TR 1.2 (rule): [pubspec.yaml](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/pubspec.yaml#L10-L16) → línea 16: `shared_preferences: ^2.3.2`.
- TR 1.3 (rule): [app/core/errors.py](file:///c:/Users/deluxXe/Documents/ARIA/app/core/errors.py#L1-L19) → 5 excepciones, todas heredan de `ARIAError(Exception)`.

---

## Task 2: Migrar MemoryStore de sqlite3 síncrono a aiosqlite asíncrono + índice
- **Prioridad**: high
- **AC cubiertos**: AC-1, AC-3
- **Dependencias**: Task 1
- **Status**: completed

### Completion Evidence
- TR 2.1 (rule): [store.py](file:///c:/Users/deluxXe/Documents/ARIA/app/memory/store.py#L1-L84) → `_init_db`, `save_message`, `get_recent_messages` son `async def` y usan `aiosqlite.connect`.
- TR 2.2 (rule): [store.py](file:///c:/Users/deluxXe/Documents/ARIA/app/memory/store.py#L24-L31) → `CREATE INDEX IF NOT EXISTS idx_messages_session_id_id ON messages(session_id, id DESC)`.
- TR 2.3 (rule): [orchestrator.py](file:///c:/Users/deluxXe/Documents/ARIA/app/core/orchestrator.py#L30-L66) → líneas 32, 35, 60: tres lugares con `await memory.*`. [main.py](file:///c:/Users/deluxXe/Documents/ARIA/app/main.py#L36-L82) → línea 45: `await memory._init_db()`.
- TR 2.4 (rule): `tests/test_memory_async.py` 4 tests pasando (test_init_db_creates_index, test_save_and_recent_messages_order, test_recent_messages_isolation_per_session, test_save_message_keeps_model_and_route). Evidencia pytest final: 27 PASSED.

---

## Task 3: WhisperModel singleton en SpeechService
- **Prioridad**: high
- **AC cubiertos**: AC-2
- **Dependencias**: —
- **Status**: completed

### Completion Evidence
- TR 3.1 (rule): [speech_service.py](file:///c:/Users/deluxXe/Documents/ARIA/app/voice/speech_service.py#L1-L61). `self._whisper_model: Any | None = None` (línea 16) inicializado en `__init__`. Un único `WhisperModel(...)` en [línea 27](file:///c:/Users/deluxXe/Documents/ARIA/app/voice/speech_service.py#L23-L28) dentro de `_get_whisper_model()` con guard `self._whisper_model is not None: return self._whisper_model`.
- TR 3.2 (rule): `tests/test_speech_service.py::test_whisper_model_is_singleton` PASSED → crea servicio, llama `transcribe_audio` 2 veces, assert `INSTANCES_CREATED == 1`.

---

## Task 4: Handlers de errores HTTP globales + propagación excepciones de dominio
- **Prioridad**: high
- **AC cubiertos**: AC-4
- **Dependencias**: Task 1
- **Status**: completed

### Completion Evidence
- TR 4.1 (rule): [policies.py](file:///c:/Users/deluxXe/Documents/ARIA/app/core/policies.py#L1-L13) → línea 11 lanza `WorkspaceBoundaryError`; 0 ocurrencias de `ValueError` en el archivo.
- TR 4.2 (rule): [profile_store.py](file:///c:/Users/deluxXe/Documents/ARIA/app/voice/profile_store.py#L55-L58) → línea 58 lanza `ProfileNotFoundError`; 0 `FileNotFoundError` en el archivo.
- TR 4.3 (rule): `tests/test_errors.py` 5/5 tests PASSED, con TestClient verificando status codes 403/404/400/503/500 y JSON `{"detail": "..."}`.
- TR 4.4 (rule): `test_unhandled_exception_maps_to_500_without_leak` PASSED → body contiene mensaje genérico y NINGÚN path absoluto del host ni `Path.home()`.

---

## Task 5: Eliminar doble routeo en TaskService
- **Prioridad**: high
- **AC cubiertos**: AC-5
- **Dependencias**: —
- **Status**: completed

### Completion Evidence
- TR 5.1 (rule): [task_service.py](file:///c:/Users/deluxXe/Documents/ARIA/app/services/task_service.py#L1-L22). Resultado `grep -c '\.decide('` = 0.
- TR 5.2 (rule): línea 18 de [task_service.py](file:///c:/Users/deluxXe/Documents/ARIA/app/services/task_service.py#L17-L20) → `task_type=result.route` que proviene de `ChatResponse.route`.
- TR 5.3 (rule): [main.py:60](file:///c:/Users/deluxXe/Documents/ARIA/app/main.py#L59-L61) → `task_service = TaskService(orchestrator=orchestrator)` sin parámetro `router`.

---

## Task 6: Flutter session_id persistido + Nueva Conversación
- **Prioridad**: high
- **AC cubiertos**: AC-6
- **Dependencias**: Task 1
- **Status**: completed

### Completion Evidence
- TR 6.1 (rule): [aria_api.dart](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/core/services/aria_api.dart#L16-L36) → `sendChat` acepta `{String? sessionId}` y añade `body['session_id'] = sessionId` cuando no es nulo/vacío. También [sendAudioChat](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/core/services/aria_api.dart#L96-L121) incluye `session_id` field.
- TR 6.2 (rule): [chat_screen.dart](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/features/chat/presentation/chat_screen.dart#L16-L65) `_loadSessionId()` lee `SharedPreferences` con clave `aria_session_id` o crea nuevo UUID-style hex y persiste. [voice_screen.dart](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/features/voice/presentation/voice_screen.dart#L19-L58) idem.
- TR 6.3 (rule): [chat_screen.dart](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/features/chat/presentation/chat_screen.dart#L97-L113) `AppBar.actions` → `IconButton(Icons.add_comment_outlined)` llama `_resetSessionId()` que genera un nuevo ID y limpia `_messages`. SnackBar informativo.
- TR 6.4 (rule): diff Flutter muestra solo `shared_preferences: ^2.3.2` nueva dependencia. Ninguna otra dependencia añadida. IDs generados localmente con `Random.secure` 16 bytes hex.

---

## Task 7: Flutter baseUrl configurable vía --dart-define
- **Prioridad**: high
- **AC cubiertos**: AC-7
- **Dependencias**: —
- **Status**: completed

### Completion Evidence
- TR 7.1 (rule): [aria_api.dart](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/lib/src/core/services/aria_api.dart#L11-L15) →
  ```dart
  baseUrl = baseUrl ??
      const String.fromEnvironment(
        'ARIA_API_URL',
        defaultValue: 'http://127.0.0.1:8000',
      );
  ```
- TR 7.2 (rule): [clients/aria_native/README.md](file:///c:/Users/deluxXe/Documents/ARIA/clients/aria_native/README.md) completamente reescrito documentando: flutter run con `--dart-define=ARIA_API_URL=http://10.0.2.2:8000` para Android Emulator, uso en dispositivo real con IP LAN, y persistencia de `aria_session_id`.

---

## Task 8: Añadir tests de integración y unitarios
- **Prioridad**: high
- **AC cubiertos**: AC-1, AC-2, AC-3, AC-4, AC-8
- **Dependencias**: Tasks 2-5
- **Status**: completed

### Completion Evidence
- TR 8.1 (rule): pytest final exit code 0, 27 passed.
- TR 8.2 (rule): 8 archivos de test (7 nuevos):
  - [test_router.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_router.py) (3 tests: code/research/general routes)
  - [test_policies.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_policies.py) (5 tests: workspace boundary casos)
  - [test_tool_gateway.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_tool_gateway.py) (5 tests: normalize_arguments + unknown tool)
  - [test_memory_async.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_memory_async.py) (4 tests: índice, orden, aislamiento, metadata)
  - [test_speech_service.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_speech_service.py) (3 tests: singleton, missing faster-whisper, unknown backend)
  - [test_task_service.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_task_service.py) (1 test async: task_type proveniente ChatResponse.route)
  - [test_errors.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_errors.py) (5 tests: handlers HTTP)
  - [test_health.py](file:///c:/Users/deluxXe/Documents/ARIA/tests/test_health.py) (existente)
- TR 8.3 (rule): [pytest.ini](file:///c:/Users/deluxXe/Documents/ARIA/pytest.ini) con `asyncio_mode = auto` + `requirements.txt` incluye `pytest-asyncio==0.24.0`.

---

## Task 9: Ejecutar suite completa y validar regresiones
- **Prioridad**: high
- **AC cubiertos**: AC-8, AC-9
- **Dependencias**: Tasks 1-8
- **Status**: completed

### Completion Evidence
- TR 9.1 (rule): `pytest -v --tb=short` exit code 0 → log final: `27 passed, 1 warning in 1.95s`.
- TR 9.2 (rubric AC-9) → **Score 2/2**
  - Justificación:
    1. No se introdujeron TODO/FIXME (verificado con grep global).
    2. Cada corrección sigue los estilos del proyecto: español en comentarios y textos de error, Pydantic para schemas, tipado Python 3.12 (`str | None`), `async/await` idiomático, PEP8.
    3. Flutter: mismo patrón StatefulWidget + Material 3 + NavigationBar; SharedPreferences integrado siguiendo estilo existente.
    4. Sin regresiones: 27/27 tests pasando, incluyendo el test original de salud.
    5. No breaking en contratos REST: `session_id` ya existía y era opcional; formato errores JSON `{"detail": "..."}` compatible con FastAPI.
    6. Sin dependencias innecesarias (solo 2 nuevas justificadas: `aiosqlite` y `shared_preferences`, más `pytest-asyncio` para testing).
