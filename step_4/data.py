import redis
import random

r = redis.Redis(decode_responses=True)

# 초기화 (선택)
r.delete("announcement:list")
r.delete("announcement:next_id")

# 기본 본문
base_body = "공지사항 내용입니다. 중요합니다.\n" * 10
base_title = "일반 공지사항"

for i in range(1, 101):
    title = f"{base_title} #{i}"

    # 중간 하나만 매우 큰 본문 (ID 50)
    if i == 100:
        big_body = "🚨 중대한 보안 공지입니다.\n" * 2000000  # 약 4~5MB 정도
        body = big_body
    else:
        body = base_body + str(random.randint(0, 10000))

    # ID 증가 및 저장
    notice_id = r.incr("announcement:next_id")
    r.set(f"announcement:{notice_id}:title", title)
    r.set(f"announcement:{notice_id}:body", body)
    r.lpush("announcement:list", notice_id)

print("✅ 공지사항 100개 등록 완료 (ID 50은 대용량)")
