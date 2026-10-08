# Especificación: Corrección de Problemas de Alta Prioridad en ARIA

## Problema

El proyecto ARIA presenta 7 problemas de alta prioridad identificados durante el análisis exhaustivo que afectan a:
- Estabilidad del servidor (IO bloqueante)
- Funcionamiento principal (sin historial de chat en el cliente Flutter, doble routeo redundante)
- Rendimiento crítico (carga del modelo Whisper por cada transcripción)
- Integridad de datos (falta de índice en tabla de mensajes)
- Experiencia de error (respuestas HTTP 500 genéricas en lugar de 404/400)
- Integración móvil (URL API hardcodeada incompatible con emuladores Android)

## Usuarios Afectados

- Usuario final del backend (cualquier consumidor de la API)
- Usuario de la app Flutter (desktop y móvil)
- Operador del servidor en entorno de producción / LAN

## Objetivos

1. Eliminar la bloqueo del event loop causado por SQLite síncrono.
2. Convertir el modelo de STT en singleton para evitar recargas por petición.
3. Añadir índice a la tabla `messages` para evitar full table scans.
4. Implementar jerarquía de errores de dominio y mapeos HTTP adecuados.
5. Eliminar el routeo redundante en `TaskService`.
6. Habilitar historial real de chat en Flutter mediante `session_id` persistido.
7. Hacer configurable la URL base del API en Flutter vía `--dart-define`.
8. Cubrir cada corrección con tests unitarios / de integración.
9. Ejecutar la suite completa de tests para asegurar ausencia de regresiones.

## No Objetivos

- Añadir nuevas características de usuario.
- Refactorizar la arquitectura de capas (ej. añadir ABCs / Protocol).
- Cambiar proveedor de modelos o framework de IA.
- Añadir autenticación, rate limit o CORS (quedan para siguiente fase).
- Migrar a `pyproject.toml`.

## Requisitos Funcionales

### RF-1 IO asíncrono en MemoryStore
- Todas las operaciones de `MemoryStore` deben ejecutarse sin bloquear el event loop de asyncio.
- El esquema de la tabla `messages` y su contrato de datos no debe variar.

### RF-2 Singleton Whisper
- `WhisperModel` debe instanciarse UNA sola vez durante el ciclo de vida de `SpeechService`.
- El modelo se carga en el método `__init__` (lazy init si falla import y no hay dependencia instalada, elevando RuntimeError solo en el momento de transcribir, como hasta ahora).
- El backend configurable via `stt_backend` debe seguir respetado.

### RF-3 Índice messages(session_id, id DESC)
- Al inicializar la BD se debe garantizar la existencia de un índice en `messages(session_id, id DESC)`.
- Inicializaciones sucesivas no deben fallar (idempotente).

### RF-4 Jerarquía de errores y mapeo HTTP
- Crear módulo `app/core/errors.py` con excepciones de dominio: `ARIAError` (base), `WorkspaceBoundaryError`, `ProfileNotFoundError`, `ToolNotSupportedError`, `VoiceBackendError`.
- Añadir handlers globales en FastAPI (`add_exception_handler`) que mapeen:
  - `ProfileNotFoundError` → 404
  - `WorkspaceBoundaryError` → 403
  - `ToolNotSupportedError` → 400
  - `ValueError`/`KeyError` genéricos → 400 (con mensaje seguro, no leak de internos)
  - Cualquier excepción no controlada → 500 con mensaje genérico y log structlog de la traza.
- Los mensajes de error devueltos al cliente deben ser JSON con al menos `{"detail": "..."}`.

### RF-5 Eliminar doble routeo en TaskService
- `TaskService.run()` NO debe invocar `router.decide()` por su cuenta; debe delegar 100% en `orchestrator.handle_chat()` (que ya routea internamente).
- El valor `task_type` de `TaskRunResponse` debe provenir del `ChatResponse.route` devuelto por orchestrator.

### RF-6 Flutter: session_id persistido y enviado
- El cliente Flutter debe generar un `session_id` (UUID v4 hex, igual que el backend) y persistirlo en disco (`SharedPreferences`).
- Cada `sendChat` debe incluir `session_id` en el body del POST.
- Debe existir un botón / acción explícita para "Nueva conversación" que genere y persista un nuevo session_id.

### RF-7 Flutter: baseUrl configurable vía --dart-define
- `AriaApi` debe leer `String.fromEnvironment('ARIA_API_URL', defaultValue: 'http://127.0.0.1:8000')`.
- Documentar en el README del cliente Flutter cómo pasar el valor (incluyendo `10.0.2.2` para Android Emulator).

### RF-8 Cobertura de tests
- Añadir tests unitarios para: TaskRouter, ensure_within_workspace, ToolGateway.normalize_arguments, MemoryStore (tmp_path), errores HTTP handlers.
- Añadir al menos 1 test de integración: `POST /chat` con `TestClient` (usando mocks de LLM si es necesario; o fallback a que falle por Ollama no disponible pero se compruebe el manejo de error).

### RF-9 Ejecución completa de tests
- `pytest` debe finalizar con exit code 0 después de aplicar todas las correcciones.

## Requisitos No Funcionales

### RNF-1 Compatibilidad hacia atrás
- Ningún contrato de API REST (endpoints, request/response schemas) debe cambiar excepto:
  - Añadir `session_id` opcional que ya existía y no era usado por Flutter (no breaking).
  - Formato de errores JSON consistente (cambio benigno).

