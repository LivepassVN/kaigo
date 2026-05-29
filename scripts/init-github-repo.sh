#!/usr/bin/env bash
# LivepassVN/kaigo を GitHub に作成して初回 push する。
# 事前: gh auth login （ブラウザで認証）
set -euo pipefail
cd "$(dirname "$0")/.."

ORG="LivepassVN"
REPO="kaigo"
REMOTE="origin"
URL="https://github.com/${ORG}/${REPO}.git"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI がありません: brew install gh"
  exit 1
fi

if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo "GitHub に未ログインです。ターミナルで実行してください:"
  echo "  gh auth login"
  exit 1
fi

if ! git diff-index --quiet HEAD -- 2>/dev/null || [ -n "$(git status --porcelain)" ]; then
  echo "未コミットの変更があります。先に commit してください。"
  git status -sb
  exit 1
fi

git remote remove "$REMOTE" 2>/dev/null || true
git remote add "$REMOTE" "$URL"

if gh repo view "${ORG}/${REPO}" >/dev/null 2>&1; then
  echo "リポジトリ ${ORG}/${REPO} は既に存在します。push のみ実行します。"
  git push -u "$REMOTE" main
else
  echo "リポジトリ ${ORG}/${REPO} を作成して push します..."
  gh repo create "${REPO}" \
    --org "$ORG" \
    --public \
    --description "認知症独居支援スピーカー（OpenHome DevKit / Phase 1）" \
    --source=. \
    --remote="$REMOTE" \
    --push
fi

echo "完了: ${URL}"
