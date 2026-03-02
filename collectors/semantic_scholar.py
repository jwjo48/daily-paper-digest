"""
Semantic Scholar 논문 수집기
ACM (CHI, CSCW, FAccT 등) + arXiv를 포함한 폭넓은 검색.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional

from config import S2_API_KEY, SEMANTIC_SCHOLAR_QUERIES, TARGET_VENUES


S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,authors,url,venue,year,publicationDate,openAccessPdf,externalIds"


def _api_request(endpoint: str, params: dict) -> Optional[dict]:
    """Semantic Scholar API 요청"""
    query_str = urllib.parse.urlencode(params)
    url = f"{S2_API_BASE}/{endpoint}?{query_str}"

    req = urllib.request.Request(url)
    req.add_header("Content-Type", "application/json")
    if S2_API_KEY:
        req.add_header("x-api-key", S2_API_KEY)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"⚠️ Semantic Scholar API 오류: {e}")
        return None


def fetch_semantic_scholar_papers() -> list[dict]:
    """Semantic Scholar에서 논문 검색"""
    current_year = datetime.now().year
    all_papers = []

    for query in SEMANTIC_SCHOLAR_QUERIES:
        data = _api_request("paper/search", {
            "query": query,
            "limit": 15,
            "fields": FIELDS,
            "year": f"{current_year - 1}-{current_year}",
            "fieldsOfStudy": "Computer Science",
        })

        if data and "data" in data:
            for paper in data["data"]:
                if paper is None:
                    continue
                all_papers.append(paper)

    # 중복 제거 (paperId 기준)
    seen = set()
    unique = []
    for p in all_papers:
        pid = p.get("paperId", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(_normalize_paper(p))

    print(f"📄 Semantic Scholar에서 {len(unique)}편 수집")
    return unique


def _normalize_paper(p: dict) -> dict:
    """Semantic Scholar 논문을 공통 형식으로 변환"""
    authors = []
    if p.get("authors"):
        authors = [a.get("name", "") for a in p["authors"] if a]

    # URL 결정
    url = p.get("url", "")
    pdf_url = ""
    if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
        pdf_url = p["openAccessPdf"]["url"]

    # arXiv ID가 있으면 arXiv URL 사용
    ext_ids = p.get("externalIds") or {}
    if ext_ids.get("ArXiv"):
        url = f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
        pdf_url = pdf_url or f"https://arxiv.org/pdf/{ext_ids['ArXiv']}"

    return {
        "title": (p.get("title") or "Untitled").strip(),
        "authors": authors,
        "abstract": (p.get("abstract") or "")[:1000],
        "url": url,
        "pdf_url": pdf_url,
        "published": p.get("publicationDate") or str(p.get("year", "")),
        "venue": p.get("venue") or "Unknown",
        "categories": [],
        "source": "semantic_scholar",
    }


if __name__ == "__main__":
    papers = fetch_semantic_scholar_papers()
    for p in papers[:5]:
        print(f"  - [{p['venue']}] {p['title'][:70]}... ({p['published']})")
