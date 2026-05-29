# kaigo データスキーマ（Phase 1）

仏壇 AI 転用を見据えた永続データ形式。OpenHome の `write_file` / `read_file`（`in_ability_directory=False`）で保存する。

## ファイル一覧

| ファイル | 形式 | 書き手 | Agent 注入 |
|---------|------|--------|-----------|
| `kaigo_persona.md` | Markdown | kaigo_core | ○（60–90秒周期） |
| `kaigo_reminders.json` | JSON | kaigo_core | × |
| `kaigo_location.json` | JSON | kaigo_core | × |
| `kaigo_episodes.jsonl` | JSONL | kaigo_core, kaigo_journal, kaigo_vision | × |
| `kaigo_daily_YYYY-MM-DD.json` | JSON | kaigo_journal | × |
| `kaigo_family.json` | JSON | kaigo_core | × |
| `kaigo_home_state.md` | Markdown | Phase 3 予約 | ○（将来） |

予約: `device_events[]` は Phase 3 IoT 用（`kaigo_home_state.md` または日次 JSON 内）。

---

## kaigo_location.json

天気 API（Open-Meteo）用の位置。Skill 初回起動時にデフォルト（江戸川区）を書き込む。

```json
{
  "label": "えどがわく",
  "latitude": 35.7064,
  "longitude": 139.8683,
  "name": "東京都江戸川区"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `label` | string | 音声読み上げ用（ひらがな推奨） |
| `latitude` | number | WGS84 緯度 |
| `longitude` | number | WGS84 経度 |
| `name` | string | 表示用（任意） |

---

## kaigo_persona.md

利用者の呼び名・好み・口調。200 語以内を目安。

```markdown
# kaigo_persona

## 呼び名
（例: 田中さん）

## 好きな話題
- 庭の話
- 孫の話

## 避ける話題
- 詳しい病名の話

## 口調メモ
- ゆっくり、敬語
```

---

## kaigo_reminders.json

```json
{
  "reminders": [
    {
      "id": "med_morning",
      "label": "朝のお薬",
      "time": "08:00",
      "days": [0, 1, 2, 3, 4, 5, 6],
      "enabled": true,
      "last_fired_date": null
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | string | 一意 ID |
| `label` | string | 音声で読み上げる文言 |
| `time` | string | `HH:MM`（24h、DevKit タイムゾーン） |
| `days` | int[] | 0=月 … 6=日 |
| `enabled` | bool | 有効 / 無効 |
| `last_fired_date` | string \| null | 最終発火日 `YYYY-MM-DD`（background が更新） |

---

## kaigo_episodes.jsonl

1 行 1 エピソード（追記のみ）。

```json
{"date":"2026-05-28","trigger":"voice","transcript_snippet":"今日は孫が来た","image_path":null,"mood":null}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | string | `YYYY-MM-DD` |
| `trigger` | string | `voice` / `reminder` / `photo` 等 |
| `transcript_snippet` | string | 会話抜粋（短く） |
| `image_path` | string \| null | kaigo_vision 保存パス |
| `mood` | string \| null | Phase 1+ |

---

## kaigo_family.json（Phase 2 — 家族通知）

**オプトイン必須。** `enabled` と `consent_given` が両方 `true` のときだけ Webhook を送信する。

テンプレート: [config/kaigo_family.template.json](../config/kaigo_family.template.json)

```json
{
  "enabled": true,
  "consent_given": true,
  "resident_label": "田中さん",
  "webhook_url": "https://your-server.example.com/kaigo/notify",
  "webhook_secret": "change-me-long-random-string",
  "notify_on_emergency": true,
  "notify_daily_summary": true,
  "daily_summary_time": "21:00",
  "last_daily_sent_date": null
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `enabled` | bool | 通知機能のマスタースイッチ |
| `consent_given` | bool | 利用者・家族の同意（両方 true で送信） |
| `resident_label` | string | 通知文に載せる呼び名 |
| `webhook_url` | string | POST 先（リレーサーバ推奨） |
| `webhook_secret` | string | `X-Kaigo-Secret` ヘッダー |
| `notify_on_emergency` | bool | 「助けて」等で即時通知 |
| `notify_daily_summary` | bool | 毎日定時に日次サマリー |
| `daily_summary_time` | string | `HH:MM`（DevKit TZ） |
| `last_daily_sent_date` | string \| null | 最終日次送信日（background が更新） |

送信イベント: `emergency`, `daily_summary`, `test`（接続確認）

---

## kaigo_daily_YYYY-MM-DD.json

```json
{
  "date": "2026-05-28",
  "summary": "朝の挨拶と孫の話。服薬リマインダーに応答。",
  "highlights": ["孫が来る予定"],
  "device_events": []
}
```

`device_events[]` — Phase 3 まで空配列で予約:

```json
{"ts":"2026-05-28T14:00:00+09:00","source":"door","event":"opened"}
```

---

## kaigo_home_state.md（Phase 3 予約）

IoT センサーの最新状態を Agent に注入する想定。Phase 1 では **テンプレートのみ** 配置し、Ability は書き込まない。ファイル例: [config/kaigo_home_state.template.md](../config/kaigo_home_state.template.md)

```markdown
# kaigo_home_state

## 最終更新
（未使用 — Phase 3）

## ドア
- 状態: unknown

## 押しボタン
- 最終押下: —

## 温湿度
- 温度: —
- 湿度: —

## メモ
- device_events は kaigo_daily_*.json の device_events[] にも追記可能
```

---

## エクスポート（オフライン）

DevKit / Dashboard から以下をまとめてコピー:

1. `kaigo_persona.md`
2. `kaigo_reminders.json`
3. `kaigo_episodes.jsonl`
4. `kaigo_daily_*.json`
5. `kaigo_snapshots/`（画像、kaigo_vision）

ZIP または rsync で仏壇 AI 側へ渡す想定。
