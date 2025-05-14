import redis
import random
import string

r = redis.Redis(decode_responses=True)
QUEUE_KEY = "queue:list"

def random_user_id():
    return "user_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def bulk_enqueue(n=10000):
    pipeline = r.pipeline()
    for _ in range(n):
        uid = random_user_id()
        pipeline.rpush(QUEUE_KEY, uid)
    pipeline.execute()
    print(f"{n} users enqueued.")

if __name__ == "__main__":
    bulk_enqueue(1000000)  # 필요 시 숫자 조절
