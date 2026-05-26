# Daily Paper Digest

HCI/AI 연구 논문을 매일 자동 수집하여 요약하고, 사용자가 선택한 논문을 Obsidian vault에 저장하는 시스템.

## 핵심 실행 방법

```bash
# 논문 수집 (요약 없이 수집만)
python3 collect_papers.py

# 수집 결과 확인
cat staging/latest.json
```

## 디렉토리 구조

- `collect_papers.py` — **논문 수집 전용** (Routine에서 사용)
- `collectors/arxiv_collector.py` — arXiv API 수집
- `collectors/semantic_scholar.py` — Semantic Scholar API 수집
- `papers/` — **Obsidian vault 연동 폴더** (테마별 하위 폴더)
- `staging/latest.json` — 수집된 원본 논문 (임시)
- `config.py` — 연구 키워드, API 설정 (`.env`에서 자동 로드)
- `daily_digest.py` — 레거시 전체 파이프라인 (GitHub Actions용)
- `summarizer.py` — 레거시 Claude API 요약 (Routine에서는 미사용)

## 환경변수

`.env` 파일에 설정 (자동 로드됨):
- `ANTHROPIC_API_KEY` — 레거시용 (Routine에서는 미사용)
- `TELEGRAM_BOT_TOKEN` — Telegram bot용
- `TELEGRAM_CHAT_ID` — Telegram 채팅 ID
- `S2_API_KEY` — Semantic Scholar API (선택)

## Routine 워크플로우

1. `python3 collect_papers.py` 실행 → `staging/latest.json` 생성
2. Claude가 직접 논문 요약 및 관련성 평가
3. 사용자에게 번호 목록 + 테마 폴더 목록 제시
4. 사용자 선택 → `papers/<테마>/` 에 마크다운 저장 → git commit + push

자세한 Routine 행동 지침: `.claude/skills/daily-digest/SKILL.md`
