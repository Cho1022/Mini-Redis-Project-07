# Mini Redis Requirements

## 1. 목표
- Redis와 유사한 TCP 기반 key-value 서버를 Python으로 구현한다.
- 최소 명령 세트와 TTL, 영속성 개념을 포함한 교육용 Mini Redis를 완성한다.
- 팀원이 병렬 개발할 수 있도록 인터페이스와 우선순위를 먼저 고정한다.

## 2. 우선순위

### P0. 반드시 먼저 끝낼 것
- `Command`, `Response`, `RedisError` 같은 core 모델 정의
- in-memory 저장소와 TTL 처리
- RESP parser / encoder
- dispatcher와 TCP 서버 연결

### P1. P0 다음에 붙일 것
- AOF append / replay
- RDB snapshot / load
- 통합 테스트와 demo client

### P2. 시간 남으면 확장
- cluster router
- benchmark 정리
- 발표용 scale-out 시나리오

## 3. 필수 기능

### 저장소
- 문자열 key, 문자열 value 저장
- 해시 테이블 기반 조회
- 기본 명령 지원
  - `PING`
  - `SET key value`
  - `GET key`
  - `DEL key`
  - `EXISTS key`
  - `EXPIRE key seconds`
  - `TTL key`

### TTL
- TTL은 초 단위로 관리한다.
- 만료 처리는 우선 lazy expiration 으로 구현한다.
- 만료된 키는 조회 시 제거한다.
- 만료 상태는 별도 저장값이 아니라 현재 시각 계산 결과로 판단한다.

### 프로토콜
- 요청과 응답은 RESP 기반으로 처리한다.
- 잘못된 요청은 에러 응답으로 돌려준다.
- 최소 RESP 타입
  - Array
  - Bulk String
  - Simple String
  - Integer
  - Error
  - Null Bulk String

### 서버
- TCP 소켓으로 요청을 받는다.
- 단일 클라이언트 동작부터 안정화한다.
- 예외가 발생해도 서버 프로세스 전체가 종료되지 않게 처리한다.

### 영속성
- RDB: 현재 메모리 상태를 파일로 snapshot 저장
- AOF: write 계열 명령을 append log로 저장
- 서버 재시작 시 AOF replay 또는 RDB load 전략을 설명할 수 있어야 한다.

## 4. 모듈별 계약

### `src/core/command.py`
- 역할: parser가 생성하는 내부 명령 객체
- 필드 예시
  - `name: str`
  - `args: list[str]`

### `src/core/response.py`
- 역할: dispatcher가 반환하는 내부 응답 객체
- 필드 예시
  - `kind: str`
  - `value: object | None`
  - `message: str | None`

### `src/storage/engine.py`
- 역할: dispatcher가 호출하는 저장 엔진 추상 인터페이스
- 최소 메서드
  - `set(key: str, value: str) -> None`
  - `get(key: str) -> str | None`
  - `delete(key: str) -> int`
  - `exists(key: str) -> int`
  - `expire(key: str, seconds: int) -> int`
  - `ttl(key: str) -> int`

### `src/server/dispatcher.py`
- 역할: `Command`를 받아 storage/persistence 로직을 호출하고 `Response`로 반환
- 규칙
  - 프로토콜 상세를 몰라야 한다.
  - 저장소 구현체 교체 가능해야 한다.

### `src/protocol/resp_parser.py`
- 입력: `bytes`
- 출력: `Command`

### `src/protocol/resp_encoder.py`
- 입력: `Response`
- 출력: `bytes`

## 5. 비기능 요구사항
- 코드가 비어 있는 상태여도 폴더 책임은 문서와 일치해야 한다.
- 표준 라이브러리 중심으로 구현하고, 의존성은 최소화한다.
- 테스트는 `pytest` 기준으로 작성한다.
- 파일 경로는 프로젝트 루트 기준 상대 경로를 사용한다.

## 6. 검증 기준
- parser 단위 테스트
- storage/TTL 단위 테스트
- dispatcher 단위 테스트
- TCP 통합 테스트
- 영속성 save/load 기본 테스트

## 7. 이번 단계 산출물
- `requirements.md`: 구현 기준서
- `AGENT.md`: 역할/순서 문서
- `README.md`: 프로젝트 개요와 실행 방법
- `docs/aof.md`: AOF 설계 문서
- `docs/rdb.md`: RDB 설계 문서
