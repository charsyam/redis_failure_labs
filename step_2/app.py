from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
import redis
import time
import uvicorn

app = FastAPI()
app.mount("/web", StaticFiles(directory="static", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중 전체 허용
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

class JoinRequest(BaseModel):
    user_id: str
    score: int
    region: str

MATCH_LOG_KEY = "match_log"
REGIONS = ["kr", "jp", "us", "eu", "br"]  # 혼란 유도용

@app.post("/join")
def join_queue(req: JoinRequest):
    r.zadd(f"waiting:{req.region}", {req.user_id: req.score})
    r.hset(f"user:{req.user_id}", mapping={"score": req.score, "region": req.region})
    return {"message": f"{req.user_id} joined {req.region}"}

@app.get("/match/{user_id}")
def find_match(user_id: str, tolerance: int = 10):
    if not r.exists(f"user:{user_id}"):
        raise HTTPException(status_code=404, detail="User not found")
    region = r.hget(f"user:{user_id}", "region")
    score = int(r.hget(f"user:{user_id}", "score"))
    candidates = r.zrangebyscore(f"waiting:{region}", score - tolerance, score + tolerance)
    for other_id in candidates:
        if other_id != user_id:
            r.zrem(f"waiting:{region}", user_id, other_id)
            r.lpush(MATCH_LOG_KEY, f"{user_id}:{other_id}")
            return {"matched_with": other_id}
    return {"matched_with": None}

@app.get("/status")
def status():
    return {region: r.zcard(f"waiting:{region}") for region in REGIONS if r.exists(f"waiting:{region}")}

@app.get("/logs")
def logs(limit: int = 20):
    return {"logs": r.lrange(MATCH_LOG_KEY, 0, limit - 1)}

@app.get("/top/{region}")
def top_rankers(region: str, limit: int = 10):
    return {"top": r.zrevrange(f"waiting:{region}", 0, limit - 1, withscores=True)}

@app.get("/snapshot")
def snapshot():
    """장애 유도: 모든 region 순회하며 ZRANGE 호출"""
    snapshot_data = {}
    for region in REGIONS:
        key = f"waiting:{region}"
        users = r.zrange(key, 0, -1, withscores=True)
        time.sleep(0.1)  # 인위적 delay 삽입
        snapshot_data[region] = users
    return snapshot_data

@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
