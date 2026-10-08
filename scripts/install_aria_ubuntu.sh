#!/usr/bin/env bash

set -euo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
APP_USER="${APP_USER:-${SUDO_USER:-$USER}}"
SERVICE_NAME="${SERVICE_NAME:-aria}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PLANNER_MODEL="${PLANNER_MODEL:-qwen3:8b}"
CODER_MODEL="${CODER_MODEL:-qwen2.5-coder:7b}"
INSTALL_VOICE_DEPS="${INSTALL_VOICE_DEPS:-true}"

log() {
  echo
  echo "==> $1"
}

require_sudo() {
  if ! command -v sudo >/dev/null 2>&1; then
    echo "Este script necesita sudo." >&2
    exit 1
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"
  local file="$3"

  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    echo "${key}=${value}" >> "$file"
  fi
}

log "Comprobando sistema"
require_sudo

if [[ ! -f /etc/os-release ]]; then
  echo "No se puede detectar el sistema operativo." >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "Este script esta pensado para Ubuntu Server." >&2
  exit 1
fi

log "Actualizando paquetes base"
sudo apt update
sudo apt upgrade -y
sudo apt install -y \
  git \
  curl \
  ffmpeg \
  build-essential \
  ca-certificates \
  "${PYTHON_BIN}" \
  python3-venv \
  python3-pip

log "Instalando Ollama si hace falta"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

sudo systemctl enable ollama
sudo systemctl start ollama

log "Preparando entorno Python"
cd "$APP_DIR"

if [[ ! -d ".venv" ]]; then
  "${PYTHON_BIN}" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if [[ "${INSTALL_VOICE_DEPS}" == "true" && -f "requirements-voice.txt" ]]; then
  pip install -r requirements-voice.txt
fi

log "Preparando configuracion"
if [[ ! -f ".env" ]]; then
  cp .env.example .env
fi

mkdir -p storage/logs storage/cache storage/voice_profiles storage/voice_outputs workspaces/projects

set_env_value "ARIA_ENV" "production" ".env"
set_env_value "ARIA_HOST" "0.0.0.0" ".env"
set_env_value "ARIA_PORT" "8000" ".env"
set_env_value "ARIA_OLLAMA_BASE_URL" "http://127.0.0.1:11434" ".env"
set_env_value "ARIA_PLANNER_MODEL" "${PLANNER_MODEL}" ".env"
set_env_value "ARIA_CODER_MODEL" "${CODER_MODEL}" ".env"
set_env_value "ARIA_SQLITE_PATH" "storage/aria.db" ".env"
set_env_value "ARIA_WORKSPACE_DIR" "workspaces/projects" ".env"
set_env_value "ARIA_VOICE_PROFILES_DIR" "storage/voice_profiles" ".env"
set_env_value "ARIA_VOICE_OUTPUTS_DIR" "storage/voice_outputs" ".env"
set_env_value "ARIA_ALLOW_SHELL" "false" ".env"
set_env_value "ARIA_MAX_TOOL_ITERATIONS" "4" ".env"
set_env_value "ARIA_VOICE_BACKEND" "xttsv2" ".env"
set_env_value "ARIA_STT_BACKEND" "faster-whisper" ".env"
set_env_value "ARIA_ENABLE_NATIVE_APPS" "true" ".env"

log "Descargando modelos"
ollama pull "${PLANNER_MODEL}"
ollama pull "${CODER_MODEL}"

log "Instalando servicio systemd"
SERVICE_TMP="$(mktemp)"
sed \
  -e "s|{{ARIA_USER}}|${APP_USER}|g" \
  -e "s|{{ARIA_DIR}}|${APP_DIR}|g" \
  deploy/aria.service > "${SERVICE_TMP}"

sudo cp "${SERVICE_TMP}" "/etc/systemd/system/${SERVICE_NAME}.service"
rm -f "${SERVICE_TMP}"

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

log "Estado final"
sudo systemctl --no-pager --full status "${SERVICE_NAME}" || true
echo
echo "Prueba de salud sugerida:"
echo "curl http://127.0.0.1:8000/health"
echo
echo "Si vas a usar movil por LAN, abre el puerto 8000:"
echo "sudo ufw allow 8000/tcp"
