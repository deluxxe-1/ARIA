# ARIA Native

Aplicacion nativa compartida para escritorio y movil basada en `Flutter`.

## Objetivo

- Escritorio: Windows como companion de ARIA en el PC principal.
- Movil: Android/iPhone para hablar con ARIA por texto y audio.
- Sin panel web.

## Estado

- Chat por texto contra `POST /chat` con historial persistido (`session_id` guardado en `SharedPreferences`).
- Accion "Nueva conversacion" para regenerar el `session_id`.
- Gestion basica de perfiles de voz.
- Envio de audio a `POST /voice/chat` reutilizando el mismo `session_id` del chat.
- Base lista para crecer con microfono en vivo y reproduccion TTS.

## Configuracion

La URL del backend se configura en tiempo de compilacion usando `--dart-define`:

```bash
# Escritorio (backend en la misma maquina, valor por defecto)
flutter run -d windows

# Android Emulator: 10.0.2.2 es el alias del host del emulator
flutter run -d android --dart-define=ARIA_API_URL=http://10.0.2.2:8000

# Dispositivo movil real por red local (IP del PC donde corre ARIA backend)
flutter run -d android --dart-define=ARIA_API_URL=http://192.168.1.20:8000

# iOS Simulator y macOS usan 127.0.0.1 por defecto; para dispositivo real usa la IP LAN.
flutter run -d ios --dart-define=ARIA_API_URL=http://192.168.1.20:8000
```

## Arranque

```bash
flutter pub get
flutter run -d windows --dart-define=ARIA_API_URL=http://127.0.0.1:8000
```

## Nota

- El `session_id` se genera la primera vez y se guarda en `SharedPreferences` con la clave `aria_session_id`.
- El boton "Nueva conversacion" regenera el `session_id` y vacia el historial visible.
- Para dispositivos Android reales, recuerda abrir el puerto `8000` del firewall del PC servidor y que el host/IP del backend sea alcanzable desde el movil.
