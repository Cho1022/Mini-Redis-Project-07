# Flask Test Summary

이 폴더는 MongoDB, Redis, Mini Redis 프로젝트의 `SET`, `GET` 성능을 비교하기 위한 테스트용 코드 모음이다.

## 현재 목적

- 순수 DB 호출 기준으로 성능 비교
- 비교 대상:
  - MongoDB
  - Redis
  - Mini Redis Project
- 비교 항목:
  - `SET`
  - `GET`

## 주요 파일

- `compare.html`
  - 브라우저에서 보는 비교 화면
  - `SET`, `GET` 평균 시간을 막대 그래프로 표시
- `benchmark_api.py`
  - Flask API 서버
  - `/db-benchmark` 엔드포인트로 벤치마크 결과를 JSON으로 반환
- `db_benchmark.py`
  - 실제 벤치마크 로직
  - MongoDB, Redis, Mini Redis를 직접 호출해서 시간 측정
- `compare_test_file.py`
  - MongoDB 테스트용 Flask 서버
- `redis_test_server.py`
  - Redis 테스트용 Flask 서버

## 현재 비교 방식

- HTTP 비교는 제외하고, 순수 DB 성능 비교 중심으로 정리함
- `warmup` 횟수만큼 먼저 실행하고 결과에는 포함하지 않음
- 이후 `count` 횟수만큼 실제 측정해서 평균 시간 사용

## 실행 방법

### 1. MongoDB 실행

- 로컬 MongoDB 서버가 켜져 있어야 함

### 2. Redis 실행

- 기본 포트는 `6379`
- 현재 환경에서는 일반 Redis가 실행되지 않아 연결 거부(`10061`)가 발생할 수 있었음

### 3. Mini Redis 실행

예상 실행 예시:

```bash
python -m src.main --port 6380
```

### 4. 벤치마크 API 실행

```bash
python benchmark_api.py
```

### 5. 화면 열기

- `compare.html`을 브라우저에서 열기
- 반복 횟수, 워밍업 횟수, Redis 포트, Mini Redis 포트를 입력 후 실행

## 기본 포트

- `benchmark_api.py`: `5003`
- Redis: `6379`
- Mini Redis: `6380`

## 자주 나온 이슈

### 1. `redis.py` 이름 충돌

- 파일명이 라이브러리 `redis`와 충돌해서 import 오류가 발생했음
- 그래서 `redis_test_server.py`로 이름 변경

### 2. `wrong number of arguments for 'del' command`

- cleanup 로직에서 Redis `DEL` 처리 방식 때문에 발생
- 테스트 키를 하나씩 지우는 방식으로 변경

### 3. `unknown command 'SCAN'`

- 사용 중인 Redis 환경이 `SCAN`을 지원하지 않았음
- `SCAN` 의존성을 제거하고 직접 키를 순회하도록 수정

### 4. `Error 10061 connecting to 127.0.0.1:6379`

- 일반 Redis 서버가 현재 떠 있지 않다는 뜻
- Redis 설치 또는 실행 상태 확인 필요

### 5. `__pycache__` 권한 문제

- 새 경로에서 `py_compile` 시도 시 `.pyc` 쓰기 권한 오류가 있었음
- 코드 자체 문제라기보다 폴더 권한 문제로 보임

## 참고

- 현재 코드에는 예전 절대경로 하드코딩은 남아 있지 않음
- 따라서 폴더를 옮겨도 기본 동작 구조는 유지됨
