#!/usr/bin/env python3
"""
daily_digest.py — 매일 실행되는 메인 스크립트

논문 수집 → Claude 요약 → Obsidian 저장 → Telegram 알림
"""

import sys
import traceback
from datetime import datetime

from collectors.arxiv_collector import fetch_arxiv_papers
from collectors.semantic_scholar import fetch_semantic_scholar_papers
from summarizer import summarize_papers
from delivery.obsidian_md import save_papers_to_obsidian
from delivery.telegram_sender import send_digest_to_telegram, send_error_to_telegram


def deduplicate(papers: list[dict]) -> list[dict]:
    """제목 기반 중복 제거"""
    seen = set()
    unique = []
    for p in papers:
        # 제목 정규화 (소문자, 공백 제거)
        key = p["title"].lower().strip().replace(" ", "")
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    """메인 파이프라인"""
    start_time = datetime.now()
    print(f"{'=' * 60}")
    print(f"📚 Daily Paper Digest — {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}")

    try:
        # ================================================
        # Step 1: 논문 수집
        # ================================================
        print("\n🔍 Step 1: 논문 수집 중...")

        arxiv_papers = fetch_arxiv_papers()
        s2_papers = fetch_semantic_scholar_papers()

        all_papers = deduplicate(arxiv_papers + s2_papers)
        print(f"📊 총 {len(all_papers)}편 (arXiv: {len(arxiv_papers)}, S2: {len(s2_papers)}, 중복 제거 후)")

        if not all_papers:
            print("📭 수집된 논문이 없습니다")
            send_digest_to_telegram([])
            return

        # ================================================
        # Step 2: Claude API로 요약 + 관련성 스코어링
        # ================================================
        print("\n🤖 Step 2: Claude API로 요약 생성 중...")

        scored_papers = summarize_papers(all_papers)
        print(f"✅ 관련성 있는 논문: {len(scored_papers)}편")

        # ================================================
        # Step 3: Obsidian vault에 마크다운 저장
        # ================================================
        print("\n📝 Step 3: Obsidian vault에 저장 중...")

        created_files = save_papers_to_obsidian(scored_papers)
        print(f"💾 {len(created_files)}개 파일 생성 완료")

        # ================================================
        # Step 4: Telegram으로 핸드폰 알림
        # ================================================
        print("\n📱 Step 4: Telegram 알림 전송 중...")

        telegram_ok = send_digest_to_telegram(scored_papers)
        if telegram_ok:
            print("✅ Telegram 전송 성공")
        else:
            print("⚠️ Telegram 전송 실패 (키 확인 필요)")

        # ================================================
        # 완료
        # ================================================
        elapsed = (datetime.now() - start_time).seconds
        print(f"\n{'=' * 60}")
        print(f"🎉 완료! ({elapsed}초 소요)")
        print(f"   - 수집: {len(all_papers)}편")
        print(f"   - 관련: {len(scored_papers)}편")
        print(f"   - 파일: {len(created_files)}개")
        print(f"{'=' * 60}")

    except Exception as e:
        error_msg = f"Error in daily_digest: {str(e)}\n{traceback.format_exc()}"
        print(f"\n❌ {error_msg}")

        # 에러도 Telegram으로 알림
        try:
            send_error_to_telegram(str(e))
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
