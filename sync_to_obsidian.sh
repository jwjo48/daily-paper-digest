#!/usr/bin/env bash
# =============================================================
# GitHub papers/  →  iCloud Obsidian vault 단방향 동기화
# ⚠️ 반드시 당신 Mac에서 실행 (클라우드는 iCloud 접근 불가)
#
# 하는 일:
#   1. repo가 없으면 clone, 있으면 main 최신으로 pull
#   2. papers/ (테마 폴더 포함) 을 iCloud Obsidian vault로 복사
#      - 새 논문만 추가 / repo에서 갱신된 노트만 덮어씀
#      - vault에서 직접 쓴 "메모"는 보존 (--update)
#      - 어떤 파일도 삭제하지 않음
# =============================================================
set -euo pipefail

# ▼▼▼ 처음 한 번만 본인 환경에 맞게 수정 ▼▼▼
VAULT_NAME="Obsidian"          # 실제 vault 이름으로 변경
SUBFOLDER="daily-papers"       # vault 안에 논문을 넣을 폴더
REPO_DIR="$HOME/daily-paper-digest"   # Mac에 repo를 둘 위치
REPO_URL="https://github.com/jwjo48/daily-paper-digest.git"
# ▲▲▲ vault 이름 확인:  ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/  ▲▲▲

ICLOUD_BASE="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
DEST="$ICLOUD_BASE/$VAULT_NAME/$SUBFOLDER"

# 1. repo 준비
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "📥 repo가 없어 clone합니다 → $REPO_DIR"
  git clone "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"
echo "🔄 main 최신 가져오는 중..."
git fetch origin main --quiet
git checkout main --quiet 2>/dev/null || git checkout -b main origin/main --quiet
git reset --hard origin/main --quiet   # 로컬 동기화 전용 클론이므로 항상 origin/main에 맞춤

# 2. vault로 복사
if [ ! -d "$ICLOUD_BASE/$VAULT_NAME" ]; then
  echo "❌ vault를 찾을 수 없습니다: $ICLOUD_BASE/$VAULT_NAME"
  echo "   VAULT_NAME을 확인하세요. 사용 가능한 vault 목록:"
  ls "$ICLOUD_BASE" 2>/dev/null || echo "   (iCloud Obsidian 폴더가 없습니다)"
  exit 1
fi

mkdir -p "$DEST"
rsync -av --update --exclude='.gitkeep' "$REPO_DIR/papers/" "$DEST/"

echo "✅ 동기화 완료 → $DEST"
