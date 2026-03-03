#!/usr/bin/env python3
"""
bot_server.py — Telegram bot for on-demand paper search.

Conversation flow (per user):
  1. User sends any text message  → treated as topic query
  2. Bot asks for venue           → user replies or skips (empty / "skip")
  3. Bot asks for year            → user replies or skips
  4. Bot asks for count           → user replies or skips (default: 3)
  5. Bot searches + summarises → sends structured 4-section results

Commands:
  /start, /help  → usage instructions
  /search        → reset and start a new search
"""

import json
import os
import sys
import urllib.request
from datetime import datetime
from typing import Optional

# ── project imports ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from collectors.on_demand_search import search_papers
from summarizer import summarize_papers

# ── constants ─────────────────────────────────────────────────────────────────
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
POLL_TIMEOUT = 60           # long-poll seconds per getUpdates call
DEFAULT_COUNT = 3

# ── session state (in-memory; reset each run in GitHub Actions) ───────────────
# { chat_id: { "stage": str, "topic": str, "venue": str|None,
#              "year": int|None, "count": int } }
sessions: dict[int, dict] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Telegram helpers
# ─────────────────────────────────────────────────────────────────────────────

def _telegram(method: str, payload: dict) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{TELEGRAM_API}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"⚠️ Telegram {method} 오류: {e}")
        return None


def send(chat_id: int, text: str, reply_to: Optional[int] = None) -> None:
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to

    result = _telegram("sendMessage", payload)
    if result and not result.get("ok"):
        # fallback: plain text
        payload.pop("parse_mode", None)
        _telegram("sendMessage", payload)


def get_updates(offset: int) -> list[dict]:
    result = _telegram("getUpdates", {
        "offset": offset,
        "timeout": POLL_TIMEOUT,
        "allowed_updates": ["message"],
    })
    if result and result.get("ok"):
        return result.get("result", [])
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Conversation logic
# ─────────────────────────────────────────────────────────────────────────────

def _is_skip(text: str) -> bool:
    """Treat empty string or 'skip' (any case) as skip."""
    return text.strip().lower() in ("", "skip")


def handle_message(chat_id: int, msg_id: int, text: str) -> None:
    text = text.strip()
    cmd = text.lower().split()[0] if text else ""

    # ── Commands ─────────────────────────────────────────────────────────────
    if cmd in ("/start", "/help"):
        sessions.pop(chat_id, None)
        send(chat_id, (
            "📚 <b>Paper Search Bot</b>\n\n"
            "검색하고 싶은 논문 주제를 자유롭게 입력하세요.\n"
            "그러면 venue, 출판 연도, 논문 개수를 차례로 물어볼게요.\n\n"
            "각 단계에서 <b>빈칸</b> 또는 <b>skip</b>을 보내면 기본값을 사용합니다.\n\n"
            "/search — 새 검색 시작\n"
            "/help — 도움말"
        ), reply_to=msg_id)
        return

    if cmd == "/search":
        sessions.pop(chat_id, None)
        send(chat_id, "🔍 어떤 주제의 논문을 찾을까요?", reply_to=msg_id)
        sessions[chat_id] = {"stage": "topic"}
        return

    # ── Session state machine ─────────────────────────────────────────────────
    session = sessions.get(chat_id)

    if session is None:
        # First message → treat as topic
        sessions[chat_id] = {"stage": "topic"}
        session = sessions[chat_id]

    stage = session.get("stage", "topic")

    if stage == "topic":
        if _is_skip(text):
            send(chat_id, "❓ 검색 주제를 입력해 주세요.", reply_to=msg_id)
            return
        session["topic"] = text
        session["stage"] = "venue"
        send(chat_id, (
            f"✅ 검색어: <b>{text}</b>\n\n"
            "📍 <b>Venue</b>를 입력하세요.\n"
            "예: <code>CHI</code> / <code>CSCW</code> / <code>FAccT</code>\n"
            "빈칸 또는 <code>skip</code> → 전체 검색"
        ), reply_to=msg_id)

    elif stage == "venue":
        session["venue"] = None if _is_skip(text) else text
        session["stage"] = "year"
        venue_str = session["venue"] or "전체"
        send(chat_id, (
            f"📍 Venue: <b>{venue_str}</b>\n\n"
            "📅 <b>출판 연도</b>를 입력하세요.\n"
            "예: <code>2024</code>\n"
            "빈칸 또는 <code>skip</code> → 전체 기간"
        ), reply_to=msg_id)

    elif stage == "year":
        if _is_skip(text):
            session["year"] = None
        else:
            try:
                year = int(text)
                if 1990 <= year <= datetime.now().year:
                    session["year"] = year
                else:
                    send(chat_id, "⚠️ 올바른 연도를 입력해 주세요. (예: 2024)", reply_to=msg_id)
                    return
            except ValueError:
                send(chat_id, "⚠️ 숫자로 연도를 입력해 주세요. (예: 2024)", reply_to=msg_id)
                return

        year_str = str(session.get("year")) if session.get("year") else "전체"
        session["stage"] = "count"
        send(chat_id, (
            f"📅 연도: <b>{year_str}</b>\n\n"
            f"🔢 <b>논문 몇 개</b>를 찾을까요?\n"
            f"빈칸 또는 <code>skip</code> → 기본값 {DEFAULT_COUNT}개"
        ), reply_to=msg_id)

    elif stage == "count":
        if _is_skip(text):
            session["count"] = DEFAULT_COUNT
        else:
            try:
                count = int(text)
                if 1 <= count <= 10:
                    session["count"] = count
                else:
                    send(chat_id, "⚠️ 1~10 사이의 숫자를 입력해 주세요.", reply_to=msg_id)
                    return
            except ValueError:
                send(chat_id, "⚠️ 숫자를 입력해 주세요. (예: 5)", reply_to=msg_id)
                return

        # ── All params collected → search ─────────────────────────────────
        topic = session["topic"]
        venue = session.get("venue")
        year = session.get("year")
        count = session.get("count", DEFAULT_COUNT)

        summary_parts = [f"🔍 검색 중...\n• 주제: <b>{topic}</b>"]
        if venue:
            summary_parts.append(f"• Venue: <b>{venue}</b>")
        if year:
            summary_parts.append(f"• 연도: <b>{year}</b>")
        summary_parts.append(f"• 개수: <b>{count}편</b>")
        send(chat_id, "\n".join(summary_parts), reply_to=msg_id)

        # Search
        papers = search_papers(topic=topic, venue=venue, year=year, count=count)

        if not papers:
            send(chat_id, (
                "📭 조건에 맞는 논문을 찾지 못했습니다.\n"
                "Venue나 연도 범위를 넓혀 다시 시도해 보세요.\n\n"
                "새 검색: /search"
            ), reply_to=msg_id)
            sessions.pop(chat_id, None)
            return

        send(chat_id, f"📚 <b>{len(papers)}편</b> 발견! 요약 생성 중...", reply_to=msg_id)

        # Summarize
        scored = summarize_papers(papers)
        if not scored:
            scored = papers   # fallback: send without summaries

        # Send each paper
        for i, p in enumerate(scored, 1):
            _send_paper(chat_id, i, p)

        send(chat_id, "✅ 검색 완료!\n새 검색: /search")
        sessions.pop(chat_id, None)


