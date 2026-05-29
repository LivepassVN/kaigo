# kaigo 家族通知リレー

DevKit の `kaigo_family.json` から Webhook POST を受け、家族向けチャネルに転送します。

**LINE Notify は 2025-03-31 終了。** LINE 通知は [Messaging API](https://developers.line.biz/ja/docs/messaging-api/) を使用してください。

**チャネル設定詳細:** [docs/notify-channels.md](../../docs/notify-channels.md)

**ホスティング:**

| 方法 | 用途 | ドキュメント |
|------|------|-------------|
| **ngrok** | 開発・検証 | [docs/hosting-ngrok.md](../../docs/hosting-ngrok.md) |
| **Railway** | 本番・URL 固定 | [docs/hosting-railway.md](../../docs/hosting-railway.md) |

## セットアップ（ローカル）

```bash
cd tools/family_relay
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export KAIGO_WEBHOOK_SECRET=change-me-long-random-string

# いずれか1つ以上（複数可）
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
# export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
# export LINE_CHANNEL_ACCESS_TOKEN=...
# export LINE_TO_USER_ID=U...

python app.py
```

`kaigo_family.json` の `webhook_url` に公開 URL を設定:

```json
{
  "enabled": true,
  "consent_given": true,
  "webhook_url": "https://your-server.example.com/kaigo/notify",
  "webhook_secret": "change-me-long-random-string"
}
```

## エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/health` | 死活確認 + 有効チャネル一覧 |
| POST | `/kaigo/notify` | DevKit からの通知 JSON |

## ローカルテスト

```bash
curl -X POST http://127.0.0.1:8080/kaigo/notify \
  -H "Content-Type: application/json" \
  -H "X-Kaigo-Secret: change-me-long-random-string" \
  -d '{"event":"test","resident_label":"利用者","message":"テスト"}'
```

DevKit 側では「**通知テスト**」または「**家族通知**」で確認。
