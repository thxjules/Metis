from fastapi import FastAPI
from pydantic import BaseModel
from application.ingest_service import IngestService
from infra.redis_repository import RedisRepository

app = FastAPI()

repo = RedisRepository()
service = IngestService(repo)

class Chunk(BaseModel):
    call_id: str
    chunk_id: str
    text: str
    ts: int
    is_final: bool
    speaker: str
    confidence: float

@app.post("/ingest")
async def ingest(chunk: Chunk):
    return service.ingest(chunk.dict())