# kaigo_core

Phase 1 の中核 Skill + Background Daemon。

## 機能

### 生活支援
- 日付・曜日・時刻の案内
- **天気・気温**（Open-Meteo / `kaigo_location.json`）
- 服薬・食事・水分リマインダー（background）

### 対話（傾聴）
- **傾聴チャット** — `kaigo_persona.md` と直近エピソードを文脈に、TTS 向けひらがなで応答
- **話題提案** — 挨拶時・沈黙時にやさしい質問を1つ
- **思い出の想起** — 「覚えてる？」で `kaigo_episodes.jsonl` を要約
- **思い出の記録** — 「思い出を記録」でエピソード追記
- **もう一度** — 直前の発話をリピート
- **お別れ** — 「おやすみ」等で穏やかに終了

### その他
- 緊急キーワード → 落ち着いた応答（119 / 家族連絡を促す）
- `kaigo_persona.md` の初期化・呼び名更新

> **家族通知（Phase 2）** — 後回し。`family_notify.py` はリポジトリに残置。

## OpenHome への登録

1. [app.openhome.com](https://app.openhome.com/) → **Create → Ability**
2. **kaigo_core** — `main.py` を Skill としてアップロード
3. `background.py` を Background Daemon に登録
4. **Installed Abilities** → **Enabled ON** / **Agent Ability ON**
5. 推奨トリガー:

| カテゴリ | トリガー語 |
|---------|-----------|
| 起動 | `かいご` |
| 生活 | `今日`, `お薬`, `天気`, `てんき`, `リマインダー` |
| **対話** | `話したい`, `退屈`, `寂しい`, `覚えてる`, `思い出` |
| 緊急 | `助けて` |

6. Agent（kaigo）に Ability を割り当て → **Sync Abilities**

## 対話の使い方

| 言い方 | 動作 |
|--------|------|
| `かいご` | 時間帯の挨拶 + 呼び名 + 話題提案 |
| `かいご、きょうはマグロが届いた` | 傾聴応答（エピソードに記録） |
| `話したい` | 「なにかお話しください」→ 傾聴 |
| `覚えてる？` | 最近の会話記録を要約 |
| `思い出を記録` | 思い出を聞いて JSONL に保存 |
| `もう一度` | 直前の発話をリピート |
| `おやすみ` | お別れの挨拶 |

## 永続ファイル

| ファイル | 説明 |
|---------|------|
| `kaigo_persona.md` | 人格・呼び名（Agent 注入 + 対話文脈） |
| `kaigo_episodes.jsonl` | 会話・思い出ログ（対話の記憶） |
| `kaigo_reminders.json` | リマインダー |
| `kaigo_location.json` | 天気用位置 |

## テストフレーズ

- 「今日は何曜日？」
- 「天気」
- 「お薬の時間を教えて」
- 「話したい」
- 「覚えてる？」
- 「田中と呼んでください」
- 「助けて」

## トラブル

**Ability が発動しない** → Installed Abilities で **Enabled ON** / **Agent Ability ON** → 新規会話。

**Agent が無音** → Restart Agent → `resume_normal_flow()` 確認 → 新規会話。

詳細: [docs/deploy.md](../../docs/deploy.md)
