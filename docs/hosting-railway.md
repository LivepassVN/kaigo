# Railway で kaigo 家族通知リレーを公開する

## Railway とは

**Railway**（[railway.app](https://railway.app/)）は、小さな Web アプリを **サーバを自分で立てなくても** インターネット公開できる **PaaS**（Platform as a Service）です。

| 比喩 | 説明 |
|------|------|
| レンタル厨房 | キッチン（サーバ）・ガス・水道は Railway が用意。あなたは `app.py` を置くだけ |
| Heroku 系 | 昔よく使われた Heroku に近い。GitHub 連携 → 自動デプロイ |

**kaigo で使う理由:** DevKit から **HTTPS の URL** に POST する必要がある。自宅 PC を 24 時間起動しなくてよい。

**料金:** 無料クレジットあり（月数ドル程度）。家族通知程度なら **ほぼ無料〜数百円/月** で収まることが多い。常時起動の VPS より手軽。

**他の選択肢（参考）**

| サービス | 特徴 |
|---------|------|
| **Railway** | 手軽・HTTPS 自動・GitHub 連携 |
| **Render** | Railway に似た無料枠あり |
| **Cloudflare Tunnel** | 自宅 PC で `app.py` を動かし Tunnel で公開（無料だが PC 常時起動） |
| **ngrok** | 動作確認用。URL が変わるので本番向きではない |
| **VPS（さくら等）** | 月固定・自由度大・設定はやや重い |

**通知チャネル:** [notify-channels.md](notify-channels.md) — LINE Notify は終了。Slack / Discord / LINE Messaging API を使用。

---

## 前提

1. GitHub アカウント（リポジトリ `kaigo` を push 済み）
2. 通知チャネル（いずれか）— 手順は [notify-channels.md](notify-channels.md)
   - **Slack** Incoming Webhook（**最も手軽・推奨**）
   - **Discord** Webhook
   - **LINE Messaging API**（LINE Notify の後継。公式アカウント設定が必要）
3. OpenHome Dashboard で `kaigo_family.json` を編集できること

> **LINE Notify**（notify-bot.line.me）は **2025-03-31 終了**。新規発行不可。

---

## 手順 1 — Railway アカウント

1. [railway.app](https://railway.app/) → **Login with GitHub**
2. 初回はクレジットカード登録を求められることがある（無料枠超過防止用）

---

## 手順 2 — プロジェクト作成

1. **New Project** → **Deploy from GitHub repo**
2. リポジトリ `kaigo` を選択（未連携なら GitHub 連携を許可）
3. デプロイ後、サービスを開く → **Settings**
4. **Root Directory** を次に設定:

```
tools/family_relay
```

5. **Save** → **Redeploy**

Railway が `Procfile` を読み、`gunicorn` で Flask を起動します。

---

## 手順 3 — 環境変数

サービス → **Variables** に追加:

| 変数名 | 値 | 必須 |
|--------|-----|------|
| `KAIGO_WEBHOOK_SECRET` | 長いランダム文字列 | 推奨 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook | Slack 使う場合 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook | Discord 使う場合 |
| `LINE_CHANNEL_ACCESS_TOKEN` | Messaging API 長期トークン | LINE 使う場合 |
| `LINE_TO_USER_ID` | 通知先 userId | LINE 使う場合 |

**いずれか1つ以上** 設定。詳細: [notify-channels.md](notify-channels.md)

---

## 手順 4 — 公開 URL を取得

1. サービス → **Settings** → **Networking** → **Generate Domain**
2. 例: `kaigo-relay-production.up.railway.app`
3. Webhook URL は:

```
https://kaigo-relay-production.up.railway.app/kaigo/notify
```

### 動作確認

```bash
curl https://kaigo-relay-production.up.railway.app/health
# → {"ok":true,"service":"kaigo-family-relay"}

curl -X POST https://kaigo-relay-production.up.railway.app/kaigo/notify \
  -H "Content-Type: application/json" \
  -H "X-Kaigo-Secret: （手順3で設定した値）" \
  -d '{"event":"test","resident_label":"利用者","message":"Railwayテスト"}'
```

LINE / Slack に届けば OK。

---

## 手順 5 — DevKit（OpenHome）側

Dashboard のファイル `kaigo_family.json`:

```json
{
  "enabled": true,
  "consent_given": true,
  "resident_label": "田中さん",
  "webhook_url": "https://kaigo-relay-production.up.railway.app/kaigo/notify",
  "webhook_secret": "（Railway の KAIGO_WEBHOOK_SECRET と同じ値）",
  "notify_on_emergency": true,
  "notify_daily_summary": true,
  "daily_summary_time": "21:00"
}
```

1. `main.py` + `family_notify.py` を最新にアップロード
2. **Sync Abilities**
3. 「**通知テスト**」で DevKit → Railway → LINE の経路を確認

---

## トラブル

| 症状 | 対処 |
|------|------|
| 502 / Application failed | Railway の **Deploy Logs** を確認。Root Directory が `tools/family_relay` か |
| 401 unauthorized | `webhook_secret` と `X-Kaigo-Secret`（Railway 側 `KAIGO_WEBHOOK_SECRET`）が一致しているか |
| curl は OK、DevKit だけ失敗 | `enabled` + `consent_given` が true か、DevKit がインターネット接続されているか |
| LINE に届かない | [notify-channels.md](notify-channels.md) の Messaging API 手順。友だち追加・userId 設定を確認 |

---

## ローカルで先に試す（Railway の前）

```bash
cd tools/family_relay
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export KAIGO_WEBHOOK_SECRET=test-secret
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
python app.py
```

別ターミナルで `curl http://127.0.0.1:8080/health` → 問題なければ Railway へ。

---

## セキュリティメモ

- `KAIGO_WEBHOOK_SECRET` は推測困難な長い文字列にする
- LINE トークンは **Railway Variables のみ**。GitHub に commit しない
- 利用者・家族の **同意** 後に `consent_given: true` にする（[privacy.md](../../docs/privacy.md)）
