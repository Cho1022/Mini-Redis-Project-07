# Mini Redis

Python으로 구현하는 교육용 Mini Redis 프로젝트입니다. TCP 서버, RESP 프로토콜, in-memory 저장소, TTL, 그리고 AOF/RDB 영속성 개념까지 단계적으로 붙이는 것을 목표로 합니다.

## 프로젝트 목표
- Redis와 유사한 요청/응답 흐름 구현
- 해시 테이블 기반 key-value 저장소 구현
- TTL 및 lazy expiration 처리
- RESP parser / encoder 구현
- AOF / RDB 기반 복구 전략 정리
- 발표 가능한 수준의 문서와 구조 확보

## 우선순위
1. storage 인터페이스와 core 모델 고정
2. RESP parser / encoder 구현
3. dispatcher와 TCP server 연결
4. TTL 검증 및 통합 테스트
5. AOF / RDB 설계와 구현
6. cluster router 및 benchmark 정리

## 현재 폴더 구조
```text
Mini-Redis/
├─ src/
│  ├─ cluster/
│  ├─ core/
│  ├─ persistence/
│  ├─ protocol/
│  ├─ server/
│  ├─ storage/
│  └─ utils/
├─ scripts/
├─ tests/
├─ docs/
├─ AGENT.md
├─ README.md
├─ requirements.md
├─ requirements.txt
├─ appendonly.aof
└─ dump.rdb
```

## 주요 모듈
- `src/server`: TCP 연결 수락, 요청 수신, dispatcher 연결
- `src/protocol`: RESP 요청 파싱과 응답 인코딩
- `src/storage`: 실제 key-value 저장과 TTL 처리
- `src/persistence`: RDB snapshot, AOF append/replay
- `src/cluster`: 확장 설명용 key routing 구조

## 기본 명령 범위
- `PING`
- `SET key value`
- `GET key`
- `DEL key`
- `EXISTS key`
- `EXPIRE key seconds`
- `TTL key`

## 작업 규칙
- 구현은 `requirements.md`와 `AGENT.md`를 먼저 기준으로 삼습니다.
- P0 범위는 storage, protocol, server 연결입니다.
- persistence와 cluster는 핵심 흐름 안정화 후 붙입니다.
- `main` 브랜치 직접 push는 피합니다.

## 문서 안내
- `requirements.md`: 기능 요구사항과 모듈 인터페이스
- `AGENT.md`: 역할 분담과 협업 순서
- `docs/aof.md`: append-only file 설계
- `docs/rdb.md`: snapshot 설계

## 실행 예정 방식
프로젝트 구현이 진행되면 아래 흐름으로 실행하는 것을 기준으로 합니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.main
```

## 테스트 예정 방식
```bash
pytest -q
```

현재 저장소는 초기 골격 단계이므로, 먼저 문서로 인터페이스와 우선순위를 고정한 뒤 구현을 시작합니다.
