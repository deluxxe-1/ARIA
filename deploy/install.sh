#!/usr/bin/env bash
# ============================================================
# ARIA — Script de instalación rápida Ubuntu Server 24.04 (RTX 3060)
# Versión: 0.1.0 | Fecha: 2026-10-09
# Uso recomendado: ejecutar PASO A PASO las secciones, NO sh install.sh completo
#    bash deploy/install.sh prereqs   # Solo etapa 1-3
#    bash deploy/install.sh software  # Solo etapa 4-7
#    bash deploy/install.sh deploy    # Solo etapa 8-11
#    bash deploy/install.sh verify    # Solo etapa 12-13
# ============================================================
set -eo pipefail

log()  { printf '\033[0;36m[aria-install]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[aria-install WARN]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[0;31m[aria-install ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Ejecutar como root o sudo $0"
[ -f /etc/os-release ] || die "No se detectó /etc/os-release"
. /etc/os-release
[ "${ID}" = "ubuntu" ] || die "Solo soportado Ubuntu Server (detectado: ${PRETTY_NAME})"
[ "${VERSION_ID}" = "24.04" ] || warn "Ubuntu ${VERSION_ID} detectado. La guía está testeada en 24.04 LTS Noble."

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export TZ=UTC

case "${1:-}" in
# ============================================================
prereqs)
# ============================================================
  log "=== ETAPA 1/4: pre-requisitos OS, drivers NVIDIA 560, CUDA 12.6 ==="
  set -x
  add-apt-repository -y universe restricted multiverse
  apt clean all && apt update -y
  apt -y dist-upgrade
  apt install -y intel-microcode linux-firmware nvidia-firmware-common \
    curl wget ca-certificates gnupg lsb-release apt-transport-https software-properties-common \
    build-essential pkg-config git jq unzip htop tmux rsync ufw fail2ban logrotate systemd-sysv
  swapoff -a && sed -i.bak '/ swap / s/^/#/' /etc/fstab
  printf 'blacklist nouveau\noptions nouveau modeset=0\nalias nouveau off\n' \
    > /etc/modprobe.d/blacklist-nouveau.conf
  update-initramfs -u -k all

  curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/3bf863cc.pub \
    | gpg --dearmor -o /usr/share/keyrings/cuda-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/ /" \
    > /etc/apt/sources.list.d/cuda.list
  apt update -y
  apt install -y --no-install-recommends nvidia-driver-560-server nvidia-utils-560-server nvidia-settings \
    cuda-toolkit-12-6 cuda-libraries-dev-12-6 libcublas-dev-12-6 libcudnn9-cuda-12 nvidia-persistenced
  printf 'export CUDA_HOME=/usr/local/cuda\nexport PATH=$CUDA_HOME/bin:$PATH\nexport LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH\n' \
    > /etc/profile.d/cuda.sh && chmod +x /etc/profile.d/cuda.sh
  . /etc/profile.d/cuda.sh
  systemctl enable --now nvidia-persistenced.service
  warn "REINICIO OBLIGATORIO (shutdown -r now). Después correr: bash $0 software"
  ;;
# ============================================================
software)
# ============================================================
  log "=== ETAPA 2/4: Python 3.12, Ollama binario, usuario aria + dirs ==="
  nvidia-smi || die "nvidia-smi falla. Revisa drivers/reinicio."
  apt install -y --no-install-recommends \
    python3.12 python3.12-venv python3.12-dev python3-pip python3-setuptools \
    libssl-dev libffi-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    liblzma-dev libxml2-dev libxslt1-dev libjpeg-dev libevent-dev
  update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
  curl -fsSL https://ollama.com/install.sh | sh
  systemctl stop ollama.service 2>/dev/null || true; systemctl disable ollama.service 2>/dev/null || true
  /usr/local/bin/ollama --version

  ARIA_DIR="/opt/aria"
  [ -d "$ARIA_DIR/deploy" ] || die "$ARIA_DIR/deploy no existe. Clona el repo antes."
  install -o root -g root -m 644 ${ARIA_DIR}/deploy/aria.sysusers /usr/lib/sysusers.d/aria.conf
  systemd-sysusers aria.conf
  usermod -aG nvidia aria; usermod -aG video aria
  install -o root -g root -m 644 ${ARIA_DIR}/deploy/aria.tmpfiles /usr/lib/tmpfiles.d/aria.conf
  systemd-tmpfiles --create aria.conf
  chown -R aria:aria "${ARIA_DIR}"
  log "=== Correr ahora: bash $0 deploy ==="
  ;;
