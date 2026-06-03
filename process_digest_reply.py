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

# 매칭: "<숫자[,숫자...]> → <목적지>"
# 목적지: 단일 영문자 또는 "N:폴더이름"
_GROUP_RE = re.compile(
    r"(\d+(?:\s*,\s*\d+)*)"                    # paper numbers
    r"\s*(?:→|->|=>|>)\s*"                     # arrow
    r"(N\s*:\s*[^,\n]+?|[A-Za-z])"             # destination
    r"(?=\s*(?:,\s*\d|$))",                    # lookahead: next group or end
    re.UNICODE,
)


# "추천대로 전부 저장" 단축어
_ACCEPT_KEYWORDS = {
    "ok", "okay", "o", "y", "yes", "ㅇ", "ㅇㅇ", "ㅇㅋ", "응", "넵", "네",
    "추천", "추천대로", "recommend", "all", "전부", "다", "go",
}


def recommended_assignments(papers: list[dict]):
    """각 논문의 rec_folder(기존) 또는 rec_new(새 폴더)로 배정 목록 생성."""
    out: list[tuple[int, str]] = []
    for i, p in enumerate(papers, 1):
        folder = (p.get("rec_folder") or p.get("rec_new") or "").strip()
        if folder:
            out.append((i, folder))
    return out


# "N: 생각" — 화살표 없는 줄은 N번 논문에 대한 thoughts
_THOUGHT_LINE_RE = re.compile(r"^\s*(\d+)\s*[:：]\s*(\S.*?)\s*$")


def parse_reply(text: str, folder_map: dict[str, str], num_papers: int,
                papers: list[dict] | None = None):
    """Returns (assignments, thoughts, error).

    assignments: list of (paper_num, folder_name)
    thoughts:    dict {paper_num: thought_text}

    지원 형식:
      1,3 → A                      (기존)
      2 → N:새폴더                 (기존)
      1 → A | 신뢰 보정에 유용     (인라인 thoughts, 한 줄 한 논문)
      ok                           (추천대로 저장)
      1: 이 논문은 ...             (N번 논문 thoughts만 추가)
    """
    papers = papers or []
    text = text.replace("⇒", "→").replace("➔", "→").replace("=>", "→").replace("->", "→")

    thoughts: dict[int, str] = {}
    body_lines: list[str] = []

    # 1) "N: 생각" 형태(화살표 없음)는 thoughts로 분리
    for line in text.splitlines():
        if "→" not in line and ">" not in line:
            m = _THOUGHT_LINE_RE.match(line)
            if m:
                n = int(m.group(1))
                if 1 <= n <= num_papers:
                    thoughts[n] = m.group(2).strip()
                    continue
        body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if body.lower() in ("skip", "0", "pass", "패스", "건너뛰기"):
        return [], {}, None  # explicit skip (thoughts 무시)

    # 2) "ok / ㅇㅇ / 추천대로" → 추천 테마 그대로
    if body.lower() in _ACCEPT_KEYWORDS:
        assignments = recommended_assignments(papers)
        if not assignments:
            return None, thoughts, "추천 테마 정보가 없어 자동 저장할 수 없어요."
        return assignments, thoughts, None

    if not body and thoughts:
        # thoughts만 보냈는데 저장 대상이 없음
        return None, thoughts, "어느 폴더에 저장할지 함께 알려주세요. 예: 1 → A | 생각"

    # 3) 배정 줄 파싱 (줄마다 처리, 줄 끝 '| 생각'은 그 논문 thoughts)
    assignments: list[tuple[int, str]] = []
    for seg in body.splitlines():
        if not seg.strip():
            continue
        seg_thought = None
        if "|" in seg:
            left, seg_thought = seg.split("|", 1)
            seg_thought = seg_thought.strip() or None
        else:
            left = seg

        matches = list(_GROUP_RE.finditer(left))
        if not matches:
            return None, thoughts, f"형식을 인식하지 못했습니다: {seg.strip()!r}"

        for m in matches:
            nums_str, dest = m.group(1), m.group(2).strip()
            if dest.upper().startswith("N"):
                folder = dest.split(":", 1)[1].strip() if ":" in dest else ""
                if not folder:
                    return None, thoughts, "새 폴더 이름이 비어있습니다. (예: N:폴더이름)"
            else:
                folder = folder_map.get(dest.upper())
                if not folder:
                    return None, thoughts, f"폴더 '{dest.upper()}'는 목록에 없습니다."

            try:
                nums = [int(n.strip()) for n in nums_str.split(",")]
            except ValueError:
                return None, thoughts, f"논문 번호를 인식하지 못했습니다: {nums_str!r}"

            for n in nums:
                if not (1 <= n <= num_papers):
                    return None, thoughts, f"논문 번호 {n}은 1~{num_papers} 범위가 아닙니다."
                assignments.append((n, folder))
                if seg_thought:
                    thoughts[n] = seg_thought

    if not assignments:
        return None, thoughts, "형식을 인식하지 못했습니다."

    return assignments, thoughts, None


