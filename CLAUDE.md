# Daily Paper Digest

HCI/AI 연구 논문을 매일 자동 수집하여 요약하고 Telegram으로 알림을 보내는 시스템.

## 실행 방법

```bash
python daily_digest.py
```

외부 패키지 설치 불필요 — 모든 핵심 기능이 Python 표준 라이브러리(urllib, json, xml)로 구현되어 있음.

## 아키텍처

- `daily_digest.py` — 메인 파이프라인 (수집 → 요약 → 저장 → 알림)
- `collectors/arxiv_collector.py` — arXiv API에서 키워드 기반 논문 수집
- `collectors/semantic_scholar.py` — Semantic Scholar API에서 논문 검색
- `summarizer.py` — Claude API로 관련성 스코어링 + 한국어 4-section 요약
- `delivery/telegram_sender.py` — Telegram Bot API로 다이제스트 전송
- `delivery/obsidian_md.py` — Obsidian vault에 마크다운 논문 노트 생성
- `config.py` — 연구 키워드, API 설정, 경로 등 (`.env`에서 자동 로드)

## 환경변수

`.env` 파일에 설정 (자동 로드됨):
- `ANTHROPIC_API_KEY` — Claude API 요약에 필요 (필수)
- `TELEGRAM_BOT_TOKEN` — Telegram 알림 전송 (필수)
- `TELEGRAM_CHAT_ID` — 알림 받을 채팅 ID (필수)
- `S2_API_KEY` — Semantic Scholar API (선택, 없어도 동작)

## 연구 컨텍스트

Notre Dame 대학교 HCI 포스닥 연구자의 관심 분야:
- AI의 사회적 영향 (취약 계층, 공공 혜택 시스템)
- Human-AI 파트너십 (커뮤니티 서비스 조직)
- 참여적 디자인 (비기술 이해관계자)
- LLM 기반 공공 혜택 내비게이션
- 알고리즘적 돌봄과 신뢰-부담 역학
