import redis
import json
from typing import Optional

class RedisRepository:
    def __init__(self, url="redis://localhost:6379/0"):
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def _call_key(self, call_id: str) -> str:
        return f"call:{call_id}"

    def _chunks_key(self, call_id: str) -> str:
        return f"call:{call_id}:chunks"

    def _processed_key(self, call_id: str) -> str:
        return f"call:{call_id}:processed"

    # Idempotencia
    def is_processed(self, call_id: str, chunk_id: str) -> bool:
        return self.client.sismember(self._processed_key(call_id), chunk_id)

    def mark_processed(self, call_id: str, chunk_id: str):
        self.client.sadd(self._processed_key(call_id), chunk_id)
        self.client.expire(self._processed_key(call_id), 3600)

    #Estado
    def init_call(self, call_id: str):
        key = self._call_key(call_id)
        if not self.client.exists(key):
            self.client.hset(key, mapping={
                "risk_score": 0,
                "status": "active"
            })
            self.client.expire(key, 3600)

    def increment_risk(self, call_id: str, delta: int) -> int:
        return self.client.hincrby(self._call_key(call_id), "risk_score", delta)

    def get_call(self, call_id: str) -> dict:
        return self.client.hgetall(self._call_key(call_id))

    def set_status(self, call_id: str, status: str):
        self.client.hset(self._call_key(call_id), "status", status)

    def push_chunk(self, call_id: str, text: str, max_len: int = 5):
        key = self._chunks_key(call_id)
        self.client.rpush(key, text)
        self.client.ltrim(key, -max_len, -1)
        self.client.expire(key, 3600)

    def get_window(self, call_id: str):
        return self.client.lrange(self._chunks_key(call_id), 0, -1)