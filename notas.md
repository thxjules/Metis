# Nota técnica — Identificación de agente y campaña en Metis

## Estado actual
El agente ingresa su ID y campaña manualmente al iniciar `mic_client.py`.
Es la solución más simple y funciona sin dependencias externas.

## Alternativa 1 — API de la plataforma del agente
Cuando tengas acceso a la plataforma que usan los agentes:
- Consultar el ID del agente autenticado via API al iniciar la sesión
- La plataforma ya asigna un ID único por agente
- `mic_client.py` haría un GET al endpoint de sesión y obtendría `agent_id` y `campaign` automáticamente
- El agente no tendría que ingresar nada manualmente

## Alternativa 2 — Diarización + separación de canales
Cuando tengas acceso a los canales de audio separados (agente izquierdo, cliente derecho):
- Canal izquierdo = agente → `SpeakerRole.AGENT`
- Canal derecho = cliente → `SpeakerRole.CLIENT`
- `mic_client.py` captura stereo y separa los dos streams
- El `agent_id` llega desde la plataforma (ver Alternativa 1)
- Elimina completamente los falsos positivos del engine porque ya se sabe quién habla

## Pendiente
- Confirmar qué plataforma usan los agentes en Convertia
- Verificar si la plataforma expone API de sesión
- Solicitar acceso al audio por canales separados