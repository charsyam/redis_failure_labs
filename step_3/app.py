from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import redis
import time
import redis
import random


app = FastAPI()
app.mount("/web", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(decode_responses=True)

@app.get("/user_match")
def get_user_match(user_id: str, count: int = 10, segments: int = 10):
    redis_start = time.time()

    all_users = r.zrevrange("user_rank", 0, -1, withscores=True)

    redis_end = time.time()
    redis_elapsed_ms = round((redis_end - redis_start) * 1000, 2)

    total = len(all_users)
    if total == 0:
        return {"error": "no users", "redis_elapsed_ms": redis_elapsed_ms}

    # 현재 유저 랭크/점수 찾기
    user_rank = None
    user_score = None
    for i, (uid, score) in enumerate(all_users):
        if uid == user_id:
            user_rank = i + 1  # 1-based rank
            user_score = score
            break

    if user_rank is None:
        return {"error": "user not found", "redis_elapsed_ms": redis_elapsed_ms}

    # 전체 유저를 세그먼트로 나누고, 각 세그먼트에서 일부 랜덤 추출
    chunk_size = total // segments
    users_per_chunk = max(1, count // segments)
    sampled_candidates = []

    for i in range(segments):
        start = i * chunk_size
        end = total if i == segments - 1 else start + chunk_size
        chunk = all_users[start:end]
        chunk_sample = random.sample(chunk, min(users_per_chunk, len(chunk)))
        enriched = [(uid, score, start + idx + 1) for idx, (uid, score) in enumerate(chunk_sample)]
        sampled_candidates.extend(enriched)

    # 자신 제외 + 점수 차이 기준 정렬
    filtered = [
        (uid, score, rank, abs(score - user_score))
        for uid, score, rank in sampled_candidates
        if uid != user_id
    ]
    sorted_by_similarity = sorted(filtered, key=lambda x: x[3])[:count]

    # 응답 포맷 정리
    matched_users = [(uid, score, rank) for uid, score, rank, _ in sorted_by_similarity]

    return {
        "your_rank": user_rank,
        "your_score": user_score,
        "matched_users": matched_users,
        "total_users": total,
        "redis_elapsed_ms": redis_elapsed_ms
    }

@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))

@app.get("/random_users")
def get_random_users(count: int = 30):
    all_users = r.zrevrange("user_rank", 0, -1, withscores=True)
    total = len(all_users)

    # ID, score, rank 정보를 붙여서 리스트 구성
    enriched = [(uid, score, i + 1) for i, (uid, score) in enumerate(all_users)]
    # 랜덤 샘플링
    sampled = random.sample(enriched, min(count, len(enriched)))

    return {
        "total_users": total,
        "random_users": sampled
    }
