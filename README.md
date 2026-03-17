# Mini Redis (Flask)

Python + Flask 기반 Mini Redis 프로젝트.

## 1. 프로젝트 목표
- Hash Table 기반 Key-Value Store 구현
- TTL 만료 처리 구현
- Invalidation 구현
- Flask API 제공
- Snapshot 저장/복구 구현
- 캐시 사용/미사용 성능 비교

## 2. 팀 역할
- A: Core Engine / Hash Table / Lock
- B: Flask API / Demo API
- C: TTL / Invalidation / Cleanup
- D: Persistence / Benchmark / README

## 3. 폴더 구조
```text
mini-redis/
├─ app/
│  ├─ __init__.py
│  ├─ common/
│  ├─ core/
│  ├─ expiration/
│  ├─ api/
│  ├─ persistence/
│  └─ demo/
├─ tests/
├─ docs/
├─ benchmark/
├─ data/
├─ .github/
├─ AGENT.md
├─ README.md
├─ requirements.txt
└─ run.py
```

## 4. 핵심 정책
- delete = 물리 삭제
- invalidate = 논리 무효화
- expired = 저장된 상태가 아니라 시간 계산 결과
- main 브랜치 직접 push 금지
- .venv 는 git에 올리지 않음

## 5. 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

## 6. 테스트
```bash
pytest -q
```

## 7. API
- PUT /api/v1/cache/<key>
- GET /api/v1/cache/<key>
- DELETE /api/v1/cache/<key>
- POST /api/v1/cache/<key>/invalidate
- POST /api/v1/demo/fetch-and-cache

자세한 내용은 `docs/api-spec.md` 참고.