def _send_paper(chat_id: int, idx: int, p: dict) -> None:
    """Format and send a single paper result."""
    relevance = p.get("relevance", "?")
    title = p.get("title", "")
    venue = p.get("venue", "")
    url = p.get("url", "")
    category_emojis = {
        "human_ai_collab": "🤝", "public_benefits_tech": "🏛️",
        "low_income_populations": "🛡️", "participatory_design": "🎨",
        "algorithmic_fairness": "⚖️", "llm_applications": "🧠",
        "ai_general": "🤖",
    }
    emoji = category_emojis.get(p.get("category", ""), "📄")

    lines = [f"{emoji} <b>{idx}. [{relevance}/10] {title}</b>"]
    if venue:
        lines.append(f"📍 {venue}")
    lines.append("")
    if p.get("background"):
        lines.append(f"🎯 <b>배경/목적:</b> {p['background']}")
    if p.get("methods"):
        lines.append(f"🔬 <b>방법:</b> {p['methods']}")
    if p.get("results"):
        lines.append(f"📊 <b>결과:</b> {p['results']}")
    if p.get("conclusion"):
        lines.append(f"💡 <b>결론:</b> {p['conclusion']}")
    if url:
        lines.append(f"\n<a href=\"{url}\">📎 논문 링크</a>")

    send(chat_id, "\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Offset persistence (GitHub Actions variable)
# ─────────────────────────────────────────────────────────────────────────────

def load_offset() -> int:
    """Load offset from env var (set by GitHub Actions or local env)."""
    return int(os.environ.get("BOT_OFFSET", "0"))


def save_offset(offset: int) -> None:
    """
    Persist the new offset.
    In GitHub Actions, update the repository variable via API.
    Locally, just print it (user can set it manually).
    """
    github_token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    if github_token and repo:
        _update_github_variable(repo, github_token, "BOT_OFFSET", str(offset))
    else:
        print(f"ℹ️  Next BOT_OFFSET={offset}")


def _update_github_variable(repo: str, token: str, name: str, value: str) -> None:
    """Update a GitHub Actions repository variable via REST API."""
    url = f"https://api.github.com/repos/{repo}/actions/variables/{name}"
    payload = json.dumps({"name": name, "value": value}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            print(f"✅ GitHub variable {name} updated to {value}")
    except Exception as e:
        print(f"⚠️ GitHub variable 업데이트 실패: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    offset = load_offset()
    print(f"🤖 Bot server 시작 (offset={offset})")

    updates = get_updates(offset)
    if not updates:
        print("📭 새 메시지 없음")
        return

    for update in updates:
        offset = update["update_id"] + 1
        msg = update.get("message")
        if not msg:
            continue

        chat_id = msg["chat"]["id"]
        msg_id = msg["message_id"]
        text = msg.get("text", "")

        print(f"💬 [{chat_id}] {text!r}")
        try:
            handle_message(chat_id, msg_id, text)
        except Exception as e:
            print(f"⚠️ 메시지 처리 오류: {e}")
            send(chat_id, "⚠️ 처리 중 오류가 발생했습니다. /search 로 다시 시작해 주세요.")

    save_offset(offset)
    print(f"✅ 처리 완료 (다음 offset={offset})")


if __name__ == "__main__":
    main()
