# Mini Redis

Python으로 구현한 교육용 Mini Redis 프로젝트입니다.  
이번 프로젝트의 목표는 단순히 key-value 저장소를 만드는 것이 아니라, **Redis의 핵심 개념인 해시 테이블 기반 저장, TTL, RESP 프로토콜, TCP 서버 흐름, 영속성 확장 가능성**까지 직접 구현하고 설명할 수 있는 수준까지 도달하는 것이었습니다.

우리는 프로젝트를 4개의 역할로 나누어 병렬로 개발했고, 각 모듈이 서로 연결되어 하나의 Mini Redis 서버로 동작하도록 구성했습니다.

---

# 1. 프로젝트 목표

이번 과제의 핵심 목표는 다음과 같았습니다.

- 해시 테이블을 활용한 key-value 저장소 구현
- 외부에서 사용할 수 있는 Mini Redis 서버 구현
- 저장, 조회, 삭제, TTL, 무효화 기능 구현
- Redis 스타일 프로토콜(RESP) 처리
- 동시성, 만료, 무효화, 영속성, 확장성에 대한 설계 고민
- 테스트를 통한 기능 검증
- README만으로 발표 가능한 수준의 설명 정리

즉, 단순 CRUD 구현이 아니라 **“Redis를 어느 정도 이해한 상태에서 Mini Redis를 직접 설계하고 설명하는 프로젝트”**를 목표로 했습니다.

---

# 2. 구현 범위

현재 TM 브랜치 기준으로 구현된 범위는 다음과 같습니다.

## 구현된 기능
- TCP 서버 기반 요청/응답 처리
- RESP 프로토콜 파싱 및 인코딩
- 해시 테이블 기반 in-memory 저장소
- `PING`
- `SET key value`
- `GET key`
- `DEL key`
- `EXISTS key`
- `EXPIRE key seconds`
- `TTL key`
- `invalidate` 처리
- lazy expiration 방식 TTL 처리
- RDB snapshot save/load 모듈
- AOF append/replay 모듈
- cluster router 모듈
- 단위 테스트 및 일부 통합 테스트

## 아직 완전 통합되지 않은 부분
- RDB/AOF가 현재 서버 실행 흐름에 완전히 연결되지는 않음
- persistence를 통한 실제 서버 재시작 복구 흐름은 추가 통합 필요
- cluster router는 확장 설계 수준이며 실제 분산 실행 구조는 아님
- HTTP API 형태는 구현하지 않았고, TCP + RESP 인터페이스로 외부 사용 가능하게 구성함
- Redis를 썼을 때와 안 썼을 때의 성능 비교는 benchmark 및 시각화 보조 자료 기반으로 준비 중

즉 현재 프로젝트는 **Mini Redis의 핵심 구조와 저장소 동작, 프로토콜, 테스트 흐름까지는 구현되었고, 영속성과 scale-out은 확장 단계까지 도달한 상태**라고 볼 수 있습니다.

---

# 3. 전체 구조

프로젝트의 전체 흐름은 아래와 같습니다.

```text
클라이언트
  ↓
TCP Server
  ↓
RESP Parser
  ↓
Dispatcher
  ↓
Storage Engine
  ↓
InMemory Store + Expiration Manager
  ↓
Response 생성
  ↓
RESP Encoder
  ↓
클라이언트 응답
보조적으로 다음 모듈이 존재합니다.

persistence/rdb.py
persistence/aof.py
cluster/router.py
즉 현재 구조는 단일 서버 기반 Mini Redis 코어를 구현하고, 영속성과 확장성은 모듈 단위로 준비한 구조입니다.
```
# 4. 역할 분담
1번. 서버 흐름 담당
담당 파일
server/tcp_server.py
server/dispatcher.py
역할
클라이언트 TCP 연결 수락
요청 바이트 수신
parser로 요청 전달
dispatcher를 통해 storage와 연결
응답을 다시 encoder를 통해 클라이언트로 전송
예외 발생 시 서버 전체가 종료되지 않도록 보호
동시성 처리 구조 설명
핵심 책임
서버의 입구
요청 처리 흐름 제어
명령 하나가 끝까지 실행되도록 연결
발표 포인트
“클라이언트 요청을 받아 내부 실행 흐름으로 전달하는 역할”
“동시성 문제를 줄이기 위해 단일 이벤트 루프 기반 비동기 구조를 사용했다”
구현 평가
서버 흐름은 전체 구조에서 가장 중요한 연결부였고, 현재 recv -> parse -> dispatch -> encode -> send 흐름이 통합 테스트 수준에서 확인됩니다. 특히 fragmented request, multiple commands in one buffer 등 실제 네트워크 상황을 고려한 처리가 잘 들어가 있다는 점이 강점입니다.

