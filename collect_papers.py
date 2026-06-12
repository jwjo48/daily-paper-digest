#!/usr/bin/env python3
"""
collect_papers.py — 논문 수집만 수행 (요약 없음)

Claude Code Routine에서 사용:
1. arXiv + Semantic Scholar에서 논문 수집
2. 중복 제거
3. staging/latest.json에 저장

요약은 Claude Code가 직접 수행 (Max plan 내 처리, API 비용 0).
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from collectors.arxiv_collector import fetch_arxiv_papers
from collectors.semantic_scholar import fetch_semantic_scholar_papers

PAPERS_DIR = Path(__file__).parent / "papers"


def _norm_title(title: str) -> str:
    """제목 정규화: 소문자 + 영숫자만 (구두점/공백 차이 무시)"""
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def _norm_url(url: str) -> str:
    """URL 정규화: arXiv는 ID(버전 제외)로, 그 외는 소문자/끝슬래시 제거"""
    if not url:
        return ""
    url = url.strip().lower()
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url)
    if m:
        return f"arxiv:{m.group(1)}"
    return url.rstrip("/")


def deduplicate(papers: list[dict]) -> list[dict]:
    """제목 기반 중복 제거 (수집 배치 내부)"""
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].lower().strip().replace(" ", "")
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def load_archived_keys() -> tuple[set, set]:
    """papers/ 보관함의 모든 노트 frontmatter에서 title/url 키 집합을 수집"""
    titles, urls = set(), set()
    if not PAPERS_DIR.exists():
        return titles, urls
    for md in PAPERS_DIR.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        frontmatter = text[3:end] if end != -1 else text
        for line in frontmatter.splitlines():
            stripped = line.strip()
            if stripped.startswith("title:"):
                val = stripped[len("title:"):].strip().strip('"').strip("'")
                if val:
                    titles.add(_norm_title(val))
            elif stripped.startswith("url:"):
                val = stripped[len("url:"):].strip().strip('"').strip("'")
                if val:
                    urls.add(_norm_url(val))
    return titles, urls


def filter_archived(papers: list[dict]) -> list[dict]:
    """이미 papers/ 에 저장된 논문(제목 또는 URL 일치)을 제외"""
    archived_titles, archived_urls = load_archived_keys()
    if not archived_titles and not archived_urls:
        return papers
    kept = []
    for p in papers:
        nt = _norm_title(p.get("title", ""))
        nu = _norm_url(p.get("url", ""))
        if nt and nt in archived_titles:
            continue
        if nu and nu in archived_urls:
            continue
        kept.append(p)
    return kept


def main():
    print(f"📚 논문 수집 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 수집
    arxiv_papers = fetch_arxiv_papers()
    s2_papers = fetch_semantic_scholar_papers()

    # 중복 제거 (수집 배치 내부)
    all_papers = deduplicate(arxiv_papers + s2_papers)
    print(f"📊 총 {len(all_papers)}편 (arXiv: {len(arxiv_papers)}, S2: {len(s2_papers)})")

    # 보관함 대조 — 이미 papers/ 에 저장된 논문 제외
    before = len(all_papers)
    all_papers = filter_archived(all_papers)
    removed = before - len(all_papers)
    if removed:
        print(f"🗂️  보관함 중복 {removed}편 제외 → 신규 {len(all_papers)}편")

    if not all_papers:
        print("📭 수집된 논문이 없습니다 (모두 이미 저장됨)")
        sys.exit(0)

    # staging 디렉토리에 저장
    staging_dir = Path(__file__).parent / "staging"
    staging_dir.mkdir(exist_ok=True)

    output_path = staging_dir / "latest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "collected_at": datetime.now().isoformat(),
            "count": len(all_papers),
            "papers": all_papers,
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(all_papers)}편 저장 → {output_path}")


if __name__ == "__main__":
    main()
