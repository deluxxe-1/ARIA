#!/usr/bin/env bash

set -euo pipefail

log() {
  echo
  echo "==> $1"
}

require_ubuntu() {
  if [[ ! -f /etc/os-release ]]; then
    echo "No se puede detectar el sistema operativo." >&2
    exit 1
  fi

  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "Este script esta pensado para Ubuntu." >&2
    exit 1
  fi
}

log "Comprobando Ubuntu"
require_ubuntu

log "Actualizando repositorios"
sudo apt update
sudo apt upgrade -y

log "Instalando utilidades base"
sudo apt install -y ubuntu-drivers-common pciutils

log "Detectando GPU NVIDIA"
lspci | grep -i nvidia || {
  echo "No se ha detectado una GPU NVIDIA en este servidor." >&2
  exit 1
}

log "Instalando driver recomendado"
sudo ubuntu-drivers autoinstall

echo
echo "Instalacion del driver completada."
echo "Reinicia el servidor antes de continuar:"
echo "sudo reboot"
echo
echo "Despues del reinicio, ejecuta:"
echo "nvidia-smi"
echo
echo "Si quieres ver informacion extra de la GPU:"
echo "lspci | grep -i nvidia"
