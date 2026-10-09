# Guía de instalación — ARIA en Ubuntu Server 24.04 LTS
**Hardware objetivo**: Intel i7-9700 (8C/8T), 16 GB DDR4, NVIDIA RTX 3060 (12 GB VRAM, Ampere CC 8.6), SSD 256 GB+
**SO**: Ubuntu Server 24.04 LTS (Noble Numbat), mínima, **sin entorno gráfico**.
**Fecha documentación**: 2026-10-09 | ARIA 0.1.0
**Rendimiento objetivo (RTX 3060)**: ~40-55 tok/s Qwen3:8b Q4_K_M, ~50-65 tok/s Qwen2.5-Coder:7b Q4_K_M, memoria ocupada ~10-11 GB VRAM ambos cargados.

---

## 0. Índice
1. [Pre-instalación y actualización del SO](#1-pre-instalación-y-actualización-del-so)
2. [Drivers NVIDIA 560 + CUDA 12.6 (RTX 3060)](#2-drivers-nvidia-560--cuda-126-rtx-3060)
3. [Verificación GPU + persistencia NVIDIA](#3-verificación-gpu--persistencia-nvidia)
4. [Python 3.12 + toolchain de compilación](#4-python-312--toolchain-de-compilación)
5. [Ollama runtime (instalación binaria oficial GPU-aware)](#5-ollama-runtime-instalación-binaria-oficial-gpu-aware)
6. [Usuario `aria` dedicado + directorios de trabajo](#6-usuario-aria-dedicado--directorios-de-trabajo)
7. [Despliegue código + entorno virtual](#7-despliegue-código--entorno-virtual)
8. [Configuración `.env` producción](#8-configuración-env-producción)
9. [Descarga de modelos LLMs (dual-LLM ~11 GB VRAM)](#9-descarga-de-modelos-llms-dual-llm-11-gb-vram)
10. [Migraciones Alembic + smoke tests](#10-migraciones-alembic--smoke-tests)
11. [Servicios systemd `ollama.service` + `aria.service` hardening](#11-servicios-systemd-ollamaservice--ariaservice-hardening)
12. [Cortafuegos ufw (solo puertos estrictamente necesarios)](#12-cortafuegos-ufw-solo-puertos-estrictamente-necesarios)
13. [Pruebas post-instalación (humo, estrés, voz)](#13-pruebas-post-instalación-humo-estrés-voz)
14. [Monitoreo CPU / RAM / GPU (continuo + alertas)](#14-monitoreo-cpu--ram--gpu-continuo--alertas)
15. [Rotación logs systemd-journal + logrotate](#15-rotación-logs-systemd-journal--logrotate)
16. [Procedimiento de actualización (rollback seguro)](#16-procedimiento-de-actualización-rollback-seguro)
17. [Tabla troubleshooting frecuente](#17-tabla-troubleshooting-frecuente)

---

## 1. Pre-instalación y actualización del SO

Ejecutar **como `root` o con `sudo`**. No continuar hasta `apt dist-upgrade` exit 0.

```bash
# Paso 1.1 — Repositorios universe/multiverse habilitados (firmware NVIDIA)
sudo add-apt-repository -y universe
sudo add-apt-repository -y restricted
sudo add-apt-repository -y multiverse

# Paso 1.2 — Limpiar + actualizar paquetes base
sudo apt clean all
sudo apt update -y
sudo NEEDRESTART_MODE=a apt -y dist-upgrade

# Paso 1.3 — Firmware + microcode CPU Intel (i7-9700 Coffee Lake) + herramientas base
sudo NEEDRESTART_MODE=a apt install -y \
  intel-microcode linux-firmware nvidia-firmware-common \
  curl wget ca-certificates gnupg lsb-release apt-transport-https software-properties-common \
  build-essential pkg-config git jq unzip htop tmux rsync ufw fail2ban logrotate \
  systemd-sysv usbguard

# Paso 1.4 — Desactivar SWAP si <32GB RAM (16GB es justo para 2 modelos + STT)
# ⚠️ RTX 3060 12GB: si SWAP se activa, tokens/s caen x10.
sudo swapoff -a
sudo sed -i.bak '/ swap / s/^/#/' /etc/fstab
# Verificar
free -h | awk '/Swap:/ {print "Swap libre: "$4} { if($2=="0B") print "OK: swap desactivado"}'

# Paso 1.5 — Parametros kernel: desactivar nouveau (libre NVIDIA) + IOMMU passthrough GPU
sudo tee /etc/modprobe.d/blacklist-nouveau.conf <<'EOF'
blacklist nouveau
options nouveau modeset=0
alias nouveau off
EOF
sudo update-initramfs -u -k all

# Paso 1.6 — Reinicio para aplicar microcode + initramfs
echo "=== REINICIO OBLIGATORIO en 5 segundos… ==="
sleep 5
sudo reboot
```

✅ **Checkpoint 1**: `cat /proc/cmdline` → **no aparece** `nouveau.modeset=1`. `lsmod | grep nouveau` → sin resultados.

---

## 2. Drivers NVIDIA 560 + CUDA 12.6 (RTX 3060)

> RTX 3060 Ampere sm_86 requiere driver ≥525. **Driver 560.x** recomendado (estable, CUDA 12.6, compatibilidad Ollama 0.6+).

```bash
# Paso 2.1 — Añadir repo NVIDIA CUDA oficial (no ubuntu-drivers autoinstall → suele instalar driver viejo)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/3bf863cc.pub | sudo gpg --dearmor -o /usr/share/keyrings/cuda-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/ /" \
  | sudo tee /etc/apt/sources.list.d/cuda.list > /dev/null
sudo apt update -y

# Paso 2.2 — Instalar driver metapaquete NVIDIA 560 + CUDA Toolkit mínimo
sudo NEEDRESTART_MODE=a apt install -y --no-install-recommends \
  nvidia-driver-560-server nvidia-utils-560-server nvidia-settings \
  cuda-toolkit-12-6 cuda-libraries-dev-12-6 libcublas-dev-12-6 libcudnn9-cuda-12 \
  nvidia-persistenced

# Paso 2.3 — PATH permanente CUDA (/usr/local/cuda/bin)
sudo tee /etc/profile.d/cuda.sh <<'EOF'
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
EOF
sudo chmod +x /etc/profile.d/cuda.sh
source /etc/profile.d/cuda.sh

# Paso 2.4 — Reinicio para cargar driver NVIDIA kernel module
sudo reboot
```

✅ **Checkpoint 2**: Tras reinicio → continuar al capítulo 3.

---

## 3. Verificación GPU + persistencia NVIDIA

```bash
# Paso 3.1 — nvidia-smi debe mostrar RTX 3060, Driver 560, CUDA 12.6
nvidia-smi
# Salida esperada:
#   NVIDIA-SMI 560.xx.xx   Driver Version: 560.xx   CUDA Version: 12.6
#   GPU  Name        Persistence-M  Bus-Id        Disp.A  Volatile Uncorr. ECC
#   0    NVIDIA GeForce RTX 3060  On    …              Off  0

# Paso 3.2 — Activar nvidia-persistenced para no cold-start GPU cada request
sudo systemctl enable --now nvidia-persistenced.service
sudo systemctl is-active nvidia-persistenced  # → active

# Paso 3.3 — NVML bindings Python + bandwidth test
/usr/local/cuda/extras/demo_suite/bandwidthTest --device=0 --memory
# PASS en Result = 200+ GB/s típico PCIe 3.0 x16

# Paso 3.4 — Cuántica VRAM RTX 3060 debe ser 12288 MiB ≈ 12 GB
nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits
# → 12288
```

⚠️ **Blocker**: si `nvidia-smi` devuelve `NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver` → ir al capítulo 17, punto 1.

---

## 4. Python 3.12 + toolchain de compilación

ARIA `requires-python=">=3.12"` (en `pyproject.toml`). Ubuntu 24.04 trae 3.12 por defecto.

```bash
# Paso 4.1 — Python 3.12 + venv + dev headers + uvloop/httptools libs
sudo apt install -y --no-install-recommends \
  python3.12 python3.12-venv python3.12-dev python3-pip python3-setuptools \
  libssl-dev libffi-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  liblzma-dev libxml2-dev libxslt1-dev libjpeg-dev libevent-dev

# Paso 4.2 — Pin del sistema para `/usr/bin/python3 = 3.12` (por si lo toco upgrade)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Paso 4.3 — Verificar versiones exactas
python3 --version    # Python 3.12.x
python3 -m venv --help >/dev/null && echo "venv: OK"
```

✅ **Checkpoint 3**: `python3 --version` → `3.12.3`+. `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` ≥ 3.40.

---

## 5. Ollama runtime (instalación binaria oficial GPU-aware)

> **NO usar `apt install ollama`** (repo Ubuntu suele estar desactualizado 2-3 versiones). Usar script oficial.

```bash
# Paso 5.1 — Instalar binario oficial (detecta GPU RTX 3060 automáticamente via NVML)
curl -fsSL https://ollama.com/install.sh | sh

# Paso 5.2 — Desactivar el servicio por defecto (usaremos el nuestro en /etc/systemd/system user=aria)
sudo systemctl stop ollama.service 2>/dev/null || true
sudo systemctl disable ollama.service 2>/dev/null || true

# Paso 5.3 — Verificar binario
/usr/local/bin/ollama --version   # ≥ 0.6.0
```

---

## 6. Usuario `aria` dedicado + directorios de trabajo

> Siguridad: ARIA NUNCA corre como `root`. Usuario sin shell login.

```bash
# Paso 6.1 — Usar sysusers.d (distro-agnostic, no useradd hardcodeado)
sudo install -o root -g root -m 644 /opt/aria/deploy/aria.sysusers /usr/lib/sysusers.d/aria.conf
sudo systemd-sysusers aria.conf
id aria  # → uid=xxx(aria) gid=xxx(aria) groups=xxx(aria), shell=/usr/sbin/nologin

# Paso 6.2 — Añadir usuario aria al grupo 'nvidia' (para /dev/nvidia*)
sudo usermod -aG nvidia aria
sudo usermod -aG video aria
groups aria  # → nvidia, video, aria

# Paso 6.3 — Directorios con tmpfiles.d
sudo install -o root -g root -m 644 /opt/aria/deploy/aria.tmpfiles /usr/lib/tmpfiles.d/aria.conf
sudo systemd-tmpfiles --create aria.conf
# Verificar permisos:
stat -c '%a %U:%G %n' /opt/aria /opt/aria/storage /var/lib/ollama
# Todos deben ser 750 aria aria.
```

---

## 7. Despliegue código + entorno virtual

```bash
# Paso 7.1 — Copiar código (desde git o rsync local) al deploy dir /opt/aria
# Si usas git (recomendado):
cd /opt
sudo git clone <URL_DE_TU_REPO_ARIA> aria
sudo chown -R aria:aria /opt/aria
# O rsync desde máquina dev (ejemplo):
# sudo rsync -az --delete --exclude='.venv' --exclude='.git' --exclude='__pycache__' usuario@DEV-MACHINE:/ruta/aria/ /opt/aria/ && sudo chown -R aria:aria /opt/aria

# Paso 7.2 — Crear venv dentro /opt/aria/.venv (como usuario aria)
sudo -u aria bash -c '
  set -euo pipefail
  cd /opt/aria
  rm -rf .venv
  python3 -m venv --copies --without-pip .venv
  source .venv/bin/activate
  # pip bootstrap desde venv
  python3 -m ensurepip --upgrade
  pip install --upgrade pip setuptools wheel
'

# Paso 7.3 — Instalar paquete ARIA modo editable con extras voice (faster-whisper GPU)
sudo -u aria bash -c '
  set -euo pipefail
  cd /opt/aria
  source .venv/bin/activate
  export CUDA_HOME=/usr/local/cuda
  export LD_LIBRARY_PATH=$CUDA_HOME/lib64
  pip install --no-cache-dir -e ".[voice,dev]"
'

# Paso 7.4 — Sancheck de imports
sudo -u aria bash -c '
  source /opt/aria/.venv/bin/activate && python3 -c "
import fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, httpx, structlog, pydantic_settings
try:
    from faster_whisper import WhisperModel
    print(\"faster-whisper: OK (GPU detectado? WhisperModel CUDA)\")
except Exception as e:
    print(f\"faster-whisper WARNING: {e}\")
print(\"Imports backend OK\")
"
'
```

✅ **Checkpoint 4**: `pip list | grep -E "aria|faster-whisper|uvicorn|sqlalchemy|alembic"` todos presentes con versiones lockeadas.

---

## 8. Configuración `.env` producción

```bash
cd /opt/aria
sudo -u aria cp -n deploy/.env.example .env  # -n no sobrescribir si existe

# PASO OBLIGATORIO: editar .env con clave API segura, paths absolutos, production
sudo -u aria editor /opt/aria/.env

# === VALORES OBLIGATORIOS A CAMBIAR ===
# 1. ARIA_ENV=production
# 2. ARIA_HOST=0.0.0.0   (escuchar LAN, NO 127.0.0.1)
# 3. ARIA_ENABLE_API_KEY=true
# 4. ARIA_API_KEY → generar con:
sudo openssl rand -hex 32   # Copiar resultado al .env

# (Opcional pero recomendado) CORS restrictivo:
#   ARIA_CORS_ORIGINS='["http://192.168.1.100:8080","http://aria.local"]'
sudo chown aria:aria /opt/aria/.env
sudo chmod 640 /opt/aria/.env
ls -la /opt/aria/.env   # → -rw-r----- 1 aria aria
```

---

## 9. Descarga de modelos LLMs (dual-LLM ~11 GB VRAM)

> RTX 3060 12 GB: usar **Q4_K_M** (sweet spot calidad/velocidad). Q5_K_M excede VRAM si cargas ambos a la vez.

```bash
# Levantar Ollama TEMPORALMENTE usuario aria para poder hacer pull y guardar en /var/lib/ollama
sudo systemd-run --user --user=aria --collect --setenv=HOME=/opt/aria --setenv=OLLAMA_MODELS=/var/lib/ollama /usr/local/bin/ollama serve
# Esperar 3s, o correr en otro tmux window en su defecto:
sudo -u aria bash -c '
export OLLAMA_MODELS=/var/lib/ollama
export CUDA_VISIBLE_DEVICES=0
mkdir -p /var/lib/ollama && chown aria:aria /var/lib/ollama
/usr/local/bin/ollama pull qwen3:8b-instruct-q4_K_M      # ≈ 6.1 GB, ~3 min en 100 Mbps
/usr/local/bin/ollama pull qwen2.5-coder:7b-instruct-q4_K_M  # ≈ 5.1 GB
# Optional Whisper GPU STT (faster-whisper descarga solo, no Ollama)
'

# Verificar que el modelo se guardó en /var/lib/ollama (no root)
sudo du -sh /var/lib/ollama/*  # → ~11.2 GB

# Actualizar .env para apuntar a modelos quantizados (si usaste q4_K_M)
sudo -u aria sed -i.bak \
  -e 's|^ARIA_PLANNER_MODEL=.*|ARIA_PLANNER_MODEL=qwen3:8b-instruct-q4_K_M|' \
  -e 's|^ARIA_CODER_MODEL=.*|ARIA_CODER_MODEL=qwen2.5-coder:7b-instruct-q4_K_M|' \
  /opt/aria/.env
```

---

## 10. Migraciones Alembic + smoke tests

```bash
sudo -u aria bash -c '
  set -euo pipefail
  cd /opt/aria
  source .venv/bin/activate

  # Paso 10.1 — Alembic stamp head (si DB vacía) o upgrade head a última revisión
  export ARIA_SQLITE_PATH=/opt/aria/storage/aria.db
  export ARIA_ENV=production
  python3 -m alembic -c alembic.ini upgrade head

  # Paso 10.2 — Verificar que la tabla messages + índice existen
  python3 -c "
import aiosqlite, asyncio
async def main():
    async with aiosqlite.connect('/opt/aria/storage/aria.db') as c:
        cur = await c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='messages'\")
        r = await cur.fetchone()
        assert r and r[0] == 'messages', 'Tabla messages no creada'
        cur2 = await c.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND name='idx_messages_session_id_desc'\")
        r2 = await cur2.fetchone()
        assert r2, 'Índice idx_messages_session_id_desc no creado'
        print('SQLite schema OK')
asyncio.run(main())
  "

  # Paso 10.3 — Smoke pytest (50 tests, ~10s) — SALIR si hay FAILED
  python3 -m pytest tests/ -x -q --no-header --tb=short
'
```

✅ **Checkpoint 5**: pytest exit 0 → 50 PASSED, 2 warnings deprecación normales. Alembic revision → `alembic current` → `0001_init_messages_index (head)`.

---

## 11. Servicios systemd `ollama.service` + `aria.service` hardening

```bash
# Paso 11.1 — Instalar unidades systemd
sudo install -o root -g root -m 644 /opt/aria/deploy/ollama.service /etc/systemd/system/ollama.service
sudo install -o root -g root -m 644 /opt/aria/deploy/aria.service   /etc/systemd/system/aria.service
sudo systemctl daemon-reload

# Paso 11.2 — Levantar Ollama primero (es dependencia de aria.service Wants=)
sudo systemctl enable --now ollama.service
sleep 4
sudo systemctl status ollama.service --no-pager
# → State=active (running), SyslogIdentifier=ollama, GPU detectado

# Paso 11.3 — Probar /api/tags de Ollama antes de arrancar ARIA
curl -fsS http://127.0.0.1:11434/api/tags | jq '.models[].name'
# → "qwen3:8b-instruct-q4_K_M", "qwen2.5-coder:7b-instruct-q4_K_M"

# Paso 11.4 — Levantar ARIA
sudo systemctl enable --now aria.service
sleep 8
sudo systemctl status aria.service --no-pager
# → active (running). CPUQuota=700%, MemoryMax=10G (ver en systemctl show aria | grep -E 'CPU|MemoryMax|ReadWrite')
```

---

## 12. Cortafuegos ufw (solo puertos estrictamente necesarios)

```bash
# Paso 12.1 — Politicas por defecto DROP (denegar todo, permitir solo explícitamente)
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Paso 12.2 — Puertos mínimos: SSH (admin) + ARIA API (8000/tcp LAN)
# SSH solo desde LAN 192.168.1.0/24 (ajusta a tu subred!)
sudo ufw allow in from 192.168.1.0/24 to any port 22 proto tcp comment 'SSH admin LAN'
# ARIA 8000/tcp LAN
sudo ufw allow in from 192.168.1.0/24 to any port 8000 proto tcp comment 'ARIA FastAPI LAN'
# IMPORTANTE: NUNCA abrir 11434 (Ollama) a LAN! Solo loopback. Confirmar:
sudo ufw deny in from any to any port 11434 comment 'Ollama NUNCA LAN — solo loopback'

# Paso 12.3 — Activar ufw + fail2ban SSH
sudo ufw --force enable
sudo ufw status numbered
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

✅ **Checkpoint 6**: Desde otra máquina LAN `nmap -p 22,8000,11434 <IP_SERVIDOR>` → 22 open, 8000 open, 11434 filtered.

---

## 13. Pruebas post-instalación (humo, estrés, voz)

```bash
# En servidor (localhost) o cliente LAN ajustando http://IP:8000
export ARIA_IP=127.0.0.1
export ARIA_KEY=$(sudo grep -E '^ARIA_API_KEY=' /opt/aria/.env | cut -d= -f2)

# Test 13.1 — Health simple
curl -fsS -X GET "http://${ARIA_IP}:8000/health" | jq .
# → {"status":"ok"}

# Test 13.2 — Health detallado (CPU, GPU, disco)
curl -fsS -X GET "http://${ARIA_IP}:8000/healthz" -H "X-ARIA-Key: ${ARIA_KEY}" | jq .
# → {status: healthy, components: {db: ok, ollama: ok, disk: ok}}

# Test 13.3 — Chat sincrono single prompt + respuesta corta (<50 tokens)
time curl -fsS -X POST "http://${ARIA_IP}:8000/chat" \
  -H 'Content-Type: application/json' -H "X-ARIA-Key: ${ARIA_KEY}" \
  -d '{"session_id":"smoke-test-001","user_input":"Escribe el nombre del planeta rojo en una sola palabra."}' | jq .answer
# Esperado: "Marte" (<1 s primero token, total < 3 s)

# Test 13.4 — Chat stream SSE (valida evento tool_call/token/done)
curl -sS -N -X POST "http://${ARIA_IP}:8000/chat/stream" \
  -H 'Accept: text/event-stream' -H "X-ARIA-Key: ${ARIA_KEY}" \
  -d '{"session_id":"smoke-stream-002","user_input":"Cuenta 1 2 3 una palabra por línea"}' \
  | tee /tmp/sse.log
# → ver lineas `event:token`, final `event:done`

# Test 13.5 — Stress paralelo 5 sesiones concurrentes (RTX 3060 debe aguantar ~4 sin queue)
for i in 1 2 3 4 5; do
  ( time curl -sS -X POST "http://${ARIA_IP}:8000/chat" \
    -H 'Content-Type: application/json' -H "X-ARIA-Key: ${ARIA_KEY}" \
    -d "{\"session_id\":\"stress-${i}\",\"user_input\":\"Dime 5 frutas\"}" \
    -o /tmp/stress${i}.json ) &
done
wait
echo "=== Stress test done. Revisa nvidia-smi concurrente en otra terminal: ==="
echo "watch -n 1 nvidia-smi"

# Test 13.6 — STT faster-whisper 1 MB WAV (reemplazar por archivo real)
# curl -fsS -X POST "http://${ARIA_IP}:8000/voice/stt" -F "file=@sample.wav" -H "X-ARIA-Key: ${ARIA_KEY}" | jq
```

✅ **Checkpoint 7**: Todos los tests HTTP devuelven 200. nvidia-smi muestra `Volatile GPU-Util 30-80%`. VRAM usada 8-11 GB.

---

## 14. Monitoreo CPU / RAM / GPU (continuo + alertas)

### 14.1 Monitoreo interactivo
```bash
# Glances (CPU, RAM, Disco, RED, GPU via nvidia plugin)
sudo apt install -y glances python3-nvml
sudo -u aria glances --enable-plugin nvidia -t 1  # http://<IP>:61208 (opcional)

# nvidia-smi en bucle 1s con colores
watch -n 1 -d nvidia-smi
# nvtop (TUI GPU, mejor que nvidia-smi)
sudo apt install -y nvtop
nvtop
```

### 14.2 Alerta Umbral GPU VRAM > 92% / Temp > 82°C por correo (Postfix mínimo)
```bash
# Instalar ssmtp o postfix-satellite (fuera scope, solo plantilla cron script)
sudo install -m 0750 -o aria -g aria /dev/stdin /opt/aria/scripts/monitor_gpu.sh <<'SCRIPT'
#!/usr/bin/env bash
# GPU check RTX 3060: VRAM%, Temp, Fallo driver
set -u
LOG=/opt/aria/logs/gpu.log
N=$(nvidia-smi --query-gpu=index,memory.used,memory.total,temperature.gpu,utilization.gpu --format=csv,noheader,nounits)
TS=$(date +%F_%T)
VRAM_USED=$(echo "$N"  | awk '{print $2}')
VRAM_TOT=$(echo "$N"   | awk '{print $3}')
TEMP=$(echo "$N"      | awk '{print $4}')
UTIL=$(echo "$N"      | awk '{print $5}' | tr -d '%')
VRAM_PCT=$(( VRAM_USED * 100 / VRAM_TOT ))
echo "[$TS] GPU0 VRAM=${VRAM_USED}/${VRAM_TOT}MiB (${VRAM_PCT}%)  TEMP=${TEMP}°C  UTIL=${UTIL}%" >> "$LOG"
# Alertas
if [ "$VRAM_PCT" -gt 92 ]; then
  echo "[$TS] ALERTA VRAM ${VRAM_PCT}% > 92%. Reiniciando aria.service en 60s." >> "$LOG"
  sleep 60 && systemctl restart aria.service
fi
if [ "$TEMP" -gt 82 ]; then
  echo "[$TS] ALERTA TEMP GPU ${TEMP}°C > 82°C. Throttling posible." >> "$LOG"
fi
SCRIPT
sudo -u aria mkdir -p /opt/aria/logs
sudo -u aria chmod +x /opt/aria/scripts/monitor_gpu.sh

# Paso 14.3 — Cron cada 2 min
(crontab -l 2>/dev/null; echo "*/2 * * * * sudo -n /opt/aria/scripts/monitor_gpu.sh 2>/dev/null") | sudo crontab -
# Añadir sudoers NOPASSWD script solo para aria monitor
sudo tee /etc/sudoers.d/aria-monitor <<'EOF'
aria ALL=(root) NOPASSWD: /opt/aria/scripts/monitor_gpu.sh
EOF
sudo chmod 0440 /etc/sudoers.d/aria-monitor
```

### 14.3 Prometheus + Grafana (opcional, fuera scope básico)
Instalar `nvidia-dcgm-exporter` (DCGM) + `node_exporter` + Grafana dashboard 12500. No documentado por ser high-scope.

---

## 15. Rotación logs systemd-journal + logrotate

```bash
# Paso 15.1 — Journald size bound (max 1GB, 7 días)
sudo tee -a /etc/systemd/journald.conf.d/99-aria.conf <<'EOF'
[Journal]
SystemMaxUse=1G
SystemMaxFileSize=50M
MaxRetentionSec=7day
ForwardToSyslog=no
EOF
sudo systemctl restart systemd-journald.service

# Paso 15.2 — Logrotate fichero /opt/aria/logs/*.log
sudo install -o root -g root -m 644 /dev/stdin /etc/logrotate.d/aria <<'EOF'
/opt/aria/logs/*.log {
  daily
  rotate 7
  compress
  delaycompress
  missingok
  notifempty
  create 0640 aria aria
  su aria aria
  copytruncate
}
EOF
sudo logrotate -f /etc/logrotate.d/aria 2>&1 | tail -n 5

# Ver logs ARIA en vivo
sudo journalctl -u aria.service -f --output=short-iso
```

---

## 16. Procedimiento de actualización (rollback seguro)

```bash
# 16.1 — Backup DB SQLite + modelo symlinks (0 downtime copy-on-write)
sudo -u aria bash -c '
  cd /opt/aria
  TS=$(date +%F_%H%M)
  mkdir -p backups/$TS
  cp -a storage/aria.db              backups/$TS/aria.db
  cp -a .env                         backups/$TS/.env
  alembic current > backups/$TS/alembic_current.txt
  tar czf backups/${TS}.tar.gz backups/$TS/
  echo "Backup $TS OK: $(du -sh backups/${TS}.tar.gz)"
'

# 16.2 — Pull código nuevo
cd /opt/aria && sudo -u aria git pull --ff-only

# 16.3 — Actualizar venv + migraciones
sudo -u aria bash -c '
  source /opt/aria/.venv/bin/activate
  pip install --no-cache-dir -e ".[voice,dev]"
  alembic upgrade head
  pytest tests/ -x -q
'

# 16.4 — Rolling restart
sudo systemctl restart aria.service
sleep 5 && sudo systemctl is-active aria.service  # → active
curl -fsS http://127.0.0.1:8000/health | jq

# 16.5 — Rollback si falla (30 min window)
# sudo -u aria bash -c 'cd /opt/aria && tar xzf backups/<TS>.tar.gz && cp -a backups/<TS>/.env . && cp -a backups/<TS>/aria.db storage/ && alembic stamp $(cat backups/<TS>/alembic_current.txt)'
# sudo systemctl restart aria.service
```

---

## 17. Tabla troubleshooting frecuente

| #  | Síntoma                                                                 | Causa más probable                         | Acción inmediata                                                                                                        |
|----|-------------------------------------------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| 1  | `nvidia-smi` error `couldn't communicate with the NVIDIA driver`       | Secure Boot activado, o módulo no cargado  | Revisar `mokutil --sb-state` → si enabled, firmar módulo NV o desactivar Secure Boot en BIOS. `modprobe nvidia`        |
| 2  | `nvidia-smi` muestra `ERR!` en Utilización + tokens/s <5               | Temperatura >86°C throttling               | Limpiar disipador polvo; `nvidia-smi -q | grep -A2 Temperature`; ver ventiladores BIOS                                   |
| 3  | CURL POST `/chat` → 401 `Unauthorized`                                 | Falta header X-ARIA-Key o .env sin clave   | Asegurar `enable_api_key=true` y enviar header exacto `X-ARIA-Key: <valor>`                                              |
| 4  | Ollama `503 Service Unavailable` → ARIA `/chat` 503 VoiceBackendError  | Ollama no arrancó o GPU OOM                | `journalctl -u ollama.service -n 100`; si `CUDA out of memory` → bajar a Q4_K_M o desactivar flash_attn                   |
| 5  | Apertura VRAM < 11000 MiB (solo carga 1 modelo)                        | Xorg / display manager ocupando VRAM       | Ubuntu Server sin GUI: no debería pasar. Si ocurre → `systemctl disable gdm3 lightdm`                                  |
| 6  | `systemctl status aria.service` → exited code 203 (Exec format)         | .venv/bin/uvicorn no con shebang correcto  | `file /opt/aria/.venv/bin/uvicorn`; recrear venv como usuario aria                                                       |
| 7  | SQLite `database is locked` en multi-worker                            | 2 workers + SQLite WAL no activo           | Añadir PRAGMA journal_mode=WAL en session.py o bajar a --workers 1. Mejor: migrar a PostgreSQL en caso mucho tráfico       |
| 8  | STT faster-whisper devuelve `VoiceBackendError: CUDA not available`    | Usuario aria no en grupo nvidia/video      | `groups aria`; añadir con `usermod -aG nvidia aria`; logout/login (reboot)                                             |
| 9  | STT Latencia > 10 s (30s audio)                                        | faster-whisper en CPU, no GPU              | Ver variables en ollama.service: `OLLAMA_GPU_LAYERS=99`; `python -c "import faster_whisper; print(faster_whisper.device)"` |
| 10 | `/healthz` degraded component disk                                     | Storage < 1GB libre                         | `du -sh /opt/aria/storage/voice_outputs/*`; POST /admin/cleanup purgar TTL > 24h                                        |
| 11 | Tokens/s muy bajos (< 10/s) en GPU                                     | CUDA_MODULE_LOADING=LAZY primera carga, o 4 workers vs 2   | Esperar 2s en el 1er prompt; bajar uvicorn --workers a 2                                    |

---

## 📚 Referencias archivos deploy

| Archivo (ruta absoluta)                                                                                                 | Propósito                                    |
|-------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| [aria.service](file:///c:/Users/deluxXe/Documents/ARIA/deploy/aria.service)                                           | Unidad systemd ARIA FastAPI hardening       |
| [ollama.service](file:///c:/Users/deluxXe/Documents/ARIA/deploy/ollama.service)                                       | Unidad systemd Ollama GPU dedicado          |
| [aria.sysusers](file:///c:/Users/deluxXe/Documents/ARIA/deploy/aria.sysusers)                                         | sysusers.d: usuario/grupo aria sin shell    |
| [aria.tmpfiles](file:///c:/Users/deluxXe/Documents/ARIA/deploy/aria.tmpfiles)                                         | tmpfiles.d: permisos dirs /opt/aria + ollama |
| [.env.example](file:///c:/Users/deluxXe/Documents/ARIA/.env.example)                                                  | Plantilla producción variables entorno      |
| [pyproject.toml](file:///c:/Users/deluxXe/Documents/ARIA/pyproject.toml)                                              | PEP 621 origen único dependencias           |

**Fin de la guía**. Tiempo estimado de instalación manual: ~45-60 min (incluyendo descarga de modelos ~11 GB). Alternativa rápida: usar `deploy/install.sh` (modo asistido).
