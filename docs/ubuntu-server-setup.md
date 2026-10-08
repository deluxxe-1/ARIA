# Instalación de ARIA en Ubuntu Server

## Requisitos previos

- Ubuntu Server actualizado
- Driver de NVIDIA instalado y funcionando
- `nvidia-smi` debe responder correctamente
- El código de `ARIA` debe estar ya clonado en el servidor
- Script NVIDIA disponible en `scripts/install_nvidia_ubuntu.sh`

## Ruta recomendada

```bash
/opt/aria
```

## Instalación rápida

Desde la carpeta del proyecto:

```bash
chmod +x scripts/install_nvidia_ubuntu.sh
./scripts/install_nvidia_ubuntu.sh
sudo reboot
```

Despues del reinicio:

```bash
nvidia-smi
chmod +x scripts/install_aria_ubuntu.sh
APP_DIR=/opt/aria APP_USER=tu_usuario ./scripts/install_aria_ubuntu.sh
```

## Qué hace el script

- actualiza paquetes
- instala dependencias del sistema
- instala `Ollama` si no existe
- crea `.venv`
- instala `requirements.txt`
- instala `requirements-voice.txt` si está presente
- prepara `.env`
- descarga `qwen3:8b`
- descarga `qwen2.5-coder:7b`
- instala `aria.service`

## Servicio systemd

Archivo base:

```text
deploy/aria.service
```

El script reemplaza:

- `{{ARIA_USER}}`
- `{{ARIA_DIR}}`

Y lo copia a:

```bash
/etc/systemd/system/aria.service
```

## Comandos útiles

Ver estado:

```bash
sudo systemctl status aria
```

Reiniciar:

```bash
sudo systemctl restart aria
```

Ver logs:

```bash
journalctl -u aria -f
```

Probar API:

```bash
curl http://127.0.0.1:8000/health
```

## Firewall

Si vas a conectarte desde móvil o desde otro ordenador:

```bash
sudo ufw allow 8000/tcp
```

## Transferencia de archivos

La guía completa para pasar el proyecto desde tu ordenador al servidor está en:

```text
docs/transfer-and-install.md
```

## Voz

La transcripción local queda lista con:

```bash
pip install -r requirements-voice.txt
```

La clonación real con `XTTS v2` sigue pendiente de integrarse del todo en `app/voice/speech_service.py`.
