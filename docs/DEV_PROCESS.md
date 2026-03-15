# Development Process & Task Plan

이 문서는 오션과 자비가 합의한 개발 프로세스, 브랜치 규칙, 태스크 템플릿, PR 템플릿, 초기 우선순위 태스크 등을 정리한 학습-개발 계획서입니다. 이 계획에 따라 작은 단위로 작업을 진행하고 각 커밋과 PR을 학습 자료로 삼습니다.

**아키텍처**: Hybrid Graph + DAG Runtime (DAG execution + State Management + Recovery)

## 원칙
- 작게, 자주, 설명 가득
- 작업 단위: 1–3시간 분량
- 커밋: 태스크 단위로 1커밋(목적·변경 요약·테스트 방법 포함)
- PR: 기능 단위로 PR 생성, 각 PR에 학습 목표·체크리스트 포함

## 브랜치 네이밍
- feature/<번호>-<짧은-설명> (예: feature/001-state-manager)

## 태스크 템플릿
- 제목: [태스크번호] 한줄요약
- 목표(학습): 무엇을 배울지 1–2문장
- 작업내역(정확히): 파일/함수/테스트 등 변경 예정 항목
- 완료조건(정량): 빌드 통과, 유닛테스트 X개 통과, 벤치 타깃 등
- 커밋 메시지 예시: feat(state): add state manager with Redis backend — 학습: 비동기 상태 저장소

## PR 템플릿
- 학습 목표
- 변경 요약(파일/함수)
- 로컬 검증법(어떻게 실행·테스트할지)
- 체크리스트:
  - [ ] 빌드 통과 (CMake/Python)
  - [ ] 유닛 테스트 통과
  - [ ] 주석/설계 블록 추가됨
  - [ ] 성능 영향 없음(간단 벤치)
  - [ ] 상태 복구 테스트 통과 (State Manager 관련)
- 리뷰 질문(있으면)

---

## 개발 단계 (Phase 0 ~ 3)

### Phase 0: State Manager & Recovery (기반)
- State Manager 인터페이스 및 구현
- Retry/Recovery 로직
- Tool Adapter contract 확장

### Phase 1: DAG Engine (실행)
- Plan validation (JSON Schema)
- Topological execution
- State integration with DAG Engine

### Phase 2: Tools (기능)
- Mock tools (search, summarize)
- C++ tokenizer
- Python inference adapter

### Phase 3: Production (배포)
- Redis backend for State Manager
- CI/CD integration
- Monitoring & logging

---

## 초기 우선순위 태스크 (Phase 0 ~ 1)

### Phase 0: State Manager & Recovery

**001: State Manager 인터페이스 및 구현**
- 목표: 비동기 상태 저장소 인터페이스 이해
- 작업내역:
  - `/poc/state_manager.py` - StateManager 클래스 (save/get/delete)
  - Memory backend 구현 (dict 기반)
  - Redis backend 스켈레톤
- 완료조건:
  - 유닛테스트 3개 이상 통과
  - TTL 동작 확인

**002: Retry 로직 및 복구 정책**
- 목표: 지수 백오프 및 재시도 로직 이해
- 작업내역:
  - `/poc/recovery.py` - Retry 로직
  - Recovery strategy (retry/cache/manual)
  - Backoff 계산 (fixed/exponential)
- 완료조건:
  - 유닛테스트 5개 이상 통과
  - 지수 백오프 검증

**003: Tool Adapter contract 확장 (State)**
- 목표: Tool 입출력에 state 필드 추가
- 작업내역:
  - Tool Output에 state 필드 추가
  - State Manager와 Tool Adapter 통합
  - 에러 핸들링 (retryable flag)
- 완료조건:
  - 예제 tool 구현 및 테스트

### Phase 1: DAG Engine

**004: Plan validation (JSON Schema)**
- 목표: JSON Schema 검증 이해
- 작업내역:
  - `/poc/utils/validator.py` - Plan/Step 검증
  - JSON Schema 정의
  - 의존성 순환 체크
- 완료조건:
  - 유효/무효 플랜 검증 테스트

**005: DAG Engine core (Topological Execution)**
- 목표: 위상 정렬 및 DAG 이해
- 작업내역:
  - `/poc/dag_engine.py` - DAG Engine 클래스
  - 위상 정렬 알고리즘
  - 의존성 해결
- 완료조건:
  - 유닛테스트 5개 이상 통과
  - 순차/병렬 실행 검증

**006: DAG Engine + State Manager 통합**
- 목표: DAG 실행 시 상태 저장 이해
- 작업내역:
  - Step 실행 후 상태 저장
  - 실패 시 복구 로직 연결
  - State cleanup
