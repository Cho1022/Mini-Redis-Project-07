# AOF Design

## 목적
- write 계열 명령을 순서대로 기록해 서버 재시작 시 복구할 수 있도록 한다.
- 구현 난도를 낮추기 위해 Mini Redis에서는 단순 append + replay 전략부터 적용한다.

## 왜 필요한가
- Mini Redis는 기본적으로 인메모리 저장소이므로 프로세스가 종료되면 데이터가 사라진다.
- AOF는 명령 로그를 남겨 마지막 snapshot 이후 변경분까지 복구하는 데 유리하다.

## 저장 대상
- 기록 대상
  - `SET`
  - `DEL`
  - `EXPIRE`
- 기록 제외
  - `GET`
  - `EXISTS`
  - `TTL`
  - `PING`

## 파일 형식
- 루트 파일: `appendonly.aof`
- 각 명령은 RESP 또는 재생 가능한 텍스트 형식 중 하나로 저장한다.
- 발표와 구현 단순성을 위해 RESP 그대로 저장하는 방식을 우선 권장한다.

## 동작 흐름
1. dispatcher가 write 명령을 성공적으로 수행한다.
2. persistence 레이어가 명령을 `appendonly.aof` 끝에 append 한다.
3. 서버 재시작 시 AOF 파일을 처음부터 읽는다.
4. parser 또는 전용 replay 로직이 명령을 복원한다.
5. 저장 엔진에 순서대로 다시 적용한다.

## 제안 인터페이스
- `append(command: Command) -> None`
- `replay(engine: StorageEngine) -> None`
- `fsync() -> None`

## 예외 처리 원칙
- AOF 기록 실패는 무시하면 안 된다.
- 최소 단계에서는 에러를 로그로 남기고 클라이언트에 내부 오류를 반환한다.
- 부분 기록이 발생하면 서버 재시작 시 손상된 마지막 명령을 감지해야 한다.

## 장점
- 마지막 write 시점까지 복구 가능성이 높다.
- 구현 개념이 직관적이라 발표 설명이 쉽다.

## 단점
- 파일이 계속 커진다.
- 재시작 시 replay 시간이 길어진다.
- 중간 손상 복구 로직이 필요하다.

## Mini Redis 범위
- 1차 구현
  - append
  - startup replay
  - write 명령만 기록
- 선택 구현
  - AOF rewrite
  - fsync 정책 분리
  - checksum 검증

## 발표 포인트
- "메모리 상태 자체가 아니라 명령의 이력을 저장한다."
- "재시작 시 같은 명령을 다시 실행해서 상태를 복원한다."
