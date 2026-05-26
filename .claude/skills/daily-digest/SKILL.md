---
name: daily-digest
description: 매일 아침 HCI/AI 관련 최신 논문을 수집하고 요약하여 사용자에게 보여주고, 선택한 논문을 Obsidian vault(papers/ 디렉토리)에 저장하는 루틴. 논문 수집, paper digest, 아침 논문 등의 요청에 자동 활성화.
---

# Daily Paper Digest Routine

## Step 1: 논문 수집

```bash
python3 collect_papers.py
```

수집된 논문은 `staging/latest.json`에 저장됩니다.

## Step 2: 논문 요약 (네가 직접 수행)

`staging/latest.json`을 읽고, 각 논문에 대해 다음을 직접 평가:

- **관련성 점수** (1-10): 아래 연구자 컨텍스트 기준
- **한국어 4-section 요약**:
  - 🎯 배경/목적: 무엇을, 왜 연구했는가 (1-2문장)
  - 🔬 방법: 연구 방법, 대상, 접근 방식 (1-2문장)
  - 📊 결과: 핵심 발견과 수치 (1-2문장)
  - 💡 결론: 결과의 의미, 향후 방향 (1-2문장)
- **연구 연관성** (영어 1문장): 아래 연구와 어떻게 연결되는지
- **카테고리**: human_ai_collab | public_benefits_tech | low_income_populations | participatory_design | algorithmic_fairness | llm_applications | ai_general

### 연구자 컨텍스트

Notre Dame 대학교 HCI 포스닥 연구자:
1. AI의 사회적 영향 — 취약 계층이 공공 혜택/커뮤니티 서비스에 접근하는 과정
2. Human-AI 파트너십 — 커뮤니티 사회 서비스 조직에서 (NSF SCC-PG, CNS-2331007)
3. 참여적 디자인 — 비기술 이해관계자와 함께 ("vibe coding")
4. LLM 기반 공공 혜택 내비게이션 시스템
5. 알고리즘적 돌봄과 신뢰-부담 역학
6. COMPASS 다중 에이전트 AI 시스템

주요 학회: CHI, CSCW, FAccT, GROUP

**관련성 6점 이상인 논문만 포함. 높은 순서로 정렬.**

## Step 3: 결과 제시

다음 형식으로 논문을 보여줘:

```
📚 오늘의 논문 N편 (YYYY-MM-DD)

1️⃣ [9/10] 논문 제목 (Venue Year)
   🎯 배경: ...
   🔬 방법: ...
   📊 결과: ...
   💡 결론: ...
   🔗 연구 연관성: ...

2️⃣ [8/10] ...

────────────────

📂 저장 가능한 폴더:
 A) Human-AI Collaboration
 B) Public Benefits
 C) Participatory Design
 ...
 N) 새 폴더 만들기

저장할 논문과 폴더를 알려주세요!
예: 1,3 → A
예: 2 → N:새폴더이름
```

**폴더 목록은 `papers/` 디렉토리의 실제 하위 폴더를 읽어서 동적으로 생성.**

논문이 없으면: "📭 오늘은 관련 논문이 없습니다."

## Step 4: 사용자 선택 처리

사용자가 답장하면 (예: `1,3 → A, 2 → N:Benefits Navigation`):

1. 선택된 논문별로 마크다운 파일 생성
2. `papers/<폴더명>/` 디렉토리에 저장
3. 새 폴더면 디렉토리 먼저 생성
4. `git add`, `git commit`, `git push`

### 마크다운 템플릿

파일명: `papers/<폴더명>/<slugified-title>.md`

```markdown
---
title: "논문 제목"
authors: "Author1, Author2 et al."
url: "https://..."
venue: "CHI"
relevance: 9
date: YYYY-MM-DD
tags: [paper, 카테고리]
status: unread
---

# 논문 제목

**저자:** Author1, Author2 et al.
**발표:** Venue (날짜)
**링크:** [논문](url) | [PDF](pdf_url)

## 🎯 배경/목적
요약 내용

## 🔬 방법
요약 내용

## 📊 결과
요약 내용

## 💡 결론
요약 내용

## 🔗 연구 연관성
영어 연관성 설명

---
## 메모

```

### 커밋 메시지 형식

```
papers: add N papers to <폴더명> (YYYY-MM-DD)
```
