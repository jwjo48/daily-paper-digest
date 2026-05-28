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
    return re.sub(r"[^a-z0-9]", "", title.lower())


def deduplicate(papers: list[dict]) -> list[dict]:
    """제목 기반 중복 제거"""
    seen = set()
    unique = []
    for p in papers:
        key = _norm_title(p["title"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


_FM_TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.MULTILINE)
_FM_URL_RE = re.compile(r'^url:\s*"?(.*?)"?\s*$', re.MULTILINE)


def load_saved_keys() -> tuple[set[str], set[str]]:
    """papers/ 에 이미 저장된 논문의 (정규화된 제목, URL) 집합 반환"""
    titles: set[str] = set()
    urls: set[str] = set()
    if not PAPERS_DIR.exists():
        return titles, urls

    for md in PAPERS_DIR.rglob("*.md"):
        try:
            head = md.read_text(encoding="utf-8")[:1000]
        except OSError:
            continue
        if m := _FM_TITLE_RE.search(head):
            titles.add(_norm_title(m.group(1)))
        if m := _FM_URL_RE.search(head):
            url = m.group(1).strip()
            if url:
                urls.add(url)
    return titles, urls


def filter_already_saved(papers: list[dict]) -> tuple[list[dict], int]:
    """이미 papers/ 에 저장된 논문은 제외"""
    saved_titles, saved_urls = load_saved_keys()
    if not saved_titles and not saved_urls:
        return papers, 0

    kept = []
    skipped = 0
    for p in papers:
        if _norm_title(p.get("title", "")) in saved_titles:
            skipped += 1
            continue
        if p.get("url") and p["url"] in saved_urls:
            skipped += 1
            continue
        kept.append(p)
    return kept, skipped


def main():
    print(f"📚 논문 수집 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 수집
    arxiv_papers = fetch_arxiv_papers()
    s2_papers = fetch_semantic_scholar_papers()

    # 중복 제거
    all_papers = deduplicate(arxiv_papers + s2_papers)
    print(f"📊 총 {len(all_papers)}편 (arXiv: {len(arxiv_papers)}, S2: {len(s2_papers)})")

    # 이미 저장된 논문 제외
    all_papers, skipped = filter_already_saved(all_papers)
    if skipped:
        print(f"🗂️  이미 저장된 {skipped}편 제외 → {len(all_papers)}편 남음")

    if not all_papers:
        print("📭 수집된 논문이 없습니다")
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
