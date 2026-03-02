# 📚 Daily Paper Digest

매일 아침 AI/HCI 논문을 자동으로 수집·요약하여 Obsidian vault에 저장하고 Telegram으로 핸드폰에 알려줍니다.

## 구조

```
arXiv API ──┐
            ├── Claude API 요약 ──┬── Obsidian vault (iCloud 동기화)
S2 API ─────┘                    └── Telegram 알림 → 📱
```

## 빠른 시작 (10분)

### 1. API 키 준비

| 서비스 | 발급 URL | 비용 |
|--------|----------|------|
| Anthropic API | https://console.anthropic.com | ~$3-5/월 |
| Telegram Bot | Telegram에서 @BotFather에게 `/newbot` | 무료 |
| Semantic Scholar | https://www.semanticscholar.org/product/api | 무료 |

**Telegram Chat ID 찾기:**
1. @BotFather에서 봇 생성 후 토큰 저장
2. 봇에게 아무 메시지 전송
3. 브라우저에서: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. 응답에서 `"chat":{"id": 123456789}` 확인

### 2. GitHub에 배포

```bash
# repo 생성 & push
git init
git add .
git commit -m "Initial: daily paper digest"
gh repo create daily-paper-digest --private --push
```

### 3. GitHub Secrets 등록

GitHub repo → Settings → Secrets and variables → Actions → New repository secret:

```
ANTHROPIC_API_KEY   → sk-ant-...
TELEGRAM_BOT_TOKEN  → 7123456789:AAF...
TELEGRAM_CHAT_ID    → 123456789
S2_API_KEY          → (Semantic Scholar에서 발급)
```

### 4. 테스트 실행

GitHub → Actions 탭 → "Daily Paper Digest" → "Run workflow" 클릭

### 5. 끝!

이제 매일 평일 아침 7시(EST)에 자동으로 실행됩니다.

---

## 로컬 실행 (Mac + iCloud + Obsidian)

로컬에서 실행하면 iCloud를 통해 Obsidian vault에 직접 저장됩니다.

```bash
# 환경변수 설정
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="7123456789:AAF..."
export TELEGRAM_CHAT_ID="123456789"
export S2_API_KEY="..."

# 실행
python daily_digest.py
```

**iCloud Obsidian vault 경로 (자동 감지):**
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/daily-papers/
```

`config.py`에서 `OBSIDIAN_VAULT_NAME`을 본인 vault 이름으로 변경하세요.

### cron으로 매일 실행 (Mac)

```bash
crontab -e
```

추가:
```
0 7 * * 1-5 cd /path/to/daily-paper-digest && /usr/bin/python3 daily_digest.py >> /tmp/paper-digest.log 2>&1
```

---

## 설정 커스터마이징

`config.py`에서 수정:

- **ARXIV_KEYWORDS**: 검색 키워드 추가/수정
- **SEMANTIC_SCHOLAR_QUERIES**: 학술 검색 쿼리
- **ARXIV_CATEGORIES**: arXiv 카테고리 (cs.HC, cs.AI 등)
- **MIN_RELEVANCE_SCORE**: 최소 관련성 점수 (기본 6)
- **DAYS_LOOKBACK**: 며칠 전까지 검색 (기본 2)
- **OBSIDIAN_VAULT_NAME**: Obsidian vault 이름
- **RESEARCH_CONTEXT**: Claude에게 전달하는 연구 맥락

---

## Obsidian vault 구조

실행 후 자동 생성되는 파일:

```
daily-papers/
├── 2026-03-02/
│   ├── digest-2026-03-02.md          ← 일간 다이제스트
│   ├── paper-llm-public-benefits.md  ← 관련성 8+ 개별 노트
│   └── paper-participatory-ai.md
├── 2026-03-03/
│   └── digest-2026-03-03.md
└── ...
```

### Dataview 연동 (선택)

Obsidian Dataview 플러그인을 설치하면 자동 테이블 생성 가능:

```markdown
## 이번 주 관련성 높은 논문

```​dataview
TABLE relevance, venue, summary_ko
FROM "daily-papers"
WHERE relevance >= 8 AND date >= date(today) - dur(7 days)
SORT relevance DESC
```​
```

---

## 비용

| 항목 | 비용 |
|------|------|
| arXiv API | 무료 |
| Semantic Scholar API | 무료 |
| Claude Sonnet (요약) | ~$0.10/일 |
| Telegram | 무료 |
| GitHub Actions | 무료 (2,000분/월) |
| **월 합계** | **~$3** |

---

## 향후 확장

- [ ] Post Webhook으로 Obsidian에서 심화분석 트리거
- [ ] 주간 종합 리포트 자동 생성
- [ ] NotebookLM / Open-Notebook 팟캐스트 연동
- [ ] 본인 논문 인용 추적
- [ ] Conference deadline 알림
