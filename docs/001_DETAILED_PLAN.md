# Task 001 — Repo scaffold (Detailed Plan)

이 문서는 태스크 001 (repo scaffold + CMake + CI)을 작고 구체적인 작업 단위로 쪼갠 세부 계획입니다. 각 항목은 1–3시간 내 완료 가능한 단위이며, 커밋 메시지와 검증 방법을 포함합니다.

## 목표
- CMake 기반 C++ 학습/개발 스캐폴드 생성
- Python PoC 디렉터리(placeholder) 추가
- GitHub Actions CI: 빌드 + 단위테스트 + clang-tidy
- README, tasks/TODO.md, PR 템플릿 포함

## 전체 예상 소요
- 총: 2–6시간
  - 스캐폴드 + CMake 최소 빌드: 30–60분
  - 간단 토크나이저 C++ 모듈 + 단위테스트: 1–2시간
  - GitHub Actions CI 작성 + 테스트: 30–90분
  - 문서화: 15–30분

---

## 작업 항목 (태스크별)

### 001-01: 브랜치 생성 + 기본 폴더 구조
- 작업 내용
  - 브랜치: feature/001-scaffold 생성
  - 디렉터리 추가:
    - /cpp (C++ 코드)
      - /cpp/src, /cpp/include, /cpp/tests
    - /poc (Python PoC placeholder)
    - .github/workflows/ (CI 파일 위치)
    - tasks/TODO.md
    - README.md (프로젝트 개요)
- 커밋 메시지 예시: chore(scaffold): add repo scaffold and folder structure
- 검증: 폴더가 리포지토리에 존재하는지 확인
- 예상 시간: 15–30분

### 001-02: CMake 최상위 파일(s) 추가
- 작업 내용
  - /CMakeLists.txt (루트)
  - /cpp/CMakeLists.txt — 라이브러리/예제/테스트 타깃 정의
  - /cpp/src/main.cpp — hello-scaffold (빌드 검증용)
- 커밋 메시지: feat(build): add CMakeLists for root and cpp module
- 로컬 검증 방법
  - mkdir build && cd build
  - cmake .. && cmake --build .
  - 실행: ./cpp/bin/hello-scaffold
- 예상 시간: 30–60분

### 001-03: 간단 C++ 모듈 + 유닛테스트
- 작업 내용
  - /cpp/include/tokenizer.h — 공백 토크나이저 API (주석 포함)
  - /cpp/src/tokenizer.cpp — 구현
  - /cpp/tests/test_tokenizer.cpp — 단위 테스트 (3개 케이스)
  - 테스트 프레임워크: Catch2 (FetchContent 사용 권장)
- 커밋 메시지: feat(tokenizer): add simple whitespace tokenizer + unit tests
- 검증
  - 빌드 후 테스트 실행: ctest 또는 ./cpp/tests/test_tokenizer
  - 모든 테스트 통과
- 예상 시간: 60–120분

### 001-04: CI 워크플로(깃허브 액션) 추가
- 작업 내용
  - .github/workflows/ci.yml 생성
  - Workflow 단계
    - Checkout
    - Setup CMake & compiler
    - Build (cmake & cmake --build)
    - Run tests (ctest)
    - Run clang-tidy (옵션)
  - Optional: Python PoC lint/test job 추가
- 커밋 메시지: ci(ci): add GitHub Actions workflow for CMake build + tests + clang-tidy
- 검증: GitHub Actions에서 워크플로 성공 확인
- 예상 시간: 30–90분

### 001-05: PR 템플릿·tasks/TODO.md·README 업데이트
- 작업 내용
  - .github/PULL_REQUEST_TEMPLATE.md 추가
  - tasks/TODO.md에 초기 태스크 목록 추가
  - README.md: 빌드/테스트 가이드 포함
- 커밋 메시지: docs: add PR template, TODO list and README basics
- 검증: README에 적은 빌드 가이드로 로컬 빌드 재현
- 예상 시간: 15–30분

---

## 코드/설정 스니펫 (예)

루트 CMakeLists.txt (요지):

cmake_minimum_required(VERSION 3.16)
project(javi_agent LANGUAGES CXX)
add_subdirectory(cpp)

/cpp/CMakeLists.txt (요지):

add_library(javi_core src/tokenizer.cpp)
add_executable(hello-scaffold src/main.cpp)
target_include_directories(javi_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
add_subdirectory(tests)

간단 tokenizer.h 설명:

// tokenize: split on whitespace
// input: const std::string& s
// output: std::vector<std::string>
std::vector<std::string> tokenize(const std::string& s);

CI 핵심 단계 요약 (ci.yml):
- run: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
- run: cmake --build build --config Release -- -j
- run: ctest --test-dir build --output-on-failure

---

## 커밋/PR 워크플로 권장
- 브랜치: feature/001-scaffold
- 작은 단위로 커밋 후 push
- PR 생성 시 학습 목표·검증법을 명시

---

파일 생성: 자동 생성됨 by javi
