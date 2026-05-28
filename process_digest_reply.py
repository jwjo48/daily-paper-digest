#!/usr/bin/env python3
"""
process_digest_reply.py — Telegram 답장을 받아 사용자가 선택한 논문을 저장.

매 10분마다 GitHub Actions에서 실행.
API/Max 쿼터를 전혀 쓰지 않음 (순수 Python).

답장 형식:
  1,3 → A             (1번, 3번 논문을 A 폴더에 저장)
  2 → N:새폴더        (2번 논문을 "새폴더"라는 새 폴더에 저장)
  1,3 → A, 2 → N:폴더  (혼합)
  skip / 0            (저장 안 함)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
STATE_FILE = Path(__file__).parent / ".bot_state.json"
DIGEST_FILE = Path(__file__).parent / "staging" / "digest.json"
PAPERS_DIR = Path(__file__).parent / "papers"
POLL_TIMEOUT = 25


# ─── Telegram helpers ────────────────────────────────────────────────────────

def _telegram(method: str, payload: dict) -> dict | None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{TELEGRAM_API}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=POLL_TIMEOUT + 10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"⚠️ Telegram {method} 오류: {e}")
        return None


def get_updates(offset: int) -> list[dict]:
    res = _telegram("getUpdates", {
        "offset": offset, "timeout": POLL_TIMEOUT, "allowed_updates": ["message"]
    })
    if res and res.get("ok"):
        return res.get("result", [])
    return []


def send(text: str, reply_to: int | None = None) -> None:
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    _telegram("sendMessage", payload)


# ─── State persistence ───────────────────────────────────────────────────────

def load_offset() -> int:
    try:
        with open(STATE_FILE) as f:
            return int(json.load(f).get("offset", 0))
    except Exception:
        return 0


def save_offset(offset: int) -> None:
    state = {}
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except Exception:
        pass
    state["offset"] = offset
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ─── Reply parser ────────────────────────────────────────────────────────────

# Lenient tokenizer: extracts paper numbers, "N:folder" destinations, or
# isolated single-letter destinations. Arrows are optional and normalized away
# before tokenizing so both "1,3 → A" and "1,3 A" / "1 3 A" / "1.3 A" work.
_ARROW_RE = re.compile(r"(?:→|->|=>|>)")
_TOKEN_RE = re.compile(
    r"(?P<num>\d+)"
    r"|(?P<ndest>\bN\s*:\s*[^,\n]+?)(?=\s*(?:,|\n|$))"
    r"|(?<![A-Za-z])(?P<letter>[A-Za-z])(?![A-Za-z])",
    re.UNICODE,
)


def parse_reply(text: str, folder_map: dict[str, str], num_papers: int):
    """Returns (assignments, error). assignments is list of (paper_num, folder_name)."""
    text = text.strip().replace("⇒", "→").replace("➔", "→")

    if text.lower() in ("skip", "0", "pass", "패스", "건너뛰기"):
        return [], None  # explicit skip

    # Arrows are optional — strip to spaces so the tokenizer sees clean boundaries.
    normalized = _ARROW_RE.sub(" ", text)

    assignments: list[tuple[int, str]] = []
    pending_nums: list[int] = []

    for m in _TOKEN_RE.finditer(normalized):
        if num := m.group("num"):
            pending_nums.append(int(num))
            continue

        if ndest := m.group("ndest"):
            folder = ndest.split(":", 1)[1].strip()
            if not folder:
                return None, "새 폴더 이름이 비어있습니다. (예: N:폴더이름)"
        else:
            letter = m.group("letter").upper()
            folder = folder_map.get(letter)
            if not folder:
                return None, f"폴더 '{letter}'는 목록에 없습니다."

        if not pending_nums:
            return None, f"폴더 지정 앞에 논문 번호가 없습니다: {m.group(0)!r}"

        for n in pending_nums:
            if not (1 <= n <= num_papers):
                return None, f"논문 번호 {n}은 1~{num_papers} 범위가 아닙니다."
            assignments.append((n, folder))
        pending_nums = []

    if pending_nums:
        return None, f"논문 번호 {pending_nums}에 폴더 지정이 없습니다."

    if not assignments:
        return None, "형식을 인식하지 못했습니다."

    return assignments, None


# ─── Markdown writer ─────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def write_paper_md(paper: dict, folder: str) -> Path:
    folder_dir = PAPERS_DIR / folder
    folder_dir.mkdir(parents=True, exist_ok=True)

    title = paper.get("title", "Untitled")
    file_path = folder_dir / f"{_slugify(title)}.md"

    md = f"""---
