# Development Process & Task Plan

이 문서는 오션과 자비가 합의한 개발 프로세스, 브랜치 규칙, 태스크 템플릿, PR 템플릿, 초기 우선순위 태스크 등을 정리한 학습-개발 계획서입니다. 이 계획에 따라 작은 단위로 작업을 진행하고 각 커밋과 PR을 학습 자료로 삼습니다.

## 원칙
- 작게, 자주, 설명 가득
- 작업 단위: 1–3시간 분량
- 커밋: 태스크 단위로 1커밋(목적·변경 요약·테스트 방법 포함)
- PR: 기능 단위로 PR 생성, 각 PR에 학습 목표·체크리스트 포함

## 브랜치 네이밍
- feature/<번호>-<짧은-설명> (예: feature/001-tokenizer-basic)

## 태스크 템플릿
- 제목: [태스크번호] 한줄요약
- 목표(학습): 무엇을 배울지 1–2문장
- 작업내역(정확히): 파일/함수/테스트 등 변경 예정 항목
- 완료조건(정량): 빌드 통과, 유닛테스트 X개 통과, 벤치 타깃 등
- 커밋 메시지 예시: feat(tokenizer): add whitespace tokenizer + tests — 학습: RAII 메모리 관리

## PR 템플릿
- 학습 목표
- 변경 요약(파일/함수)
- 로컬 검증법(어떻게 실행·테스트할지)
- 체크리스트:
  - [ ] 빌드 통과 (CMake)
  - [ ] 유닛 테스트 통과
  - [ ] 주석/설계 블록 추가됨
  - [ ] 성능 영향 없음(간단 벤치)
- 리뷰 질문(있으면)

## 초기 우선순위 태스크
- 001: repo scaffold + CMake + CI(gha)
- 002: simple tokenizer (C++) + unit tests
- 003: Python PoC: FastAPI minimal RAG flow
- 004: FAISS quickstart (Python) + small dataset
- 005: C++ tokenizer 개선: unicode/utf-8 handling + 주석
- 006: llama.cpp 읽기 & 작은 수정(주석 달기) + 빌드

## 커밋/리뷰 규칙
- 함수 상단에 목적·입력·출력·복잡도·메모리 영향 주석
- 각 모듈에 usage snippet 추가
- 각 PR은 최소 1개 유닛 테스트 포함
- /docs에 “무엇을 배웠나” 한 단락 추가

## 자동화(자비가 생성 예정)
- tasks/TODO.md 초기 백로그 추가
- .github/workflows/ci.yml: CMake 빌드 + 유닛테스트 + clang-tidy
- feature/001-scaffold 브랜치와 PR 초안 생성 (내용: CMake, 기본 폴더 구조, PR 템플릿, tasks/TODO.md)

## 개발 단계(고수준)
1) 1단계 — 초기 PoC (Python)
   - 전부 Python으로 빠르게 구현하여 전체 플로우(텔레그램/웹 → RAG → inference)를 작동시킵니다.
   - 목표: 빠른 실험과 전체 아키텍처 이해.

2) 2단계 — 포트폴리오 정리 (프론트엔드)
   - 웹 프론트엔드/간단 대시보드는 TypeScript로 구현하여 “프로덕션스러운” 데모를 만듭니다.
   - 목표: 사용자 경험과 데모 품질 향상.

3) 3단계 — 성능/학습 심화 (C++)
   - 핵심 모듈(토크나이저/인덱스/추론 인터페이스)을 C++로 재구현하고 주석·학습 자료를 풍부하게 달아 학습과 성능을 동시에 달성합니다.
   - 목표: C++ 심화 학습 및 고성능 컴포넌트 확보.

## 다음 동작 (Choose A/B/C)
A) feature/001-scaffold 브랜치 생성 및 PR 초안 만들기
B) 우선 태스크 우선순위를 재조정
C) 프로세스 수정 요청

---

파일 생성: 자동 생성됨 by javi

## 모델 추론 전략: C++ 유지 결정 및 통합 계획
우리는 모델 추론을 C++로 유지하기로 결정했습니다. 이 결정은 성능(지연, 메모리 제어), 저수준 최적화(배치·SIMD·GPU)와 학습(깊은 C++ 이해)을 모두 얻기 위한 것입니다. 아래는 통합 패턴, 구현 체크리스트, 우선 작업 항목입니다.

통합 패턴(권장)
- 1) 초기(POC): pybind11을 사용한 in-process 바인딩으로 시작합니다. Python에서 C++ inference를 직접 호출하여 개발 속도를 높입니다.
- 2) 운영(스케일 필요 시): C++ inference를 별도의 gRPC/HTTP 서버로 분리해 프로세스 격리와 수평 확장을 지원합니다.
- 3) 런타임 재사용: 가능하면 llama.cpp, ONNX Runtime, TensorRT 같은 검증된 런타임을 활용하고 어댑터를 통해 통합합니다.

주요 체크리스트 (개발·운영)
- API 계약: 입력/출력(토큰 포맷, logits, 메타) 명세화
- 배치 처리: 동적 배치·지연/처리량 목표 설계
- 리소스 제어: 타임아웃, 메모리·스레드 제한 정책
- 안정성: ASan/Valgrind, 스레드 안전성, 예외 경로 테스트
- 관찰성: latency/tokens-per-call/throughput/trace 계측
- 테스트: 단위·통합·부하 테스트
- 배포: Docker 이미지, health/readiness endpoints, 모델 아티팩트 버전 관리

즉시 실행할 작업(우선순위)
- 001-03d (A): pybind11 바인딩 템플릿 추가 (C++ 토크나이저/모델 → Python). 산출물: CMake pybind11 설정, bindings.cpp, 사용 예제.
- 002: Python 쪽 inference adapter 인터페이스 작성(predict API). 산출물: /poc/inference_adapter.py
- 003: 간단 벤치마크 스크립트 작성(대응 latency/throughput 측정). 산출물: bench/inference_bench.py
- 004: CI 통합: C++ 빌드 → pybind11 모듈 빌드 → python 통합 테스트 (.github/workflows/ci.yml)
- 005: (선택) gRPC inference server 스켈레톤 (프로세스 분리 시)

선택지 (어떻게 진행할지)
- A) pybind11 바인딩부터 만들기 (권장 시작). 내가 bindings.cpp/CMake 변경과 파이썬 사용 예까지 작성해 feature 브랜치로 커밋하겠다.
- B) gRPC inference 서버 스켈레톤을 먼저 만들기 (프로덕션 지향).
- C) 우선 adapter 인터페이스와 간단 벤치만 만들고 나중에 바인딩/서버를 연결하기.

원하면 지금 A)로 바로 진행해서 파일·커밋을 만들게. 변경사항은 작은 단위로 나눠 커밋하고 PR로 올리겠다.
