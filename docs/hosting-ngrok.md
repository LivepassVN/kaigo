# ngrok で kaigo 家族通知リレーを公開する

**開発・検証向け。** 自宅 Mac で `app.py` を動かし、ngrok が **一時的な HTTPS URL** を割り当てます。

## ngrok とは

**ngrok** は、ローカル（`localhost:8080`）を **インターネットから届く HTTPS URL** につなぐトンネルサービスです。

```
DevKit / OpenHome
    ↓ POST https://xxxx.ngrok-free.app/kaigo/notify
ngrok（クラウド）
    ↓ トンネル
自宅 Mac localhost:8080（family_relay）
    ↓
Slack / Discord / LINE Messaging API
```

> **LINE Notify**（notify-bot.line.me）は **2025-03-31 終了**。新規発行不可。

| 項目 | 内容 |
|------|------|
| 向いている用途 | **動作確認・PoC**（今の kaigo 開発段階） |
| 向いていない用途 | 24 時間本番運用（PC 常時起動・URL 変更の制約） |
| 料金 | 無料枠あり。固定 URL は有料プラン |

**Railway との違い**

| | ngrok | Railway |
|---|--------|---------|
| サーバ | 自宅 Mac | クラウド |
| PC 常時起動 | **必要** | 不要 |
| URL | 再起動で **変わる**（無料） | **固定** |
| セットアップ | 5 分 | 15 分（GitHub 連携） |

---

## 前提

- macOS（Homebrew 可）
- [ngrok アカウント](https://dashboard.ngrok.com/signup)（無料）
- 通知チャネル（**Slack 推奨**）— [notify-channels.md](notify-channels.md)

---

## 手順 1 — ngrok インストール

```bash
brew install ngrok
```

Homebrew がない場合: [ngrok.com/download](https://ngrok.com/download) から macOS 用をインストール。

---

## 手順 2 — 認証（初回のみ）

1. [dashboard.ngrok.com](https://dashboard.ngrok.com/) → **Your Authtoken** をコピー
2. ターミナルで:

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

---

## 手順 3 — リレーサーバ起動（ターミナル A）

```bash
cd /Users/tsukasa/kaigo/tools/family_relay
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export KAIGO_WEBHOOK_SECRET="$(openssl rand -hex 16)"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
# または Discord / LINE Messaging API — notify-channels.md 参照

echo "SECRET=$KAIGO_WEBHOOK_SECRET"   # 後で kaigo_family.json に使う
python app.py
```

`Running on http://0.0.0.0:8080` と出れば OK。**このターミナルは閉じない。**

---

## 手順 4 — ngrok トンネル（ターミナル B）

**新しいターミナル** を開く:

```bash
ngrok http 8080
```

表示例:

```
Forwarding   https://a1b2c3d4.ngrok-free.app -> http://localhost:8080
```

この **`https://a1b2c3d4.ngrok-free.app`** を控える。

Webhook 完全 URL:

```
https://a1b2c3d4.ngrok-free.app/kaigo/notify
```

---

## 手順 5 — 動作確認（ターミナル C）

`SECRET` は手順 3 で表示した `KAIGO_WEBHOOK_SECRET` の値。

```bash
# ヘルスチェック
curl -s https://a1b2c3d4.ngrok-free.app/health

# 通知テスト
curl -X POST https://a1b2c3d4.ngrok-free.app/kaigo/notify \
  -H "Content-Type: application/json" \
  -H "X-Kaigo-Secret: SECRET" \
  -d '{"event":"test","resident_label":"利用者","message":"ngrokテスト"}'
```

LINE / Slack に届けば OK。

---

## 手順 6 — OpenHome（DevKit）設定

Dashboard → ファイル `kaigo_family.json`:

```json
{
  "enabled": true,
  "consent_given": true,
  "resident_label": "田中さん",
  "webhook_url": "https://a1b2c3d4.ngrok-free.app/kaigo/notify",
  "webhook_secret": "手順3のKAIGO_WEBHOOK_SECRETと同じ値",
  "notify_on_emergency": true,
  "notify_daily_summary": true,
  "daily_summary_time": "21:00"
}
```

1. `kaigo_core` の `main.py` + `family_notify.py` を最新化
2. Trigger Words に **`通知テスト`** を追加
3. Installed Abilities → **Enabled ON** / **Agent Ability ON**
4. iOS → **Sync Abilities**
5. 新規会話 → 「**通知テスト**」

---

## 運用上の注意

### URL が変わる

ngrok を **止めるたび** Forwarding URL が変わります（無料プラン）。

- ngrok 再起動 → **`kaigo_family.json` の `webhook_url` を更新** → Sync Abilities
- 固定 URL が必要になったら [Railway 手順](hosting-railway.md) へ移行

### Mac を起動したままにする

ターミナル A（`python app.py`）と B（`ngrok http 8080`）の **両方** が動いている間だけ通知可能。

- Mac スリープ → 通知止まる可能性
- 開発中は **電源接続 + スリープ無効** を推奨

### ngrok Web Interface

ngrok 起動中、ブラウザで [http://127.0.0.1:4040](http://127.0.0.1:4040) を開くと **リクエスト履歴** が見える。DevKit から POST が来ているか確認できる。

---

## トラブル

| 症状 | 対処 |
|------|------|
| `curl` がタイムアウト | ターミナル A の `python app.py` が動いているか |
| 401 unauthorized | `webhook_secret` と `KAIGO_WEBHOOK_SECRET` が一致しているか |
| DevKit だけ失敗 | `enabled` + `consent_given` が true、Enabled ON、インターネット接続 |
| ngrok ERR_NGROK_3200 | authtoken 未設定 → 手順 2 |
| 通知が届かない | `curl /health` で channels が true か。Slack Webhook URL を確認 |

---

## クイック起動（2 ターミナル）

**A:**

```bash
cd /Users/tsukasa/kaigo/tools/family_relay && source .venv/bin/activate
export KAIGO_WEBHOOK_SECRET="my-dev-secret-change-me"
export SLACK_WEBHOOK_URL="..."
python app.py
```

**B:**

```bash
ngrok http 8080
```

---

## 次のステップ

ngrok で DevKit → LINE まで通ったら:

1. **Railway** に移行して URL 固定・24h 運用 → [hosting-railway.md](hosting-railway.md)
2. 緊急「**助けて**」の実通知テスト
3. 日次サマリー（21:00）の確認
