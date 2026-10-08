# ARIA

ARIA es un asistente personal local con arquitectura dual y fase 2 nativa:

- `Qwen 3` como planner y router principal
- `Qwen 2.5-Coder` como especialista en generacion de codigo
- `FastAPI` como API local
- `Ollama` como runtime de modelos
- `SQLite` para memoria persistente
- `Flutter` para app de escritorio y app movil
- Perfiles de voz y chat por audio

## Estructura

```text
app/
  api/
  core/
  memory/
  models/
  prompts/
  schemas/
  services/
  tools/
storage/
workspaces/projects/
tests/
clients/aria_native/
docs/
```

## Requisitos

- Python 3.12 o superior
- Ollama instalado y en ejecucion
- Modelos descargados:
  - `qwen3:8b`
  - `qwen2.5-coder:7b`

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Modelos

```bash
ollama pull qwen3:8b
ollama pull qwen2.5-coder:7b
```

## Ejecucion

```bash
uvicorn app.main:app --reload
```

## Despliegue en Ubuntu Server

- Plantilla `systemd`: `deploy/aria.service`
- Script de instalacion: `scripts/install_aria_ubuntu.sh`
- Script de drivers NVIDIA: `scripts/install_nvidia_ubuntu.sh`
- Guia paso a paso: `docs/ubuntu-server-setup.md`
- Transferencia e instalacion completa: `docs/transfer-and-install.md`

## Voz

Instalacion minima para subir audios y perfiles:

```bash
pip install -r requirements.txt
```

Si quieres activar transcripcion local real:

```bash
pip install -r requirements-voice.txt
```

## Endpoints Iniciales

- `GET /health`
- `POST /chat`
- `POST /task/run`
- `POST /project/create`
- `GET /voice/profiles`
- `POST /voice/profiles`
- `POST /voice/transcribe`
- `POST /voice/synthesize`
- `POST /voice/chat`

## Flujo Base

1. El usuario envia un prompt a `POST /chat`.
2. El router decide si la tarea es general o de codigo.
3. `Qwen 3` planifica y puede usar herramientas.
4. `Qwen 2.5-Coder` entra cuando la tarea requiere generar o editar codigo.
5. La sesion se guarda en `SQLite`.

## Notas

- El shell esta desactivado por defecto por seguridad.
- Todas las herramientas trabajan dentro de `workspaces/projects`.
- La app nativa esta en `clients/aria_native`.
- La guia de clonacion de voz esta en `docs/voice-cloning.md`.
- Este repositorio es un MVP funcional y ampliable.