- 완료조건:
  - End-to-end 테스트 통과

### Phase 2: Tools

**007: Mock tools (search, summarize)**
- 목표: Tool contract 구현 연습
- 작업내역:
  - `/poc/tools/mock_search.py`
  - `/poc/tools/mock_summarize.py`
  - State 반환 구현
- 완료조건:
  - 유닛테스트 각 3개 이상

**008: C++ tokenizer + Python binding**
- 목표: pybind11 바인딩 이해
- 작업내역:
  - `/cpp/src/tokenizer.cpp` (기존)
  - `/cpp/bindings/bindings.cpp`
  - CMake pybind11 설정
- 완료조건:
  - Python에서 C++ tokenizer 호출 테스트

**009: Python inference adapter**
- 목표: inference 인터페이스 설계 이해
- 작업내역:
  - `/poc/inference_adapter.py`
  - predict API
  - State 저장 통합
- 완료조건:
  - 예제 플랜 실행 및 응답

### Phase 3: Production (선택적)

**010: Redis backend for State Manager**
- 목표: 분산 상태 저장소 이해
- 작업내역:
  - Redis backend 구현
  - Connection pooling
  - TTL 설정
- 완료조건:
  - 통합 테스트 통과

**011: CI/CD integration**
- 목표: CI/CD 파이프라인 이해
- 작업내역:
  - `.github/workflows/ci.yml`
  - 테스트 자동화
  - 빌드 확인
- 완료조건:
  - PR에서 CI 통과

**012: Monitoring & Logging**
- 목표: 로깅 구조화 및 메트릭 이해
- 작업내역:
  - Structured logging
  - Metrics collection (latency, throughput)
  - Health checks
- 완료조건:
  - 로그/메트릭 시각화

---

## 커밋/리뷰 규칙
- 함수 상단에 목적·입력·출력·복잡도·메모리 영향 주석
- 각 모듈에 usage snippet 추가
- 각 PR은 최소 1개 유닛 테스트 포함
- State Manager 관련: 상태 복구 테스트 필수
- /docs에 "무엇을 배웠나" 한 단락 추가

---

## 자동화(자비가 생성 예정)
- tasks/TODO.md 초기 백로그 추가
- .github/workflows/ci.yml: Python 빌드 + 테스트 + State Manager 테스트
- feature/001-hybrid-runtime 브랜치와 PR 초안 생성 (내용: State Manager, Recovery, POC_SPEC.md, DEV_PROCESS.md)

---

## 하이브리드 런타임 아키텍처 요약

```
Runtime → Planner → DAG Engine → State Manager → Tool Adapters → Tools
                                    ↓
                              (Redis/DB)
```

**핵심 특징:**
- **DAG for Execution**: 위상 정렬, 순차/병렬 실행
- **State for Resilience**: 각 스텝 상태 저장
- **Recovery for Fault Tolerance**: 자동 재시도/캐시 재사용
- **Simple yet Production-Ready**: 단순하지만 프로덕션 준비

---

## 다음 동작

**A) feature/001-hybrid-runtime 브랜치 PR 생성** ← 현재 작업 중
- POC_SPEC.md (하이브리드 스펙)
- DEV_PROCESS.md (Phase 0 ~ 3 태스크 정의)
- 커밋 메시지: docs(spec): update POC spec for hybrid Graph + DAG runtime with state management

**B) 다음 태스크 001부터 구현 시작**
- State Manager 인터페이스 및 구현

**C) 프로세스 수정 요청**

---

## 모델 추론 전략: C++ 유지 결정 및 통합 계획
우리는 모델 추론을 C++로 유지하기로 결정했습니다. 이 결정은 성능(지연, 메모리 제어), 저수준 최적화(배치·SIMD·GPU)와 학습(깊은 C++ 이해)을 모두 얻기 위한 것입니다.

통합 패턴(권장)
- 1) 초기(POC): pybind11을 사용한 in-process 바인딩으로 시작합니다. Python에서 C++ inference를 직접 호출하여 개발 속도를 높입니다.
- 2) 운영(스케일 필요 시): C++ inference를 별도의 gRPC/HTTP 서버로 분리해 프로세스 격리와 수평 확장을 지원합니다.
- 3) 런타임 재사용: 가능하면 llama.cpp, ONNX Runtime, TensorRT 같은 검증된 런타임을 활용하고 어댑터를 통해 통합합니다.

---

파일 생성: 자동 생성됨 by javi

**마지막 업데이트**: 2026-03-15 - 하이브리드 Graph + DAG 런타임으로 아키텍처 재정의
