from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import redis
import time

app = FastAPI()
app.mount("/web", StaticFiles(directory="static", html=True), name="static")
r = redis.Redis(decode_responses=True)

QUEUE_KEY = "queue:list"

class User(BaseModel):
    user_id: str

@app.post("/enqueue")
def enqueue(user: User):
    r.rpush(QUEUE_KEY, user.user_id)
    return {"status": "ok"}

@app.post("/dequeue")
def dequeue():
    popped = r.lpop(QUEUE_KEY)
    return {"removed": popped}


@app.get("/position")
def position(user_id: str):
    start = time.perf_counter()  # 고해상도 타이머 시작
    total = r.llen(QUEUE_KEY)
    try:
        pos = r.lpos(QUEUE_KEY, user_id)
    except:
        pos = None
    end = time.perf_counter()  # 종료

    elapsed_ms = round((end - start) * 1000, 2)  # ms 단위로 반환
    return {
        "position": pos,
        "total": total,
        "redis_elapsed_ms": elapsed_ms
    }


@app.get("/top_users")
def top_users(limit: int = 100):
    users = r.lrange(QUEUE_KEY, 0, limit - 1)
    return {"count": len(users), "users": users}


@app.get("/bottom_users")
def bottom_users(limit: int = 100):
    total = r.llen(QUEUE_KEY)
    start = max(0, total - limit)
    users = r.lrange(QUEUE_KEY, start, total - 1)
    return {"count": len(users), "users": users}


@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))
