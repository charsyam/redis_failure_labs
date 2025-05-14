import requests
import random
import time
import sys

user_id = ""
if len(sys.argv) > 1:
    user_id = sys.argv[1]

URL = "http://localhost:8000/position?user_id={user_id}"

while True:
    try:
        res = requests.get(URL)
        print(f"Sent: Status: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(1)  # 500ms 간격