2번. 프로토콜 담당
담당 파일
protocol/resp_parser.py
protocol/resp_encoder.py
역할
RESP 요청 형식 파싱
바이트 데이터를 Command 객체로 변환
내부 Response를 RESP 응답 형식으로 인코딩
잘못된 프로토콜 형식 검증
Redis 명령 형식을 어떻게 해석하는지 설명
핵심 책임
클라이언트와 서버 사이의 대화 규칙 구현
요청/응답 번역
발표 포인트
“RESP는 Redis가 사용하는 프로토콜”
“parser는 요청을 내부 명령 객체로 바꾸고, encoder는 실행 결과를 RESP 형식으로 바꾼다”
구현 평가
RESP parser/encoder는 Mini Redis가 “Redis처럼 보이게 만드는” 핵심 요소였습니다. 단순 문자열 처리가 아니라 RESP bulk string, integer, error, null bulk string까지 다루고 있어 교육용 Mini Redis로서 완성도를 높여줍니다. 특히 parser가 malformed input과 incomplete buffer를 구분하는 점이 좋았습니다.

3번. 저장소/TTL 담당
담당 파일
storage/engine.py
storage/in_memory.py
storage/expiration.py
역할
실제 key-value 저장
SET, GET, DEL, EXISTS 구현
TTL 설정 및 만료 처리
invalidate 처리
lazy expiration 로직 구현
해시 테이블 기반 저장 구조 설명
핵심 책임
Mini Redis의 핵심 로직
실제 데이터 저장과 조회
만료/삭제/무효화 정책
발표 포인트
“해시 테이블(Map/dict) 기반으로 빠르게 조회할 수 있게 구현했다”
“만료된 키는 조회 시 확인하고 제거하는 방식으로 처리했다”
구현 평가
이 영역이 프로젝트의 중심이었고, 실제로 Redis다운 느낌을 만드는 핵심이었습니다. Python의 dict를 활용해 key lookup을 빠르게 만들었고, TTL은 ExpirationManager를 통해 별도 관리했습니다. 특히 lazy expiration 방식은 구현 난이도 대비 설명력이 좋아 발표용으로도 적합했습니다.

4번. 영속성/확장/문서 담당
담당 파일
persistence/rdb.py
persistence/aof.py
cluster/router.py
추가 역할
테스트 보조
발표 정리
역할
RDB 방식 snapshot 저장/복구
AOF 방식 명령 로그 저장/복구
서버 재시작 시 데이터 복구 흐름 정리
cluster/router로 scale-out 구조 설명
확장성, 복구 전략, 한계점 정리
AI 활용 회고 정리
핵심 책임
장애 복구
확장성
발표 자료 정리
발표 포인트
“인메모리 기반이라 서버 종료 시 유실될 수 있으므로 영속성 전략을 고려했다”
“확장성을 위해 key routing 구조를 설계했다”
“README를 통해 구현 범위와 테스트 결과를 정리했다”
구현 평가
이 부분은 현재 서버 흐름과 완전 통합되기보다는 확장 가능성을 보여주는 구조로 구현되었습니다. RDB는 snapshot save/load, AOF는 append/replay, router는 hash slot 기반 노드 분배라는 개념이 잘 드러납니다. 과제의 Optional 성격에 맞게 “실제 운영형 완성도”보다는 “구조 설계와 원리 구현”에 초점을 둔 점이 적절했습니다.
---
# 5. 우리가 Redis를 어느 정도 구현했는가
우리는 현재 Redis를 100% 재현한 것이 아니라, 교육용 Mini Redis로서 핵심 개념을 충분히 설명 가능한 수준까지 구현했습니다.

현재 구현한 Redis 핵심 요소
key-value 저장
해시 테이블 기반 조회
RESP 프로토콜
TCP 기반 외부 사용 가능 구조
TTL / lazy expiration
invalidate/delete
기본 명령 처리
단위/통합 테스트
RDB / AOF / Router 모듈
아직 구현하지 않은 것
진짜 Redis 수준의 persistence 통합
replication
cluster 분산 실행
고급 자료구조(list, set, sorted set)
메모리 eviction 정책
실제 Redis와 완전히 동일한 명령어 세트
운영 수준 성능 최적화
즉 현재 수준은
“Redis의 핵심 작동 원리를 이해하고 설명할 수 있는 Mini Redis” 입니다.
---
# 6. 중점 포인트에 대한 답변
동시성
현재는 asyncio 기반 단일 이벤트 루프 구조를 사용합니다.
즉 여러 클라이언트가 접속할 수 있지만, Python 로직은 단일 서버 흐름에서 비교적 단순하게 처리됩니다. 이를 통해 복잡한 lock보다 구조적 단순성으로 동시성 문제를 줄이는 방향을 택했습니다.

만료 처리
TTL은 ExpirationManager가 만료 시각을 따로 저장하고, GET, EXISTS, TTL, DEL 등의 접근 시점에 lazy expiration으로 처리합니다. 즉 만료된 키는 접근할 때 확인 후 제거합니다.

