from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import redis
import time


app = FastAPI()
app.mount("/web", StaticFiles(directory="static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(decode_responses=True)

# 데이터 모델
class Notice(BaseModel):
    title: str
    body: str

@app.post("/notice")
def write_notice(notice: Notice):
    notice_id = r.incr("announcement:next_id")
    r.set(f"announcement:{notice_id}:title", notice.title)
    r.set(f"announcement:{notice_id}:body", notice.body)
    r.lpush("announcement:list", notice_id)
    return {"id": notice_id}


@app.get("/notices")
def get_notices(page: int = 1, page_size: int = 10):
    start = (page - 1) * page_size
    end = start + page_size - 1

    total_start = time.time()

    # 리스트에서 ID 가져오는 시간 측정
    list_start = time.time()
    ids = r.lrange("announcement:list", start, end)
    list_end = time.time()
    list_elapsed_ms = round((list_end - list_start) * 1000, 2)

    # 제목 + 본문 가져오는 시간 측정
    content_start = time.time()
    title_keys = [f"announcement:{id}:title" for id in ids]
    body_keys = [f"announcement:{id}:body" for id in ids]

    titles = r.mget(title_keys)
    bodies = r.mget(body_keys)
    content_end = time.time()
    content_elapsed_ms = round((content_end - content_start) * 1000, 2)

    total_end = time.time()
    total_elapsed_ms = round((total_end - total_start) * 1000, 2)

    return {
        "page": page,
        "page_size": page_size,
        "total": r.llen("announcement:list"),
        "notices": [
            {"id": id, "title": title, "body": body}
            for id, title, body in zip(ids, titles, bodies)
        ],
        "total_elapsed_ms": total_elapsed_ms
    }



@app.get("/notice/{notice_id}")
def get_notice_detail(notice_id: str):
    title = r.get(f"announcement:{notice_id}:title")
    body = r.get(f"announcement:{notice_id}:body")
    if title is None or body is None:
        return {"error": "not found"}
    return {"id": notice_id, "title": title, "body": body}

@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))
