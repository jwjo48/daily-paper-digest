#!/usr/bin/env python3
"""
send_digest_telegram.py — staging/digest.json을 읽어 Telegram에 전송.

워크플로우 step에서 직접 호출 (Claude 안에서 호출하지 않음).
명시적 진단 + non-zero exit로 실패가 워크플로우에 노출됨.

ENV:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

DIGEST_FILE = Path(__file__).parent / "staging" / "digest.json"


def _send(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read())
            if result.get("ok"):
                print(f"✅ Sent ({len(text)} chars): {text[:60].replace(chr(10), ' ')}...")
                return True
            print(f"⚠️ Telegram returned error: {result}")
            return False
    except Exception as e:
        print(f"❌ Send failed: {e}")
        return False


def _format_paper(p: dict, folders: dict | None = None) -> str:
    num = p.get("number", "?")
    rel = p.get("relevance", "?")
    title = p.get("title", "")
    venue = p.get("venue", "")
    url = p.get("url", "")

    lines = [f"{num}. [{rel}/10] {title}"]
    if venue:
        lines.append(f"📍 {venue}")
    lines.append("")
    if p.get("background"):
        lines.append(f"🎯 배경: {p['background']}")
    if p.get("methods"):
        lines.append(f"🔬 방법: {p['methods']}")
    if p.get("results"):
        lines.append(f"📊 결과: {p['results']}")
    if p.get("conclusion"):
        lines.append(f"💡 결론: {p['conclusion']}")
    if p.get("connection"):
        lines.append("")
        lines.append(f"🔗 {p['connection']}")
    rec = _format_recommendation(p, folders or {})
    if rec:
        lines.append("")
        lines.append(rec)
    if url:
        lines.append(f"📎 {url}")
    return "\n".join(lines)


def _format_recommendation(p: dict, folders: dict) -> str:
    """논문별 테마 추천 한 줄. rec_folder(기존) 또는 rec_new(새 폴더 제안)."""
    reason = p.get("rec_reason", "")
    suffix = f" — {reason}" if reason else ""
    rec_folder = p.get("rec_folder")
    rec_new = p.get("rec_new")
    if rec_folder:
        letter = next((k for k, v in folders.items() if v == rec_folder), None)
        label = f"{letter}) {rec_folder}" if letter else rec_folder
        return f"💡 추천 테마: {label}{suffix}"
    if rec_new:
        return f"💡 추천 테마: 🆕 새 폴더 '{rec_new}'{suffix}"
    return ""


def _format_picker(folders: dict, has_recs: bool = False) -> str:
    lines = ["📂 저장할 폴더 선택", ""]
    for letter in sorted(folders.keys()):
        lines.append(f"{letter}) {folders[letter]}")
    lines.append("")
    lines.append("(N으로 시작하면 새 폴더 생성)")
    lines.append("")
    if has_recs:
        lines.append("✅ 추천대로 전부 저장:  ok  (또는 y / ㅇㅇ)")
        lines.append("")
    lines.append("직접 지정 형식:")
    lines.append("• 1,3 → A")
    lines.append("• 2 → N:Benefits Navigation")
    lines.append("• 1,3 → A, 2 → N:새폴더")
    lines.append("")
    lines.append("저장 안 함: skip 또는 0")
    return "\n".join(lines)


def main() -> int:
    print(f"📤 send_digest_telegram.py")
    print(f"   TELEGRAM_BOT_TOKEN: {'SET (' + str(len(TOKEN)) + ' chars)' if TOKEN else '❌ EMPTY'}")
    print(f"   TELEGRAM_CHAT_ID:   {CHAT_ID if CHAT_ID else '❌ EMPTY'}")
    print(f"   DIGEST_FILE:        {DIGEST_FILE} ({'exists' if DIGEST_FILE.exists() else 'MISSING'})")

    if not TOKEN or not CHAT_ID:
        print("❌ Telegram credentials missing. Aborting.")
        return 1

    if not DIGEST_FILE.exists():
        print("⚠️ digest.json missing — sending 'no papers' message.")
        ok = _send(f"📭 오늘은 관련 논문이 없습니다.")
        return 0 if ok else 1

    with open(DIGEST_FILE, encoding="utf-8") as f:
        digest = json.load(f)

    papers = digest.get("papers", [])
    folders = digest.get("folders", {})
    date = digest.get("date", "")

    print(f"   papers: {len(papers)}, folders: {len(folders)}, date: {date}")

    if not papers:
        _send(f"📭 오늘은 관련 논문이 없습니다. ({date})")
        return 0

    failures = 0
    if not _send(f"📚 오늘의 논문 {len(papers)}편 ({date})"):
        failures += 1

    for p in papers:
        if not _send(_format_paper(p, folders)):
            failures += 1

    if folders:
        has_recs = any(p.get("rec_folder") or p.get("rec_new") for p in papers)
        if not _send(_format_picker(folders, has_recs)):
            failures += 1

    if failures:
        print(f"⚠️ {failures} message(s) failed to send")
        return 1
    print(f"✅ All {len(papers) + 2} messages sent successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
