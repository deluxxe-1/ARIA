# Clonacion de Voz para ARIA

## Lo que necesitas

- Un audio limpio de `30 a 60 segundos`
- Una sola persona hablando
- Sin musica ni ruido de fondo
- Mejor en `wav` o `m4a`
- Voz natural, sin susurros ni gritos

## Recomendacion tecnica

Para este proyecto, el enfoque recomendado es:

- `faster-whisper` para STT local
- `XTTS v2` como motor de clonacion y TTS local

Esto encaja bien con la arquitectura actual:

- `POST /voice/profiles` guarda la muestra de voz
- `POST /voice/transcribe` transcribe audio
- `POST /voice/synthesize` genera audio a partir de texto
- `POST /voice/chat` permite hablar con ARIA y recibir respuesta reutilizando el perfil de voz

## Flujo recomendado

1. Subir una muestra del hablante real.
2. Guardar ese audio como perfil de voz.
3. Si tienes el texto aproximado del audio, guardarlo tambien como `transcript_hint`.
4. Usar ese perfil para sintetizar respuestas de ARIA.

## Consejos para que la clonacion salga bien

- Usa una muestra unica y continua
- Evita reverberacion
- Evita compresion agresiva
- Si puedes, graba con el movil cerca de la boca y en una habitacion silenciosa

## Limitacion actual del MVP

El backend ya deja preparados los perfiles y el flujo de voz.
La sintesis real con clonacion se deja apuntada al backend `XTTS v2`, que hay que instalar y conectar en tu maquina.

## Siguiente integracion recomendada

- Instalar el runtime real de `XTTS v2`
- Añadir generacion real del wav en `app/voice/speech_service.py`
- Exponer descarga o streaming de audio para movil y escritorio
