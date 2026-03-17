import uuid
from datetime import datetime, timezone

# Construir evento
def build_event(
    *,
    event_type: str,
    call_id: str,
    payload: dict,
    risk_score: int | None = None,
    call_status: str = "open",
):
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "call": {
            "id": call_id,
            "risk_score": risk_score,
            "status": call_status
        },
        "payload": payload
    }

