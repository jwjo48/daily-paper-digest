"""
Obsidian vault에 마크다운 논문 노트 생성
iCloud 동기화를 통해 Mac + iPhone에서 접근 가능.
"""

import os
import re
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR, IS_CI


def save_papers_to_obsidian(papers: list[dict]) -> list[str]:
    """
    논문 목록을 Obsidian vault에 마크다운 파일로 저장.
    1. 일간 다이제스트 파일 (digest-YYYY-MM-DD.md)
    2. 개별 논문 노트 (선택, 관련성 8+ 논문만)
    
    Returns: 생성된 파일 경로 목록
    """
    today = datetime.now().strftime("%Y-%m-%d")
    day_dir = OUTPUT_DIR / today

    # 폴더 생성
    day_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    # 1. 일간 다이제스트
    digest_path = day_dir / f"digest-{today}.md"
    digest_content = _generate_digest(papers, today)
    digest_path.write_text(digest_content, encoding="utf-8")
    created_files.append(str(digest_path))
    print(f"📝 다이제스트 저장: {digest_path}")

    # 2. 관련성 높은 논문은 개별 노트 생성
    for p in papers:
        if p.get("relevance", 0) >= 8:
            note_path = day_dir / f"{_slugify(p['title'])}.md"
            note_content = _generate_paper_note(p, today)
            note_path.write_text(note_content, encoding="utf-8")
            created_files.append(str(note_path))

    print(f"📁 총 {len(created_files)}개 파일 생성 → {day_dir}")

    if IS_CI:
        print(f"ℹ️  CI 환경: 파일이 {day_dir}에 저장되었습니다")
        print("   로컬에서 실행하면 iCloud Obsidian vault에 직접 저장됩니다")

    return created_files


def _generate_digest(papers: list[dict], today: str) -> str:
    """일간 다이제스트 마크다운 생성"""
    lines = [
        "---",
        f'title: "Daily Paper Digest - {today}"',
        f"date: {today}",
        "type: digest",
        "tags: [daily-digest, papers, auto-generated]",
        "---",
        "",
        f"# 📚 Daily Paper Digest — {today}",
        "",
        f"> {len(papers)}편의 관련 논문이 발견되었습니다.",
        "",
    ]

    if not papers:
        lines.append("오늘은 관련 논문이 없습니다.")
        return "\n".join(lines)

    for i, p in enumerate(papers, 1):
        relevance = p.get("relevance", "?")
        emoji = _category_emoji(p.get("category", ""))
        title = p["title"]
        authors_str = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors_str += " et al."

        lines.append(f"## {emoji} {i}. [{relevance}/10] {title}")
        lines.append("")
        lines.append(f"**저자:** {authors_str}")
        lines.append(f"**발표:** {p.get('venue', '')} | {p.get('published', '')}")
        if p.get("url"):
            lines.append(f"**링크:** [논문]({p['url']})", )
        if p.get("pdf_url"):
            lines.append(f" | [PDF]({p['pdf_url']})")
        lines.append("")

        # 4-section Korean summary
        if p.get("background"):
            lines.append(f"**🎯 배경/목적:** {p['background']}")
            lines.append("")
        if p.get("methods"):
            lines.append(f"**🔬 방법:** {p['methods']}")
            lines.append("")
        if p.get("results"):
            lines.append(f"**📊 결과:** {p['results']}")
            lines.append("")
        if p.get("conclusion"):
            lines.append(f"**💡 결론:** {p['conclusion']}")
            lines.append("")

        # 연구 연관성
        if p.get("connection"):
            lines.append(f"**🔗 연구 연관성:** {p['connection']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("*Generated automatically by daily-paper-digest*")

    return "\n".join(lines)


def _generate_paper_note(paper: dict, today: str) -> str:
    """개별 논문 노트 마크다운 생성"""
    authors_str = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors_str += " et al."

    tags = ["paper", paper.get("category", "ai_general")]
    if paper.get("venue"):
        tags.append(paper["venue"].lower().replace(" ", "-"))

    lines = [
        "---",
        f'title: "{paper["title"]}"',
        f'authors: "{authors_str}"',
        f'url: "{paper.get("url", "")}"',
        f'venue: "{paper.get("venue", "")}"',
        f"relevance: {paper.get('relevance', 0)}",
        f"date: {today}",
        f"tags: [{', '.join(tags)}]",
        "status: unread",
        "---",
        "",
        f"# {paper['title']}",
        "",
        f"**저자:** {authors_str}",
        f"**발표:** {paper.get('venue', '')} ({paper.get('published', '')})",
    ]

    if paper.get("url"):
        lines.append(f"**링크:** [논문]({paper['url']})")
    if paper.get("pdf_url"):
        lines.append(f"**PDF:** [다운로드]({paper['pdf_url']})")

    lines.extend([
        "",
        "## 🎯 배경/목적",
        paper.get("background", "없음"),
        "",
        "## 🔬 방법",
        paper.get("methods", "없음"),
        "",
        "## 📊 결과",
        paper.get("results", "없음"),
        "",
        "## 💡 결론",
        paper.get("conclusion", "없음"),
        "",
        "## 연구 관련성",
        paper.get("connection", "분석 필요"),
        "",
        "---",
        "## 메모",
        "<!-- 여기에 직접 메모를 추가하세요 -->",
        "",
        "",
        "## 심화 분석",
        "<!-- Post Webhook으로 심화분석 결과가 여기에 추가됩니다 -->",
        "",
    ])

    return "\n".join(lines)


def _slugify(text: str, limit: int = 120) -> str:
    """파일명에 사용 가능한 슬러그 생성 (단어 경계에서 자름)"""
    # 특수문자 제거, 공백을 하이픈으로
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    if len(slug) <= limit:
        return slug
    cut = slug[:limit]
    if "-" in cut:
        cut = cut.rsplit("-", 1)[0]
    return cut.strip("-")


def _category_emoji(category: str) -> str:
    return {
        "human_ai_collab": "🤝",
        "public_benefits_tech": "🏗️",
        "low_income_populations": "🛡️",
        "participatory_design": "🎨",
        "algorithmic_fairness": "⚖️",
        "llm_applications": "🧠",
        "ai_general": "🤖",
    }.get(category, "📄")