외부 사용 구조
현재는 HTTP API 대신 TCP + RESP 인터페이스를 제공하여 외부 클라이언트가 Redis 스타일 명령을 사용할 수 있도록 했습니다.

무효화 방식
현재 invalidate는 delete와 동일하게 즉시 삭제하는 방식으로 구현했습니다. 향후 deprecated 플래그 기반 soft invalidation으로 확장할 수 있습니다.

서버 다운 시 데이터 유지
현재 RDB/AOF 모듈을 구현했지만, 서버 실행 흐름과의 완전 통합은 다음 단계 과제입니다. 따라서 “영속성 전략 구현”까지는 완료되었고, “실제 재시작 복구 완전 통합”은 보완 포인트입니다.
---
# 7. 테스트와 검증
현재 테스트는 다음과 같이 구성되어 있습니다.

단위 테스트
RESP parser
RESP encoder
storage
persistence
router
통합 테스트
dispatcher 흐름
tcp server end-to-end 흐름
검증한 내용:

저장/조회/삭제가 정상 동작하는지
TTL 설정과 만료 처리
fragmented request 처리
여러 명령이 한 버퍼에 들어왔을 때 처리
persistence save/load, replay 동작
즉, 현재 코드베이스는 단순 구현 수준을 넘어서 핵심 로직을 테스트로 검증한 상태입니다.
---
# 8. 성과
이번 프로젝트에서 얻은 가장 큰 성과는 다음과 같습니다.

Redis의 핵심 구조를 직접 구현하며 내부 동작을 이해하게 됨
단순 CRUD가 아니라 TCP/RESP/TTL/영속성까지 확장된 구조를 설계함
역할 분담 후 병렬 개발이 가능하도록 인터페이스 중심으로 작업함
테스트 코드까지 작성해 “동작한다”를 검증 가능한 상태로 만듦
README 기반 발표가 가능할 정도로 구조와 흐름을 정리함
즉, 단순히 코드를 생성한 것이 아니라 설명 가능한 구현물을 만드는 데 성공했습니다.
---
# 9. 잘된 점
1. 역할 분담이 비교적 명확했다
서버, 프로토콜, 저장소, 영속성/확장으로 나눈 구조가 실제 폴더 구조와 잘 맞아떨어졌습니다.

2. Mini Redis다운 핵심이 살아 있다
RESP, TCP 서버, 해시 테이블, TTL, lazy expiration까지 들어가 있어서 단순 key-value 앱이 아니라 Redis 느낌이 납니다.

3. 테스트가 들어갔다
구현만 한 것이 아니라 parser, storage, tcp 흐름까지 테스트 코드가 있어서 발표 신뢰도가 높습니다.

4. 구조 설명이 쉽다
요청 흐름이 클라이언트 -> 서버 -> parser -> dispatcher -> storage -> encoder로 명확해 발표에 적합합니다.
---
# 10. 부족한 점
1. persistence가 서버 실행 흐름에 완전 통합되지 않았다
RDB/AOF 파일은 구현했지만, 실제 서버 시작/종료와 자동으로 연결되지는 않았습니다.

2. HTTP API는 구현하지 않았다
외부 사용은 TCP/RESP로 충분히 가능하지만, REST API 요구를 직접 충족하는 방향은 아닙니다.

3. Redis 사용 전/후 성능 비교는 보조 자료 수준이다
benchmark 및 시각화 준비는 가능하지만, 아직 최종 측정 데이터 기반 발표까지 완결된 상태는 아닙니다.

4. 고급 Redis 기능은 미구현
list, set, sorted set, replication, eviction, persistence 통합 등은 아직 없습니다.
---
# 11. AI 활용 회고
이번 프로젝트는 AI를 적극적으로 활용해 구현 속도를 높이는 데 큰 도움을 받았습니다.
특히 다음에서 효과가 좋았습니다.

폴더 구조 설계
역할 분배 정리
RESP, TTL, persistence 같은 개념 구현 초안 생성
테스트 코드 초안 작성
README/발표 정리
하지만 AI 활용에서 한계와 문제도 분명했습니다.

잘된 점
처음 설계를 빠르게 잡을 수 있었다
생소한 Redis 개념을 코드 구조로 바꾸는 데 도움이 됐다
반복적인 테스트 코드/문서 초안 작성 속도가 빨랐다
부족했던 점
AI가 만든 코드가 곧바로 완성품은 아니었다
persistence처럼 “파일은 있지만 실제 흐름에 안 붙은 상태”가 생길 수 있었다
중간중간 사람이 직접 구조 연결 여부를 반드시 검증해야 했다
AI가 잘못된 전제에서 코드를 만들면 겉보기엔 맞아 보여도 실제 통합에서 어긋날 수 있었다
즉, 이번 프로젝트를 통해 알게 된 점은
AI는 구현 속도를 크게 높여주지만, 최종 품질은 사람이 구조를 이해하고 검증할 때 비로소 확보된다는 것입니다.
---
