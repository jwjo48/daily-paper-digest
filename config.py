"""
Configuration for Daily Paper Digest
연구 키워드, API 설정, 경로 등을 여기서 관리합니다.
"""

import os
from pathlib import Path

# .env 파일에서 환경변수 자동 로드 (Claude Code Routine 등 fresh 환경 지원)
from load_env import load_dotenv
load_dotenv()

# ============================================================
# API Keys (GitHub Secrets 또는 환경변수에서 로드)
# ============================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
S2_API_KEY = os.environ.get("S2_API_KEY", "")  # Semantic Scholar

# ============================================================
# 연구 키워드 & 카테고리 (본인 연구에 맞게 수정)
# ============================================================
ARXIV_CATEGORIES = ["cs.HC", "cs.AI", "cs.CY", "cs.SI"]

ARXIV_KEYWORDS = [
    "human-computer interaction",
    "public benefits",
    "participatory design",
    "vulnerable populations",
    "algorithmic fairness",
    "social services",
    "human-AI partnership",
    "AI ethics",
    "community organizations",
    "LLM social",
    "trust AI systems",
]

SEMANTIC_SCHOLAR_QUERIES = [
    "human-AI partnership public benefits",
    "participatory design AI vulnerable populations",
    "LLM social services community organizations",
    "algorithmic care public benefits system",
    "AI ethics community social services",
    "scenario-based design HCI",
    "trust burden AI assisted systems",
]

# Semantic Scholar venue 필터 (관심 학회)
TARGET_VENUES = [
    "CHI", "CSCW", "FAccT", "GROUP", "DIS",
    "ASSETS", "NeurIPS", "AAAI", "ICML",
    "ACM Conference on Fairness",
]

# ============================================================
# Claude API 설정
# ============================================================
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"   # daily digest + bot summarization
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"       # bot topic parsing (cheap)
MAX_PAPERS_TO_SUMMARIZE = 5
MIN_RELEVANCE_SCORE = 6  # 이 점수 이상만 포함

RESEARCH_CONTEXT = """You are a research assistant for a postdoctoral HCI researcher at the University of Notre Dame. Their research focuses on:

1. AI's societal impacts on vulnerable populations accessing public benefits and community services
2. Human-AI partnerships in community social service organizations (NSF SCC-PG, CNS-2331007)
3. Participatory design with non-technical stakeholders ("vibe coding")
4. LLM-assisted public benefits navigation systems
5. Algorithmic care and trust-burden dynamics
6. The COMPASS multi-agent AI system for community services

The researcher publishes at CHI, CSCW, FAccT, and GROUP.

For each paper, provide a JSON object with:
- "relevance": integer 1-10
- "background": Korean — 연구 배경 및 목적. 무엇을, 왜 연구했는가? (1-2 sentences)
- "methods": Korean — 연구 방법. 연구 대상, 접근 방식, 실험 방법 등 (1-2 sentences)
- "results": Korean — 연구 결과. 핵심 발견과 수치 위주 (1-2 sentences)
- "conclusion": Korean — 결론 및 의의. 결과의 의미, 향후 방향, 최종 메시지 (1-2 sentences)
- "connection": How this connects to the researcher's work (1 sentence, English ok)
- "category": one of ["human_ai_collab", "public_benefits_tech", "low_income_populations", "participatory_design", "algorithmic_fairness", "llm_applications", "ai_general"]
  - "human_ai_collab": Human-AI partnership, trust dynamics, AI-assisted collaboration
  - "public_benefits_tech": AI/tech in social services, benefits navigation systems
  - "low_income_populations": AI impacts on low-income or poverty-affected groups, economic equity
  - "participatory_design": Co-design, stakeholder involvement, design with non-technical users
  - "algorithmic_fairness": Bias, fairness, accountability, algorithmic decision-making
  - "llm_applications": LLM-based systems, prompting, real-world LLM deployments
  - "ai_general": Other AI/ML papers not fitting above

CRITICAL: Respond ONLY with a valid JSON array. No markdown fences, no preamble."""

# ============================================================
# Obsidian / iCloud 설정
# ============================================================
# iCloud에서 Obsidian vault 경로 (Mac 기준)
# ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/VaultName/
OBSIDIAN_VAULT_NAME = "Obsidian"  # 본인 vault 이름으로 변경
ICLOUD_OBSIDIAN_BASE = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents"
OBSIDIAN_VAULT_PATH = ICLOUD_OBSIDIAN_BASE / OBSIDIAN_VAULT_NAME
PAPERS_FOLDER = "daily-papers"  # vault 안의 폴더 이름

# GitHub Actions에서 실행 시 로컬 경로 사용
IS_CI = os.environ.get("CI", "false").lower() == "true"
if IS_CI:
    OUTPUT_DIR = Path("/tmp/daily-papers")
else:
    OUTPUT_DIR = OBSIDIAN_VAULT_PATH / PAPERS_FOLDER

# ============================================================
# 기타 설정
# ============================================================
DAYS_LOOKBACK = 2  # 며칠 전 논문까지 검색할지
MAX_TELEGRAM_LENGTH = 4000  # Telegram 메시지 최대 길이
