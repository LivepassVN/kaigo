# 家族通知チャネル設定

DevKit → `family_relay` → **Slack / Discord / LINE Messaging API** のいずれか（または複数）。

## LINE Notify について（利用不可）

[LINE Notify](https://notify-bot.line.me/) は **2025年3月31日でサービス終了** 済みです。新規トークン発行も停止されています。

LINE 公式の後継は **[Messaging API](https://developers.line.biz/ja/docs/messaging-api/)** です（下記手順）。

---

## おすすめ（手軽さ順）

| チャネル | 難易度 | 家族の受け取り方 |
|---------|--------|-----------------|
| **Slack** | ★ 最も簡単 | Slack アプリ通知 |
| **Discord** | ★ 簡単 | Discord アプリ通知 |
| **LINE Messaging API** | ★★★ やや手間 | LINE アプリ（公式アカウント経由） |

---

## 1. Slack（推奨・最初のテスト向け）

1. [Slack](https://slack.com/) でワークスペース作成（無料）
2. チャンネル `#kaigo-alerts` 等を作成
3. チャンネル → **Integrations** → **Incoming Webhooks** → URL を発行
4. リレーサーバに設定:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T.../B.../..."
```

家族を Slack ワークスペースに招待すれば、スマホにプッシュ通知が届きます。

---

## 2. Discord

1. Discord サーバを作成
2. チャンネル設定 → **連携サービス** → **ウェブフック** → 新しいウェブフック
3. URL をコピー:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

---

## 3. LINE Messaging API（LINE アプリで受け取りたい場合）

LINE Notify の代替。無料枠で月一定数まで送信可能（[Messaging API の料金](https://developers.line.biz/ja/docs/messaging-api/pricing/)）。

### 3.1 LINE Developers でチャネル作成

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. **プロバイダー** を作成
3. **新規チャネル** → **Messaging API** を選択
4. LINE Official Account（公式アカウント）が作成される

### 3.2 トークン取得

1. チャネル → **Messaging API** タブ
2. **Channel access token（長期）** を発行 → コピー

```bash
export LINE_CHANNEL_ACCESS_TOKEN="（発行したトークン）"
```

### 3.3 家族の userId を取得

通知先の家族メンバーが **公式アカウントを友だち追加** する必要があります。

1. チャネル → **Messaging API** → **QRコード** で友だち追加（家族のスマホ）
2. 家族が公式アカウントに何かメッセージを送る（例: `登録`）
3. **Webhook** を一時的に有効にし、受信イベントから `userId` を確認  
   または Developers Console の応答メッセージログで確認

```bash
export LINE_TO_USER_ID="Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

複数家族へ送る場合は、userId をカンマ区切りで `LINE_TO_USER_ID` に設定（relay が対応するよう拡張予定）。現状は **1 userId**。

### 3.4 応答モード

Messaging API チャネルでは **Webhook の応答モード** を **Bot** に設定。  
kaigo リレーは **Push API** で送るため、常時 Webhook サーバは不要（userId 取得時だけ Webhook が必要な場合あり）。

---

## 環境変数まとめ

| 変数 | 用途 |
|------|------|
| `KAIGO_WEBHOOK_SECRET` | DevKit ↔ リレー間の共有秘密 |
| `SLACK_WEBHOOK_URL` | Slack 通知 |
| `DISCORD_WEBHOOK_URL` | Discord 通知 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API |
| `LINE_TO_USER_ID` | 通知先の LINE userId |

---

## 動作確認

```bash
curl -s http://127.0.0.1:8080/health
# channels.slack / discord / line_messaging_api の true/false を確認

curl -X POST http://127.0.0.1:8080/kaigo/notify \
  -H "Content-Type: application/json" \
  -H "X-Kaigo-Secret: your-secret" \
  -d '{"event":"test","resident_label":"利用者","message":"チャネルテスト"}'
```

DevKit では「**通知テスト**」と声をかけて確認。

---

## 参考リンク

- [LINE Notify 提供終了のお知らせ](https://notify-bot.line.me/)
- [Messaging API ドキュメント](https://developers.line.biz/ja/docs/messaging-api/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
