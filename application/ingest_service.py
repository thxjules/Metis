from infra.redis_repository import RedisRepository
from domain.engine import calculate_risk_delta, is_call_closing  # <- Nombres correctos

class IngestService:
    def __init__(self, repo: RedisRepository):
        self.repo = repo

    def ingest(self, payload: dict):
        call_id = payload["call_id"]
        chunk_id = payload.get("chunk_id", str(call_id))  # asegurar id
        text = payload["text"]
        ts = payload.get("ts", 0)
        is_final = payload.get("is_final", True)

        # 1. Inicializar llamada
        self.repo.init_call(call_id)

        # 2. Idempotencia
        if self.repo.is_processed(call_id, chunk_id):
            return {"status": "duplicate"}

        self.repo.mark_processed(call_id, chunk_id)

        # 3. Ignorar partials
        if not is_final:
            return {"status": "partial_ignored"}

        # 4. Ventana deslizante
        self.repo.push_chunk(call_id, text)
        window = self.repo.get_window(call_id)

        # 5. Procesar riesgo usando calculate_risk_delta
        delta = calculate_risk_delta(window)

        if delta != 0:
            new_score = self.repo.increment_risk(call_id, delta)
        else:
            new_score = int(self.repo.get_call(call_id).get("risk_score", 0))

        # 6. Detectar cierre usando is_call_closing
        close_event = is_call_closing(text)

        if close_event:
            self.repo.set_status(call_id, "closed")

        return {
            "call_id": call_id,
            "risk_score": new_score,
            "status": self.repo.get_call(call_id).get("status", "active")
        }