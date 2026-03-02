"""
Configuration for Daily Paper Digest
연구 키워드, API 설정, 경로 등을 여기서 관리합니다.
"""

import os
from pathlib import Path

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
    "scenario-based design",
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
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_PAPERS_TO_SUMMARIZE = 20
MIN_RELEVANCE_SCORE = 6  # 이 점수 이상만 포함

RESEARCH_CONTEXT = """You are a research assistant for a postdoctoral HCI researcher at the University of Notre Dame. Their research focuses on:

1. AI's societal impacts on vulnerable populations accessing public benefits and community services
2. Human-AI partnerships in community social service organizations (NSF SCC-PG, CNS-2331007)
3. Participatory design with non-technical stakeholders ("vibe coding")
4. LLM-assisted public benefits navigation systems
5. Algorithmic care and trust-burden dynamics
6. Scenario-Based Design methods in HCI
7. The COMPASS multi-agent AI system for community services

The researcher publishes at CHI, CSCW, FAccT, and GROUP.

For each paper, provide a JSON object with:
- "relevance": integer 1-10
- "summary_ko": Korean summary (2-3 sentences)
- "summary_en": English summary (2-3 sentences)  
- "connection": How this connects to the researcher's work (1-2 sentences)
- "category": one of ["core_hci", "ai_fairness", "public_benefits", "participatory_design", "methodology", "ai_general"]

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
