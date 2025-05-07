import requests
import random
import time

URL = "http://localhost:8000/add"

while True:
    payload = {
        "x": random.randint(10, 790),
        "y": random.randint(10, 390),
        "label": f"pt{random.randint(1000, 9999)}"
    }

    try:
        res = requests.post(URL, json=payload)
        print(f"Sent: {payload}, Status: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)  # 500ms 간격
