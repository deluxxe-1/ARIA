# Pasar ARIA al Servidor e Instalarlo

## Opcion recomendada

Usa `git` para pasar el proyecto al servidor.

## Paso 1. Sube el proyecto a un repositorio

Desde tu ordenador actual:

```bash
git init
git add .
git commit -m "ARIA base server + native apps"
git branch -M main
git remote add origin TU_URL_DEL_REPO
git push -u origin main
```

Si ya tienes repo, solo haz:

```bash
git add .
git commit -m "Update ARIA deployment and native phase"
git push
```

## Paso 2. Entra en el servidor Ubuntu

Desde tu ordenador:

```bash
ssh tu_usuario@IP_DEL_SERVIDOR
```

## Paso 3. Prepara la carpeta del proyecto

En el servidor:

```bash
sudo mkdir -p /opt/aria
sudo chown -R $USER:$USER /opt/aria
cd /opt/aria
```

## Paso 4. Descarga el proyecto en Ubuntu

```bash
git clone TU_URL_DEL_REPO /opt/aria
cd /opt/aria
```

Si ya existe y quieres actualizar:

```bash
cd /opt/aria
git pull
```

## Paso 5. Instala drivers NVIDIA

```bash
chmod +x scripts/install_nvidia_ubuntu.sh
./scripts/install_nvidia_ubuntu.sh
```

Despues reinicia:

```bash
sudo reboot
```

Vuelve a entrar por SSH y comprueba:

```bash
nvidia-smi
```

## Paso 6. Instala ARIA

```bash
cd /opt/aria
chmod +x scripts/install_aria_ubuntu.sh
APP_DIR=/opt/aria APP_USER=$USER ./scripts/install_aria_ubuntu.sh
```

## Paso 7. Verifica que todo funciona

```bash
sudo systemctl status aria
ollama list
curl http://127.0.0.1:8000/health
```

## Paso 8. Abre acceso desde móvil o PC

```bash
sudo ufw allow 8000/tcp
```

## Si no quieres usar git

Puedes copiar los archivos por `scp`.

Desde tu ordenador:

```bash
scp -r "C:/ruta/local/del/proyecto" tu_usuario@IP_DEL_SERVIDOR:/opt/aria
```

Luego en el servidor:

```bash
cd /opt/aria
chmod +x scripts/install_nvidia_ubuntu.sh
chmod +x scripts/install_aria_ubuntu.sh
```

## Orden exacto recomendado

1. Subir el proyecto al repo o copiarlo por `scp`.
2. Entrar por `ssh` al servidor.
3. Colocar el proyecto en `/opt/aria`.
4. Ejecutar `install_nvidia_ubuntu.sh`.
5. Reiniciar el servidor.
6. Confirmar `nvidia-smi`.
7. Ejecutar `install_aria_ubuntu.sh`.
8. Comprobar `systemctl status aria`.
9. Probar `curl /health`.
10. Abrir el puerto `8000` si vas a conectar móvil o app de escritorio.
