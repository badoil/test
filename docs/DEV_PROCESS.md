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

## 다음 동작 (Choose A/B/C)
A) feature/001-scaffold 브랜치 생성 및 PR 초안 만들기
B) 우선 태스크 우선순위를 재조정
C) 프로세스 수정 요청

---

파일 생성: 자동 생성됨 by javi
