"""
arXiv 논문 수집기
cs.HC, cs.AI, cs.CY 등에서 키워드 기반으로 최근 논문을 가져옵니다.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from config import ARXIV_CATEGORIES, ARXIV_KEYWORDS, DAYS_LOOKBACK


ARXIV_API_URL = "http://export.arxiv.org/api/query"


def _build_query() -> str:
    """arXiv API 쿼리 문자열 생성"""
    # 키워드 OR 조합
    keyword_parts = [f'abs:"{kw}"' for kw in ARXIV_KEYWORDS]
    keyword_query = " OR ".join(keyword_parts)

    # 카테고리 OR 조합
    cat_parts = [f"cat:{cat}" for cat in ARXIV_CATEGORIES]
    cat_query = " OR ".join(cat_parts)

    return f"({cat_query}) AND ({keyword_query})"


def fetch_arxiv_papers() -> list[dict]:
    """arXiv에서 최근 논문 수집"""
    query = _build_query()
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": 50,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })

    url = f"{ARXIV_API_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
    except Exception as e:
        print(f"⚠️ arXiv API 오류: {e}")
        return []

    # XML 파싱
    root = ET.fromstring(data)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_LOOKBACK)
    papers = []

    for entry in root.findall("atom:entry", ns):
        # 날짜 파싱
        published_str = entry.find("atom:published", ns).text
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

        if published < cutoff:
            continue

        # 카테고리 확인
        categories = [
            cat.get("term")
            for cat in entry.findall("atom:category", ns)
        ]
        if not any(c in categories for c in ARXIV_CATEGORIES):
            continue

        # 논문 정보 추출
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        authors = [
            a.find("atom:name", ns).text
            for a in entry.findall("atom:author", ns)
        ]

        # URL 추출
        paper_url = entry.find("atom:id", ns).text
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")

        papers.append({
            "title": title,
            "authors": authors,
            "abstract": abstract[:1000],  # 토큰 절약
            "url": paper_url,
            "pdf_url": pdf_url,
            "published": published.strftime("%Y-%m-%d"),
            "venue": "arXiv",
            "categories": categories,
            "source": "arxiv",
        })

    print(f"📄 arXiv에서 {len(papers)}편 수집")
    return papers


if __name__ == "__main__":
    papers = fetch_arxiv_papers()
    for p in papers[:5]:
        print(f"  - {p['title'][:80]}... ({p['published']})")
