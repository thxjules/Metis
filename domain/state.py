# state.py
from domain.speaker_role import SpeakerRole
import time

calls = {}

# Obtener el estado de la llamada
def get_call(call_id: str):
    if call_id not in calls:
        calls[call_id] = {
            "chunks": [],
            "risk_score": 0,
            "interest_score": 0,
            "risk_emitted": False,
            "strategy": "neutral",
            "previous_strategy": "neutral",
            "closed": False,
            "last_ts": None,
            "events": []
        }
    return calls[call_id]

# Agregar fragmento al estado de la llamada                                                                                                                                                                     
def append_chunk(call_id: str, text: str, ts: int, speaker: SpeakerRole):
    call = get_call(call_id)

    call["chunks"].append({
        "text": text,
        "ts": ts,
        "speaker": speaker
    })

    call["last_ts"] = ts


# Agregar evento al estado de la llamada
def add_event(call_id: str, event: dict):
    call = get_call(call_id)
    call["events"].append(event)
   
