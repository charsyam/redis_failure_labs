import redis
import random

# Redis 연결
r = redis.Redis(decode_responses=True)

# 기본 파라미터
TOTAL_USERS = 100000  # 원하는 유저 수 설정
ZSET_KEY = "user_rank"

# 기존 데이터 제거 (선택 사항)
r.delete(ZSET_KEY)

# 유저 추가
pipe = r.pipeline()
for i in range(1, TOTAL_USERS + 1):
    user_id = f"user{i}"
    score = random.randint(1, TOTAL_USERS)  # 점수는 랜덤
    pipe.zadd(ZSET_KEY, {user_id: score})
    if i % 1000 == 0:
        pipe.execute()  # 배치 처리
pipe.execute()

print(f"{TOTAL_USERS} users added to Redis Sorted Set '{ZSET_KEY}'")
