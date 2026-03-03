"""
Telegram Bot으로 논문 다이제스트를 핸드폰에 전송
"""

import json
import urllib.request
from datetime import datetime

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_TELEGRAM_LENGTH


def send_digest_to_telegram(papers: list[dict]) -> bool:
    """요약된 논문 목록을 Telegram으로 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram 설정이 없습니다 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
        return False

    today = datetime.now().strftime("%Y-%m-%d")

    if not papers:
        return _send_message(f"📭 *Daily Paper Digest — {today}*\n\n오늘은 관련 논문이 없습니다.")

    # 메시지 구성
    header = f"📚 *Daily Paper Digest — {today}*\n"
    header += f"관련 논문 *{len(papers)}*편 발견!\n\n"

    body = ""
    for i, p in enumerate(papers, 1):
        relevance = p.get("relevance", "?")
        title = _escape_md(p["title"])
        venue = _escape_md(p.get("venue", ""))
        url = p.get("url", "")
        category_emoji = _category_emoji(p.get("category", ""))

        entry = f"{category_emoji} *{i}\\. \\[{relevance}/10\\] {title}*\n"
        if venue:
            entry += f"📍 {venue}\n"
        entry += "\n"
        if p.get("background"):
            entry += f"🎯 *배경/목적:* {_escape_md(p['background'])}\n"
        if p.get("methods"):
            entry += f"🔬 *방법:* {_escape_md(p['methods'])}\n"
        if p.get("results"):
            entry += f"📊 *결과:* {_escape_md(p['results'])}\n"
        if p.get("conclusion"):
            entry += f"💡 *결론:* {_escape_md(p['conclusion'])}\n"
        if url:
            entry += f"[논문 링크]({url})\n"
        entry += "\n"

        body += entry

    full_message = header + body

    # Telegram 메시지 길이 제한 처리
    if len(full_message) <= MAX_TELEGRAM_LENGTH:
        return _send_message(full_message)
    else:
        # 분할 전송
        success = _send_message(header + f"\\(아래 {len(papers)}편\\)")
        for i, p in enumerate(papers, 1):
            relevance = p.get("relevance", "?")
            title = _escape_md(p["title"])
            url = p.get("url", "")
            emoji = _category_emoji(p.get("category", ""))

            msg = f"{emoji} *{i}\\. \\[{relevance}/10\\]* *{title}*\n\n"
            if p.get("background"):
                msg += f"🎯 *배경/목적:* {_escape_md(p['background'])}\n"
            if p.get("methods"):
                msg += f"🔬 *방법:* {_escape_md(p['methods'])}\n"
            if p.get("results"):
                msg += f"📊 *결과:* {_escape_md(p['results'])}\n"
            if p.get("conclusion"):
                msg += f"💡 *결론:* {_escape_md(p['conclusion'])}\n"
            if url:
                msg += f"[링크]({url})"

            success = _send_message(msg) and success

        return success


def send_error_to_telegram(error_msg: str) -> bool:
    """에러 발생 시 Telegram으로 알림"""
    return _send_message(f"⚠️ *Paper Digest 오류*\n\n{_escape_md(error_msg)}")


def _send_message(text: str) -> bool:
    """Telegram 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read())
            if result.get("ok"):
                return True
            print(f"⚠️ Telegram 응답 오류: {result}")
    except Exception as e:
        print(f"⚠️ Telegram 전송 실패: {e}")
        # MarkdownV2 파싱 실패 시 plain text로 재시도
        return _send_plain(text)

    return False


def _send_plain(text: str) -> bool:
    """Fallback: plain text로 전송"""
    # 마크다운 이스케이프 제거
    clean = text.replace("\\", "").replace("*", "").replace("_", "").replace("`", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": clean,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read()).get("ok", False)
    except Exception as e:
        print(f"⚠️ Telegram plain text 전송도 실패: {e}")
        return False


def _escape_md(text: str) -> str:
    """MarkdownV2용 특수문자 이스케이프"""
    special = r"_[]()~`>#+-=|{}.!"
    result = ""
    for char in text:
        if char in special:
            result += f"\\{char}"
        else:
            result += char
    return result


def _category_emoji(category: str) -> str:
    """카테고리별 이모지"""
    return {
        "human_ai_collab": "🤝",
        "public_benefits_tech": "🏛️",
        "low_income_populations": "🛡️",
        "participatory_design": "🎨",
        "algorithmic_fairness": "⚖️",
        "llm_applications": "🧠",
        "ai_general": "🤖",
    }.get(category, "📄")
