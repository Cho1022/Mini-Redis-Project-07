# RDB Design

## 목적
- 현재 메모리 상태를 시점 단위 snapshot 으로 저장한다.
- 재시작 시 빠르게 전체 상태를 복원할 수 있게 한다.

## 왜 필요한가
- AOF는 복구 범위가 넓지만 로그가 길어질 수 있다.
- RDB는 특정 시점의 상태를 한 번에 저장하므로 로딩 속도와 설명 측면에서 단순하다.

## 저장 대상
- key
- value
- 만료 시각이 있는 경우 absolute expiration timestamp

## 파일 형식
- 루트 파일: `dump.rdb`
- 실제 Redis 바이너리 포맷을 완전히 재현할 필요는 없다.
- Mini Redis에서는 Python 친화적인 직렬화 포맷을 써도 된다.
  - 예: JSON
  - 예: pickle
- 발표용으로는 "snapshot 파일"이라는 개념을 명확히 설명하는 것이 중요하다.

## 동작 흐름
1. 특정 시점에 storage 전체 상태를 읽는다.
2. 직렬화 가능한 구조로 변환한다.
3. `dump.rdb` 파일로 저장한다.
4. 서버 시작 시 파일이 존재하면 읽는다.
5. 만료되지 않은 데이터만 메모리로 복원한다.

## 제안 인터페이스
- `save_snapshot(engine: StorageEngine) -> None`
- `load_snapshot(engine: StorageEngine) -> None`

## TTL 처리 원칙
- TTL 남은 시간 대신 만료 절대 시각을 저장하는 편이 안정적이다.
- 로드 시점 기준으로 이미 만료된 키는 복원하지 않는다.

## 장점
- 로딩이 빠르다.
- 파일 크기가 비교적 작다.
- 구현 설명이 단순하다.

## 단점
- snapshot 이후 변경분은 반영되지 않는다.
- 저장 시점에 따라 데이터 유실 구간이 생길 수 있다.

## Mini Redis 범위
- 1차 구현
  - 수동 snapshot 저장
  - 시작 시 snapshot 로드
  - TTL 포함 상태 직렬화
- 선택 구현
  - 주기적 snapshot
  - atomic temp file 교체
  - compression

## AOF와 비교
- RDB는 "상태를 저장"한다.
- AOF는 "명령을 저장"한다.
- Mini Redis 발표에서는 둘의 trade-off를 같이 설명하면 좋다.

## 발표 포인트
- "메모리의 현재 상태를 파일 하나로 저장해 빠르게 복원한다."
- "AOF보다 단순하지만 마지막 시점까지 복구되지는 않을 수 있다."
