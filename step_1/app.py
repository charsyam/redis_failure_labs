from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

import redis
import time
import random

app = FastAPI()
app.mount("/web", StaticFiles(directory="static", html=True), name="static")
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Point(BaseModel):
    x: int
    y: int
    label: str

@app.post("/add")
def bulk_add_points():
    now = int(time.time())
    pipe = r.pipeline()
    for i in range(10000):
        key = f"point:{now}:{i}"
        x = random.randint(10, 790)
        y = random.randint(10, 390)
        color = random.choice(["red", "blue", "green", "orange", "purple", "black"])
        pipe.set(key, f"{x},{y},{key},{color}")
    pipe.execute()
    return {"status": "ok", "inserted": 10000}

@app.get("/points")
def get_points():
    start = time.time()
    keys = r.keys("point:*")  # intentionally slow
    duration_ms = int((time.time() - start) * 1000)

    sampled_keys = random.sample(keys, min(100, len(keys)))
    points = []
    for key in sampled_keys:
        val = r.get(key)
        if val:
            try:
                x, y, label, color = val.split(",")
                points.append({
                    "x": int(x),
                    "y": int(y),
                    "label": label,
                    "color": color
                })
            except ValueError:
                continue

    return {
        "points": points,
        "duration_ms": duration_ms,
        "total": len(keys),
        "returned": len(points)
    }


@app.get("/")
def serve_index():
    return FileResponse(Path("static/index.html"))
