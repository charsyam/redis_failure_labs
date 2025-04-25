from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

import redis
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

class Message(BaseModel):
    user_id: str
    content: str

@app.post("/register")
def register_user(user_id: str):
    r.sadd("users", user_id)
    return {"status": "ok"}

@app.post("/send_message")
def send_msg(msg: Message):
    r.incr("msg_id")  # 증가시키고 키 조합
    r.set(f"msg:{msg.user_id}:{r.get('msg_id')}", msg.content)
    return {"status": "ok"}

@app.get("/admin/search_messages")
def search_msg(prefix: str):
    keys = r.keys(f"msg:{prefix}*")  # 🚨 keys 사용으로 인한 장애 포인트
    msgs = {key: r.get(key) for key in keys}
    return msgs

@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