# ============================================================
deploy)
# ============================================================
  log "=== ETAPA 3/4: venv, modelos Qwen, Alembic, servicios systemd ==="
  ARIA_DIR="/opt/aria"
  sudo -u aria bash -c '
    set -euo pipefail
    cd /opt/aria
    rm -rf .venv
    python3 -m venv --copies --without-pip .venv
    source .venv/bin/activate
    python3 -m ensurepip --upgrade
    pip install --upgrade pip setuptools wheel
    export CUDA_HOME=/usr/local/cuda LD_LIBRARY_PATH=$CUDA_HOME/lib64
    pip install --no-cache-dir -e ".[voice,dev]"
    [ -f .env ] || cp .env.example .env
    echo "== Ahora EDITA /opt/aria/.env: activa enable_api_key, pon clave openssl, host 0.0.0.0 =="
  '
  log "Clave API sugerida (copia al .env): $(openssl rand -hex 32)"

  sudo -u aria bash -c '
    set -euo pipefail
    export OLLAMA_MODELS=/var/lib/ollama CUDA_VISIBLE_DEVICES=0
    mkdir -p /var/lib/ollama && chown aria:aria /var/lib/ollama
  '
  log "Pull de modelos (2-3 min): ejecuta manualmente como aria:"
  log "  sudo -u aria bash -c 'export OLLAMA_MODELS=/var/lib/ollama; ollama serve & sleep 3; ollama pull qwen3:8b-instruct-q4_K_M; ollama pull qwen2.5-coder:7b-instruct-q4_K_M; kill %1'"

  install -o root -g root -m 644 ${ARIA_DIR}/deploy/ollama.service /etc/systemd/system/ollama.service
  install -o root -g root -m 644 ${ARIA_DIR}/deploy/aria.service   /etc/systemd/system/aria.service
  systemctl daemon-reload
  systemctl enable --now ollama.service
  sleep 5 && systemctl is-active ollama.service || die "ollama no arrancó"

  sudo -u aria bash -c '
    set -euo pipefail; source /opt/aria/.venv/bin/activate
    cd /opt/aria && alembic -c alembic.ini upgrade head
    pytest tests/ -x -q --no-header --tb=short
  '
  systemctl enable --now aria.service
  sleep 8 && systemctl is-active aria.service || die "aria no arrancó. journalctl -u aria.service -n 100"
  log "=== Correr ahora: bash $0 verify ==="
  ;;
# ============================================================
verify)
# ============================================================
  log "=== ETAPA 4/4: ufw, smoke tests HTTP, monitoreo ==="
  ufw --force reset
  ufw default deny incoming; ufw default allow outgoing
  ufw allow in from 192.168.1.0/24 to any port 22 proto tcp comment 'SSH LAN'
  ufw allow in from 192.168.1.0/24 to any port 8000 proto tcp comment 'ARIA LAN'
  ufw deny in from any to any port 11434 comment 'Ollama loopback-only'
  ufw --force enable
  systemctl enable --now fail2ban
  ARIA_KEY=$(grep -E '^ARIA_API_KEY=' /opt/aria/.env | cut -d= -f2)
  [ -n "$ARIA_KEY" ] || die "ARIA_API_KEY no encontrado en /opt/aria/.env"
  log "== /health: $(curl -fsS http://127.0.0.1:8000/health)"
  log "== /healthz: $(curl -fsS -H "X-ARIA-Key: ${ARIA_KEY}" http://127.0.0.1:8000/healthz | head -c 180)"
  log "== /chat smoke: $(curl -fsS -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -H "X-ARIA-Key: ${ARIA_KEY}" -d '{"session_id":"installer","user_input":"Di solo OK"}' -m 15 | jq -r .answer)"
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,temperature.gpu,utilization.gpu --format=csv
  log "✅ INSTALACIÓN COMPLETADA. Revisa deploy/UBUNTU_SERVER_GPU_INSTALL.md capítulo 14/15 para monitoreo/logrotate."
  ;;
*)
  cat <<USO
Uso: sudo bash $0 <prereqs|software|deploy|verify>

  prereqs   → Actualiza SO, instala NVIDIA 560+CUDA12.6, desactiva SWAP/nouveau. REQUIERE REINICIO.
  software  → Python3.12, Ollama binario, usuario aria, directorios. (post-reinicio)
  deploy    → venv + [voice,dev], Alembic, pull modelos, systemd services.
  verify    → ufw firewall, smoke tests, nvidia-smi.

Nunca corras todo seguido sin revisar cada etapa. Los modelos tardan minutos en descargarse.
Documentación completa: /opt/aria/deploy/UBUNTU_SERVER_GPU_INSTALL.md
USO
  exit 1
  ;;
esac
