# AGENT.md

## 목적
- 팀원이 병렬로 작업해도 충돌이 적도록 역할과 선행 조건을 고정한다.
- 구현 전에 반드시 합의해야 하는 인터페이스와 문서 책임을 명확히 한다.

## 역할 분담

### 1번. 서버 흐름 담당
- 담당 파일
  - `src/server/tcp_server.py`
  - `src/server/dispatcher.py`
- 책임
  - TCP 서버 소켓 생성 및 클라이언트 연결 수락
  - 수신 바이트를 parser로 전달
  - dispatcher를 통해 command 실행 연결
  - 실행 결과를 encoder로 직렬화 후 응답 송신
  - 예외가 나도 서버 프로세스가 종료되지 않도록 보호
- 완료 기준
  - 단일 요청이 `recv -> parse -> dispatch -> encode -> send` 흐름으로 연결된다.
  - 잘못된 입력에서도 서버가 죽지 않는다.

### 2번. 프로토콜 담당
- 담당 파일
  - `src/protocol/resp_parser.py`
  - `src/protocol/resp_encoder.py`
- 책임
  - RESP Array/Bulk String 기반 요청 파싱
  - 파싱 결과를 내부 `Command` 객체로 변환
  - 내부 `Response` 객체를 RESP 응답 문자열로 변환
  - 잘못된 프로토콜 형식 검증
- 완료 기준
  - `PING`, `SET`, `GET`, `DEL`, `EXISTS`, `EXPIRE`, `TTL` 요청을 파싱할 수 있다.
  - 성공/에러 응답을 RESP로 일관되게 인코딩한다.

### 3번. 저장소/TTL 담당
- 담당 파일
  - `src/storage/engine.py`
  - `src/storage/in_memory.py`
  - `src/storage/expiration.py`
- 책임
  - 해시 테이블 기반 key-value 저장
  - `SET`, `GET`, `DEL`, `EXISTS` 구현
  - TTL 설정 및 lazy expiration 처리
  - invalidate 정책 합의 후 반영
- 완료 기준
  - 만료되지 않은 키는 즉시 조회 가능하다.
  - 만료된 키는 조회 시 제거된다.
  - 핵심 명령 단위 테스트가 존재한다.

### 4번. 영속성/확장/문서 담당
- 담당 파일
  - `src/persistence/rdb.py`
  - `src/persistence/aof.py`
  - `src/cluster/router.py`
  - `README.md`
  - `docs/aof.md`
  - `docs/rdb.md`
- 책임
  - RDB snapshot 저장/복구 흐름 설계
  - AOF append/replay 흐름 설계
  - 서버 재시작 시 복구 절차 문서화
  - scale-out 설명용 router 설계
  - README, 발표 자료, 한계점 정리
- 완료 기준
  - persistence 구현 범위와 비구현 범위가 문서에 명확히 적혀 있다.
  - 발표용 아키텍처 설명이 README와 docs에 반영된다.

## 협업 순서
1. `src/core/command.py`, `src/core/response.py`, `src/core/exceptions.py` 인터페이스 확정
2. storage 담당이 저장 엔진 메서드 시그니처 확정
3. protocol 담당이 parser/encoder 작성
4. server 담당이 dispatcher 작성
5. server 담당이 tcp server와 parser/dispatcher/encoder 연결
6. persistence 담당이 RDB/AOF 및 router 설계 연결
7. 통합 테스트 작성
8. README와 발표 자료 정리

## 공통 규칙
- `main` 브랜치에 직접 push 하지 않는다.
- 비어 있는 파일부터 무작정 구현하지 말고 인터페이스를 먼저 맞춘다.
- 예외 메시지는 사용자가 이해할 수 있는 RESP 에러 형식으로 통일한다.
- TTL은 우선 lazy expiration 방식으로 구현한다.
- persistence와 cluster는 1차 목표가 아니라 storage/server/protocol이 안정화된 뒤 붙인다.

## 발표 포인트
- 저장소는 해시 테이블 기반으로 빠른 조회를 제공한다.
- RESP parser/encoder가 Redis와 유사한 통신 규약을 만든다.
- 서버는 요청 하나가 끝까지 실행되도록 흐름을 제어한다.
- persistence는 인메모리 한계를 보완하는 전략으로 설명한다.
