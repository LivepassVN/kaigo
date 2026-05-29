#!/usr/bin/env bash
# OpenHome DevKit ターミナルオンボードの対話ヘルパー
# 詳細: docs/setup-devkit-camera.md
# 公式: https://docs.openhome.com/devkit/devkit-setup-terminal.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT="${OPENHOME_CLIENT_PATH:-${SCRIPT_DIR}/openhome_client.py}"

echo "=== OpenHome DevKit ターミナルオンボード ==="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 が見つかりません。Python 3.8 以上をインストールしてください。"
  exit 1
fi

if ! python3 -c "import bleak" 2>/dev/null; then
  echo "bleak をインストールします..."
  pip install bleak
fi

if [[ ! -f "${CLIENT}" ]]; then
  echo "openhome_client.py が見つかりません: ${CLIENT}"
  echo ""
  echo "次の手順でダウンロードしてください:"
  echo "  1. https://docs.openhome.com/devkit/devkit-setup-terminal.md を開く"
  echo "  2. openhome_client.py の Download リンクから保存"
  echo "  3. 保存先を指定して再実行:"
  echo "     OPENHOME_CLIENT_PATH=/path/to/openhome_client.py bash scripts/onboard-terminal.sh"
  echo ""
  exit 1
fi

echo "前提:"
echo "  - DevKit の電源が入っている"
echo "  - この PC の Bluetooth が ON"
echo "  - OpenHome API キーを用意（https://app.openhome.com/dashboard/settings）"
echo ""
echo "openhome_client.py を起動します。メニューで次の順に実行してください:"
echo ""
echo "  1 → Scan for openhome device"
echo "  2 → Connect to device"
echo "  3 → Request WiFi scan"
echo "  4 → Display WiFi networks"
echo "  5 → Connect to a WiFi network"
echo "  6 → Read WiFi status（接続確認）"
echo " 10 → Set API key"
echo ""
read -r -p "Enter で openhome_client.py を起動... " _

exec python3 "${CLIENT}"
