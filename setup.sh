#!/bin/bash
# =============================================================
# Daily Paper Digest — 초기 설정 스크립트
# 이 스크립트를 한 번만 실행하면 됩니다.
# =============================================================

set -e

echo "📚 Daily Paper Digest 설정 시작"
echo "================================="
echo ""

# 1. API 키 입력
echo "🔑 API 키를 입력해주세요 (나중에 변경 가능)"
echo ""

read -p "Anthropic API Key (sk-ant-...): " ANTHROPIC_KEY
read -p "Telegram Bot Token: " TG_TOKEN
read -p "Telegram Chat ID: " TG_CHAT
read -p "Semantic Scholar API Key (빈칸이면 건너뜀): " S2_KEY

# 2. .env 파일 생성
cat > .env << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
TELEGRAM_BOT_TOKEN=${TG_TOKEN}
TELEGRAM_CHAT_ID=${TG_CHAT}
S2_API_KEY=${S2_KEY}
EOF

echo ""
echo "✅ .env 파일 생성 완료"

# 3. Obsidian vault 이름 확인
echo ""
echo "📁 iCloud Obsidian vault 확인 중..."
ICLOUD_BASE="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

if [ -d "$ICLOUD_BASE" ]; then
    echo "발견된 vault들:"
    ls -1 "$ICLOUD_BASE" 2>/dev/null | while read vault; do
        echo "  → $vault"
    done
    echo ""
    read -p "사용할 vault 이름을 입력하세요: " VAULT_NAME

    # config.py 업데이트
    if [ -n "$VAULT_NAME" ]; then
        sed -i '' "s/OBSIDIAN_VAULT_NAME = \"Research\"/OBSIDIAN_VAULT_NAME = \"${VAULT_NAME}\"/" config.py
        echo "✅ config.py의 vault 이름을 '${VAULT_NAME}'으로 변경"
    fi
else
    echo "⚠️  iCloud Obsidian 경로를 찾을 수 없습니다"
    echo "   Obsidian에서 iCloud 동기화가 활성화되어 있는지 확인하세요"
    echo "   나중에 config.py에서 OBSIDIAN_VAULT_NAME을 직접 수정할 수 있습니다"
fi

# 4. 테스트 실행
echo ""
read -p "테스트 실행할까요? (y/n): " RUN_TEST

if [ "$RUN_TEST" = "y" ] || [ "$RUN_TEST" = "Y" ]; then
    echo ""
    echo "🚀 테스트 실행 중..."
    # .env 파일에서 환경변수 로드
    export $(cat .env | grep -v '^#' | xargs)
    python3 daily_digest.py
else
    echo ""
    echo "나중에 실행하려면:"
    echo "  export \$(cat .env | grep -v '^#' | xargs) && python3 daily_digest.py"
fi

# 5. GitHub 설정 안내
echo ""
echo "================================="
echo "📋 다음 단계: GitHub에 배포"
echo "================================="
echo ""
echo "1. GitHub repo 생성:"
echo "   git init && git add . && git commit -m 'init'"
echo "   gh repo create daily-paper-digest --private --push"
echo ""
echo "2. GitHub Secrets 등록 (Settings → Secrets → Actions):"
echo "   ANTHROPIC_API_KEY"
echo "   TELEGRAM_BOT_TOKEN"
echo "   TELEGRAM_CHAT_ID"
echo "   S2_API_KEY"
echo ""
echo "3. GitHub Actions가 매일 평일 7AM(EST)에 자동 실행됩니다"
echo ""
echo "🎉 설정 완료!"
