"""
On-demand paper search via Semantic Scholar.
Used by the bot for user-initiated queries.
"""

import json
import urllib.request
import urllib.parse
from typing import Optional

from config import S2_API_KEY

S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,authors,url,venue,year,publicationDate,openAccessPdf,externalIds"


def search_papers(
    topic: str,
    venue: Optional[str] = None,
    year: Optional[int] = None,
    count: int = 3,
) -> list[dict]:
    """
    Search Semantic Scholar for papers matching a topic,
    optionally filtered by venue and/or year.
    """
    params: dict = {
        "query": topic,
        "limit": min(count * 4, 50),   # over-fetch to allow for filtering
        "fields": FIELDS,
        "fieldsOfStudy": "Computer Science",
    }

    if year:
        params["year"] = f"{year}-{year}"

    query_str = urllib.parse.urlencode(params)
    url = f"{S2_API_BASE}/paper/search?{query_str}"

    req = urllib.request.Request(url)
    req.add_header("Content-Type", "application/json")
    if S2_API_KEY:
        req.add_header("x-api-key", S2_API_KEY)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
    except Exception as e:
        print(f"⚠️ Semantic Scholar 검색 오류: {e}")
        return []

    papers = data.get("data", []) or []

    # Venue filter (case-insensitive substring match)
    if venue:
        venue_lower = venue.lower()
        # Common aliases
        aliases = {
            "chi": ["chi", "sigchi", "acm chi"],
            "cscw": ["cscw"],
            "facct": ["facct", "fat*", "fairness"],
            "assets": ["assets"],
            "dis": ["dis"],
            "group": ["group"],
        }
        matched_aliases = aliases.get(venue_lower, [venue_lower])
        papers = [
            p for p in papers
            if p and any(
                alias in (p.get("venue") or "").lower()
                for alias in matched_aliases
            )
        ]

    # Normalize and return up to `count`
    results = []
    for p in papers:
        if p is None:
            continue
        results.append(_normalize(p))
        if len(results) >= count:
            break

    return results


def _normalize(p: dict) -> dict:
    """Convert S2 paper to the project's common format."""
    authors = [a.get("name", "") for a in (p.get("authors") or []) if a]
    url = p.get("url", "")
    pdf_url = ""

    if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
        pdf_url = p["openAccessPdf"]["url"]

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
