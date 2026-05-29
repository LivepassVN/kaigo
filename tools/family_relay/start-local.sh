#!/usr/bin/env bash
# リレーサーバをローカル起動（ngrok は別ターミナルで: ngrok http 8080）
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

# shellcheck disable=SC1091
source .venv/bin/activate

: "${KAIGO_WEBHOOK_SECRET:=dev-secret-change-me}"
export KAIGO_WEBHOOK_SECRET

echo "=== kaigo family relay ==="
echo "KAIGO_WEBHOOK_SECRET=$KAIGO_WEBHOOK_SECRET"
echo ""
echo "別ターミナルで:  ngrok http 8080"
echo "手順: docs/hosting-ngrok.md"
echo ""

exec python app.py