# ─── Markdown writer ─────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def _yaml_escape(text: str) -> str:
    """YAML 더블쿼트 문자열용 이스케이프."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def write_paper_md(paper: dict, folder: str, thought: str = "") -> Path:
    folder_dir = PAPERS_DIR / folder
    folder_dir.mkdir(parents=True, exist_ok=True)

    title = paper.get("title", "Untitled")
    file_path = folder_dir / f"{_slugify(title)}.md"

    thought = (thought or "").strip()
    # frontmatter 의 따옴표 문자열은 모두 이스케이프 (제목 등에 " 포함 시 YAML 깨짐 방지)
    title_y = _yaml_escape(title)
    authors_y = _yaml_escape(paper.get("authors", ""))
    url_y = _yaml_escape(paper.get("url", ""))
    venue_y = _yaml_escape(paper.get("venue", ""))
    # thought_tags 는 비워둠 → enrich-thought-tags 워크플로우(Claude)가 채움
    md = f"""---
title: "{title_y}"
authors: "{authors_y}"
url: "{url_y}"
venue: "{venue_y}"
relevance: {paper.get('relevance', '?')}
date: {paper.get('date', datetime.now().strftime('%Y-%m-%d'))}
category: {paper.get('category', 'ai_general')}
tags: [paper, {paper.get('category', 'ai_general')}]
thoughts: "{_yaml_escape(thought)}"
thought_tags: []
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

## 🧠 내 생각
{thought}

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

        assignments, thoughts, err = parse_reply(
            text, folder_map, len(papers), papers
        )

        if err:
            send(
                f"⚠️ {err}\n\n"
                f"형식 예시:\n"
                f"• 1,3 → A\n"
                f"• 2 → N:Benefits Navigation\n"
                f"• 1 → A | 내 생각 한 줄\n"
                f"• ok  (추천대로 저장)\n"
                f"• skip (저장 안 함)",
                reply_to=msg_id,
            )
            continue

        if not assignments:
            send("⏭️ 오늘 논문은 저장하지 않을게요.", reply_to=msg_id)
            continue

        # Save
        lines = []
        n_thoughts = 0
        for n, folder in assignments:
            paper = papers[n - 1]
            thought = thoughts.get(n, "")
            if thought:
                n_thoughts += 1
            path = write_paper_md(paper, folder, thought)
            saved_files.append(path)
            folder_summary[folder] += 1
            title = paper.get("title", "")[:60]
            mark = " 📝" if thought else ""
            lines.append(f"  • [{paper.get('relevance','?')}/10] {title} → {folder}{mark}")

        footer = ""
        if n_thoughts:
            footer = f"\n\n🧠 생각 {n_thoughts}개 저장됨 — 태그는 곧 자동 생성됩니다."
        send(
            f"✅ {len(assignments)}편 저장 완료:\n" + "\n".join(lines) + footer,
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


if __name__ == "__main__":
    main()
