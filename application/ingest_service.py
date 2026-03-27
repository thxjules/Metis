from infra.redis_repository import RedisRepository
from domain.engine import calculate_risk_delta, is_call_closing, RISK_THRESHOLD, INTEREST_THRESHOLD, detect_extreme_hostility
from domain.event import build_event


class IngestService:
    def __init__(self, repo: RedisRepository):
        self.repo = repo

    def ingest(self, payload: dict):
        call_id = payload["call_id"]
        chunk_id = payload.get("chunk_id", str(call_id))  
        agent_id = payload.get("agent_id", "unknown_agent")
        campaign = payload.get("campaign", "unknown_campaign")
        text = payload["text"]
        ts = payload.get("ts", 0)
        is_final = payload.get("is_final", True)

        self.repo.init_call(call_id)

        if self.repo.is_processed(call_id, chunk_id):
            return {"status": "duplicate"}

        self.repo.mark_processed(call_id, chunk_id)

        if not is_final:
            return {"status": "partial_ignored"}

        self.repo.push_chunk(call_id, text)
        self.repo.set_silence_emitted(call_id, False)

        risk_delta, interest_delta = calculate_risk_delta([text])

        if risk_delta != 0:
            self.repo.increment_risk(call_id, risk_delta)

        if interest_delta != 0:
            self.repo.increment_interest(call_id, interest_delta)

        new_score = int(self.repo.get_call(call_id).get("risk_score", 0))

        if new_score > RISK_THRESHOLD and not self.repo.is_risk_emitted(call_id):
            self.repo.set_risk_emitted(call_id, True)
            event_emmited = build_event(
                event_type="risk_threshold_exceeded",
                call_id=call_id,
                payload={"strategy": "neutral", "previous_strategy": "neutral"},
                risk_score=new_score,
                call_status="open",
            )
            self.repo.push_event(call_id, event_emmited)

        interest_score = int(self.repo.get_call(call_id).get("interest_score", 0))
        if interest_score > INTEREST_THRESHOLD and not self.repo.is_interest_emitted(call_id):
            self.repo.set_interest_emitted(call_id, True)
            event_emmited = build_event(
                event_type="interest_threshold_exceeded",
                call_id=call_id,
                payload={"strategy": "neutral", "previous_strategy": "neutral"},
                risk_score=new_score,
                call_status="open",
            )
            self.repo.push_event(call_id, event_emmited)
       

        hostility_result = detect_extreme_hostility(text)
        if hostility_result:
            hostility_type, hostility_score = hostility_result
            event_emmited = build_event(
                event_type=f"extreme_{hostility_type}",
                call_id=call_id,
                payload={"strategy": "neutral", "previous_strategy": "neutral"},
                risk_score=new_score,
                interest_score=interest_score,
                call_status="open",
            )
            self.repo.push_event(call_id, event_emmited)

        silence_active = self.repo.is_silence_emitted(call_id)

        last_ts = int(self.repo.get_call(call_id).get("last_ts", 0))
        if ts - last_ts > 10 and silence_active == False:  
            event_emmited = build_event(
                event_type="long_silence",
                call_id=call_id,
                payload={"strategy": "neutral", "previous_strategy": "neutral", "silence_duration": ts - last_ts},
                risk_score=new_score,
                interest_score=interest_score,
                call_status="open",
            )
            self.repo.push_event(call_id, event_emmited)
            self.repo.set_silence_emitted(call_id, True)


        close_event = is_call_closing(text)

        if close_event:
            current_status = self.repo.get_call(call_id).get("status", "active")
            
            if current_status != "closed":
                self.repo.set_status(call_id, "closed")
                
                event_emmited = build_event(
                    event_type="call_closed",
                    call_id=call_id,
                    payload={"closing_phrase": close_event, "strategy": "neutral", "previous_strategy": "neutral"},
                    risk_score=new_score, 
                    call_status="closed",
                )
                self.repo.push_event(call_id, event_emmited)

        self.repo.set_last_ts(call_id, ts)

        return {
            "call_id": call_id,
            "risk_score": new_score,
            "interest_score": int(self.repo.get_call(call_id).get("interest_score", 0)),
            "status": self.repo.get_call(call_id).get("status", "active"),
            "events":{
                "risk_threshold_exceeded": self.repo.is_risk_emitted(call_id),
                "interest_threshold_exceeded": self.repo.is_interest_emitted(call_id),
                "extreme_hostility": f"extreme_{hostility_type}" if hostility_result else None,
                "long_silence": (ts - last_ts) > 10 if last_ts > 0 else False,
                "call_closing": close_event is not None

            } 
        }
