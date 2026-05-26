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
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from collectors.arxiv_collector import fetch_arxiv_papers
from collectors.semantic_scholar import fetch_semantic_scholar_papers


def deduplicate(papers: list[dict]) -> list[dict]:
    """제목 기반 중복 제거"""
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].lower().strip().replace(" ", "")
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    print(f"📚 논문 수집 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 수집
    arxiv_papers = fetch_arxiv_papers()
    s2_papers = fetch_semantic_scholar_papers()

    # 중복 제거
    all_papers = deduplicate(arxiv_papers + s2_papers)
    print(f"📊 총 {len(all_papers)}편 (arXiv: {len(arxiv_papers)}, S2: {len(s2_papers)})")

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
