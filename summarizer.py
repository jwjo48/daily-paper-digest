"""
Claude API를 사용한 논문 요약 + 관련성 스코어링
"""

import json
import urllib.request
from typing import Optional

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_PAPERS_TO_SUMMARIZE,
    MIN_RELEVANCE_SCORE,
    RESEARCH_CONTEXT,
)


def summarize_papers(papers: list[dict]) -> list[dict]:
    """
    논문 목록을 Claude에 보내서 관련성 스코어 + 한영 요약을 받습니다.
    MIN_RELEVANCE_SCORE 이상인 논문만 반환.
    """
    if not papers:
        print("⚠️ 요약할 논문이 없습니다")
        return []

    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다")
        return _fallback_summary(papers)

    # 토큰 절약: 상위 N개만
    papers_to_send = papers[:MAX_PAPERS_TO_SUMMARIZE]

    # 논문 텍스트 구성
    papers_text = ""
    for i, p in enumerate(papers_to_send):
        papers_text += f"""
---
[Paper {i + 1}]
Title: {p['title']}
Authors: {', '.join(p['authors'][:5])}
Venue: {p['venue']}
URL: {p['url']}
Abstract: {p['abstract'][:500]}
---
"""

    # Claude API 호출
    response = _call_claude(papers_text)
    if not response:
        return _fallback_summary(papers_to_send)

    # JSON 파싱
    scored_papers = _parse_response(response, papers_to_send)

    # 관련성 필터링
    filtered = [p for p in scored_papers if p.get("relevance", 0) >= MIN_RELEVANCE_SCORE]
    filtered.sort(key=lambda x: x.get("relevance", 0), reverse=True)

    print(f"✅ {len(filtered)}편이 관련성 {MIN_RELEVANCE_SCORE}점 이상")
    return filtered


def _call_claude(papers_text: str) -> Optional[str]:
    """Claude API 호출"""
    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "system": RESEARCH_CONTEXT,
        "messages": [{
            "role": "user",
            "content": f"Analyze these papers and return a JSON array:\n{papers_text}",
        }],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read())
            # content 블록에서 텍스트 추출
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
    except Exception as e:
        print(f"⚠️ Claude API 오류: {e}")

    return None


def _parse_response(response_text: str, original_papers: list[dict]) -> list[dict]:
    """Claude 응답을 파싱하여 원본 논문 데이터와 병합"""
    # JSON 추출 (마크다운 코드블록 제거)
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        summaries = json.loads(text)
    except json.JSONDecodeError:
        # JSON 배열 부분만 추출 시도
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                summaries = json.loads(text[start:end])
            except json.JSONDecodeError:
                print("⚠️ Claude 응답 JSON 파싱 실패")
                return _fallback_summary(original_papers)
        else:
            print("⚠️ Claude 응답에서 JSON 배열을 찾을 수 없음")
            return _fallback_summary(original_papers)

    # 원본 논문 데이터와 병합
    results = []
    for i, summary in enumerate(summaries):
        if i < len(original_papers):
            paper = original_papers[i].copy()
            paper.update({
                "relevance": summary.get("relevance", 0),
                "summary_ko": summary.get("summary_ko", "요약 없음"),
                "summary_en": summary.get("summary_en", "No summary"),
                "connection": summary.get("connection", ""),
                "category": summary.get("category", "ai_general"),
            })
            results.append(paper)

    return results


def _fallback_summary(papers: list[dict]) -> list[dict]:
    """API 실패 시 기본 요약 (제목+초록만)"""
    print("📝 Fallback 모드: API 없이 기본 정보만 포함")
    results = []
    for p in papers:
        p_copy = p.copy()
        p_copy.update({
            "relevance": 5,
            "summary_ko": p["abstract"][:200] if p["abstract"] else "초록 없음",
            "summary_en": p["abstract"][:200] if p["abstract"] else "No abstract",
            "connection": "",
            "category": "ai_general",
        })
        results.append(p_copy)
    return results