title: "{title}"
authors: "{paper.get('authors', '')}"
url: "{paper.get('url', '')}"
venue: "{paper.get('venue', '')}"
relevance: {paper.get('relevance', '?')}
date: {paper.get('date', datetime.now().strftime('%Y-%m-%d'))}
tags: [paper, {paper.get('category', 'ai_general')}]
status: unread
---

# {title}

**저자:** {paper.get('authors', '')}
**발표:** {paper.get('venue', '')} ({paper.get('date', '')})
**링크:** [논문]({paper.get('url', '')})

## 🎯 배경/목적
{paper.get('background', '')}

## 🔬 방법
{paper.get('methods', '')}

## 📊 결과
{paper.get('results', '')}

## 💡 결론
{paper.get('conclusion', '')}

## 🔗 연구 연관성
{paper.get('connection', '')}

---
## 메모

"""
    file_path.write_text(md, encoding="utf-8")
    return file_path


# ─── Git ─────────────────────────────────────────────────────────────────────

def git_commit_and_push(files: list[Path], message: str) -> None:
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    add_args = ["git", "add", str(STATE_FILE)] + [str(f) for f in files]
    subprocess.run(add_args, check=True)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode
    if diff == 0:
        return  # nothing staged

    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)


def commit_state_only() -> None:
    """Persist .bot_state.json even when no papers were saved, so the
    offset advances past skipped/malformed/no-digest updates instead of
    re-fetching them on every run."""
    today = datetime.now().strftime("%Y-%m-%d")
    git_commit_and_push([], f"chore: advance bot offset ({today})")


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN/CHAT_ID 없음")
        sys.exit(1)

    offset = load_offset()
    print(f"🤖 Reply processor (offset={offset})")

    updates = get_updates(offset)
    if not updates:
        print("📭 새 메시지 없음")
        return

    digest = None
    if DIGEST_FILE.exists():
        with open(DIGEST_FILE) as f:
            digest = json.load(f)

    saved_files: list[Path] = []
    folder_summary: dict[str, int] = defaultdict(int)

    for update in updates:
        offset = update["update_id"] + 1
        msg = update.get("message") or {}
        text = (msg.get("text") or "").strip()
        msg_id = msg.get("message_id")

        if not text:
            continue

        print(f"💬 {text!r}")

        if not digest or not digest.get("papers"):
            send("⚠️ 오늘의 digest가 아직 없습니다.", reply_to=msg_id)
            continue

        folder_map = digest.get("folders", {})
        papers = digest["papers"]
        assignments, err = parse_reply(text, folder_map, len(papers))

        if err:
            send(
                f"⚠️ {err}\n\n"
                f"형식 예시 (화살표 생략 가능):\n"
                f"• 1,3 A\n"
                f"• 2 3 4 E\n"
                f"• 2 → N:Benefits Navigation\n"
                f"• 1,3 A\\n2 N:새폴더 (줄바꿈으로 구분)\n"
                f"• skip (저장 안 함)",
                reply_to=msg_id,
            )
            continue

        if not assignments:
            send("⏭️ 오늘 논문은 저장하지 않을게요.", reply_to=msg_id)
            continue

        # Save
        lines = []
        for n, folder in assignments:
            paper = papers[n - 1]
            path = write_paper_md(paper, folder)
            saved_files.append(path)
            folder_summary[folder] += 1
            title = paper.get("title", "")[:60]
            lines.append(f"  • [{paper.get('relevance','?')}/10] {title} → {folder}")

        send(
            f"✅ {len(assignments)}편 저장 완료:\n" + "\n".join(lines),
            reply_to=msg_id,
        )

    save_offset(offset)

    if saved_files:
        today = datetime.now().strftime("%Y-%m-%d")
        folders_str = ", ".join(f"{f} ({n})" for f, n in folder_summary.items())
        git_commit_and_push(
            saved_files,
            f"papers: add {len(saved_files)} via Telegram → {folders_str} ({today})",
        )
    else:
        # No papers saved, but we still consumed updates — persist the new
        # offset so the same updates aren't re-fetched on the next run.
        commit_state_only()


if __name__ == "__main__":
    main()
