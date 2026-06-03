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

**먼저 `ls papers/`로 기존 테마 폴더를 읽고, 논문마다 가장 적합한 테마를 추천한다:**
- 기존 폴더 중 주제가 잘 맞는 게 있으면 그 폴더를 추천 (💡 추천 테마: X) 폴더명).
- 잘 맞는 기존 폴더가 없으면 새 폴더 이름을 제안 (💡 추천 테마: 🆕 새 폴더 '이름').
  - 새 폴더 이름은 영어 Title Case, 기존 폴더 스타일과 일관되게 (예: "AI Governance").
- 가급적 기존 폴더 재사용을 우선하고, 주제가 정말 다를 때만 새 폴더 제안.
- 추천에는 한 줄 한국어 근거를 붙인다.

다음 형식으로 논문을 보여줘:

```
📚 오늘의 논문 N편 (YYYY-MM-DD)

1️⃣ [9/10] 논문 제목 (Venue Year)
   🎯 배경: ...
   🔬 방법: ...
   📊 결과: ...
   💡 결론: ...
   🔗 연구 연관성: ...
   💡 추천 테마: A) Human-AI Collaboration — 근거 한 줄

2️⃣ [8/10] ...
   💡 추천 테마: 🆕 새 폴더 'AI Governance' — 근거 한 줄

────────────────

📂 저장 가능한 폴더:
 A) Human-AI Collaboration
 B) Public Benefits
 C) Participatory Design
 ...
 N) 새 폴더 만들기

✅ 추천대로 전부 저장하려면: ok
또는 직접 지정:
예: 1,3 → A
예: 2 → N:새폴더이름
```

**폴더 목록은 `papers/` 디렉토리의 실제 하위 폴더를 읽어서 동적으로 생성.**

논문이 없으면: "📭 오늘은 관련 논문이 없습니다."

## Step 4: 사용자 선택 처리

- 사용자가 **`ok` / `ㅇㅇ` / `추천대로`** 라고 답하면 → 각 논문을 Step 3에서 **추천한 테마**(기존 폴더 또는 제안한 새 폴더)에 그대로 저장.
- 사용자가 직접 지정하면 (예: `1,3 → A, 2 → N:Benefits Navigation`) → 지정대로 저장.

### 사용자 thoughts → 태그 자동 생성

사용자가 논문에 대한 **생각(thoughts)**을 함께 남기면 (예: `1 → A | 신뢰 보정에 유용`, 또는 `1: 이건 COMPASS에 적용 가능` 같은 별도 줄):

1. 그 생각을 노트 frontmatter `thoughts:` 와 본문 `## 🧠 내 생각` 에 **그대로 저장**.
2. 그 생각 + 논문 내용을 바탕으로 **태그 2~5개를 직접 생성**한다 (소문자, 하이픈, 한/영 가능. 예: trust-calibration, eu-ai-act, 취약계층).
3. 생성한 태그를 `thought_tags:` 에 넣고, 같은 태그를 `tags:` 목록에도 병합(중복 제거).
4. 생각이 없는 논문은 `thoughts: ""`, `thought_tags: []` 로 저장 (Telegram 경로에서 나중에 enrich-thought-tags 워크플로우가 채움).

저장 절차:

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
category: 카테고리
tags: [paper, 카테고리, 생성태그1, 생성태그2]
thoughts: "사용자가 남긴 생각 (없으면 빈 문자열)"
thought_tags: [생성태그1, 생성태그2]
status: unread
---

> `category`는 독립 속성으로 반드시 포함 (Obsidian Bases `papers.base` 그룹핑에 사용).
> 값은 Step 2 카테고리 enum 중 하나: human_ai_collab | public_benefits_tech | low_income_populations | participatory_design | algorithmic_fairness | llm_applications | ai_general
> `thoughts`/`thought_tags`는 Step 4의 "thoughts → 태그" 규칙대로 채움 (생각 없으면 `""` / `[]`).

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

## 🧠 내 생각
사용자가 남긴 생각 (없으면 비움)

---
## 메모

```

### 커밋 메시지 형식

```
papers: add N papers to <폴더명> (YYYY-MM-DD)
```