### RNF-2 Sin nuevas dependencias no justificadas
- Única dependencia nueva permitida: `aiosqlite` (para RF-1). Si no fuera posible, implementar alternativa sin nueva dependencia justificándolo.
- En Flutter, única dependencia nueva permitida: `shared_preferences` (para RF-6).

### RNF-3 Rendimiento
- Después del fix, `WhisperModel` ya no se recarga entre transcripciones consecutivas.
- `get_recent_messages` con 10k filas debe aprovechar el índice (comprobable con `EXPLAIN QUERY PLAN` en test).

### RNF-4 Seguridad
- Los mensajes de error no deben exponer paths absolutos, stack traces ni detalles internos al cliente HTTP (sí al log).

### RNF-5 Calidad de código
- Seguir el estilo ya existente: español en comentarios internos, nombres en inglés cuando es convención (framework), typado estricto, PEP8, sin TODO/FIXME introducidos.

## Restricciones, Dependencias y Suposiciones

- Restricción: El shell sigue desactivado por defecto; no se toca la seguridad de sandbox.
- Dependencia: `aiosqlite` para Python.
- Dependencia Flutter: `shared_preferences`.
- Suposición: El entorno de tests local tiene Python 3.12 y puede instalar `aiosqlite`.
- Suposición: No hay despliegue productivo corriendo con volumen alto de datos; migración del índice es segura.
- Suposición: El usuario acepta añadir `aiosqlite` y `shared_preferences` a las dependencias.

## Preguntas Abiertas (resueltas por suposición)

1. ¿Añadimos `aiosqlite` a `requirements.txt`? → Sí.
2. ¿Se añade `shared_preferences` a `pubspec.yaml`? → Sí.
3. ¿Qué hacer con las transacciones? → Cada operación de MemoryStore abre su propia conexión/cursor asíncrona (igual que el código actual, versión asíncrona).

---

## Criterios de Aceptación

### AC-1 (rule) MemoryStore asíncrono no bloquea
- Pasos: Importar `app.memory.store.MemoryStore` y revisar firma de todos los métodos públicos (`__init__`, `_init_db`, `save_message`, `get_recent_messages`).
- Prueba: Todos los métodos que hacen IO son `async def` y usan `aiosqlite`.
- Evidencia: Código fuente de `app/memory/store.py` + test unitario `async` que escribe y lee 100 mensajes en < 2s (no timeouts de pytest-asyncio).

### AC-2 (rule) WhisperModel singleton
- Pasos: Inspeccionar `SpeechService.__init__` y `SpeechService.transcribe_audio`.
- Prueba: El modelo se asigna como atributo `self._whisper_model` en `__init__` o en lazy init único; no existe `WhisperModel(...)` dentro de `transcribe_audio`.
- Evidencia: Código fuente de `app/voice/speech_service.py`.

### AC-3 (rule) Índice en messages(session_id, id)
- Pasos: Conectar a una base de datos SQLite de prueba donde se haya ejecutado `_init_db`.
- Prueba: `PRAGMA index_list(messages)` devuelve al menos un índice cuyo DDL contenga `session_id` y `id DESC`.
- Evidencia: Test unitario que ejecuta PRAGMA y `EXPLAIN QUERY PLAN SELECT ... WHERE session_id=? ORDER BY id DESC LIMIT ?` y muestra `USING INDEX`.

### AC-4 (rule) Errores HTTP mapeados correctamente
- Pasos: Usar `TestClient` contra endpoints que produzcan errores.
- Prueba:
  - GET de perfil de voz inexistente (haciendo que `/voice/profiles/no_existo` falle vía un helper endpoint o llamando directamente a `get_profile` y capturando 404 con `HTTPException` / handler).
  - `WorkspaceBoundaryError` elevado desde herramienta devuelve 403.
  - Ninguna excepción devuelve stack trace en el body JSON.
- Evidencia: Tests en `tests/test_errors.py`.

### AC-5 (rule) TaskService no duplica routeo
- Pasos: Revisar `app/services/task_service.py`.
- Prueba: Una sola ocurrencia de `.decide(` en el archivo y `task_type` se toma de `chat_response.route`.
- Evidencia: Código fuente + test que simula una request y comprueba que Orchestrator.decide se llame 1 vez (usando mock/spy).

### AC-6 (rule) Flutter session_id persistido
- Pasos: Revisar `aria_api.dart` y `chat_screen.dart`.
- Prueba:
  - `sendChat` envía `"session_id"` en el body JSON.
  - El session_id se lee y escribe en `SharedPreferences`.
  - Existe acción para resetear session_id ("Nueva conversación").
- Evidencia: Código fuente + comentarios documentando la cadena.

### AC-7 (rule) Flutter baseUrl configurable
- Prueba: `AriaApi` constructor default usa `String.fromEnvironment('ARIA_API_URL')`.
- Evidencia: `aria_api.dart` + actualización `clients/aria_native/README.md`.

### AC-8 (rule) Todos los tests pasan
- Prueba: `pytest -q` ejecutado desde la raíz devuelve exit code 0.
- Evidencia: Log de ejecución pytest almacenado en evidencia.

### AC-9 (rubric) Calidad de la corrección
- Dimensión: Robustez, idiomático Python/Flutter, sin regresiones, sin deuda técnica introducida.
- Escala 0-2: 0 = introduce fallos / deuda; 1 = funcional pero con inconsistencias menores; 2 = limpio, sigue estilo del proyecto, tipado, comentado lo justo.
- Umbral de aprobación: ≥ 2.
- Evidencia: Revisión independiente de los diffs.
