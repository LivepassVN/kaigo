# OpenHome Ability のデプロイ

## 1. kaigo_core（最優先）

1. [app.openhome.com](https://app.openhome.com/) → **Create → Ability**
2. 名前: `kaigo_core`、Category: **Skill** → `abilities/kaigo_core/main.py` を Live Editor にコピーまたは zip アップロード
3. **Background Daemon** として `abilities/kaigo_core/background.py` を別 Ability または同一パッケージで登録（OpenHome の Background テンプレートに合わせる）
4. トリガー語を追加（**対話用も登録**）:
   - 生活: `かいご`, `今日`, `お薬`, `思い出`, `天気`, `てんき`, `リマインダー`, `助けて`
   - **対話:** `話したい`, `退屈`, `寂しい`, `覚えてる`, `もう一度`
5. Agent **kaigo** の Edit → Abilities に `kaigo_core` を追加
6. iOS アプリ → **Sync Abilities** → DevKit で声テスト

### 天気だけ別 Skill にする場合（推奨・設定が簡単）

1. `abilities/kaigo_weather/main.py` を Skill として登録
2. トリガー: `天気`, `てんき`, `今日の天気`
3. Agent **kaigo** の Abilities に `kaigo_weather` を追加 → Sync Abilities  
   （`kaigo_core` と **両方** に天気トリガーを付けないこと）

詳細: [abilities/kaigo_weather/README.md](../abilities/kaigo_weather/README.md)

## 2. kaigo_journal

Skill として `abilities/kaigo_journal/main.py` を登録。トリガー: `ジャーナル`, `今日の記録`

## 3. kaigo_vision（カメラ接続後）

- Category: **Local**
- `main.py` + `devkit_functions.py` + `requirements.txt`
- DevKit 実機でのみ動作（Live Editor ではカメラ不可）

## 4. 確認コマンド（DevKit）

```text
「今日は何曜日？」
「今日の天気は？」
「お薬の時間を教えて」
「思い出を記録したい」
```

## 5. 永続データ

Dashboard / Profile で `kaigo_persona.md` が生成・更新されているか確認（60–90 秒で Agent に注入）。

スキーマ: [data-schema.md](data-schema.md)

---

## トラブル: どのトリガー語も発動しない（最重要）

**症状:** 「天気」「お薬」「かいご」等、どの語でも Agent が **一般応答**（創作・説教）だけ返す。Ability の定型（気温・服薬時刻等）が出ない。

**スクショで確認した典型原因:** **Installed Abilities** タブで `KaigoCORE` の **Enabled が OFF（灰色）** のまま。トリガー語は登録済みでも **Ability 自体が無効** なので一切起動しません。

### 手順（Installed Abilities）

1. **MY ABILITIES** → **Installed Abilities** タブ
2. **KaigoCORE** カードで:
   - **Enabled** → **ON（オレンジ）** にする
   - **Agent Ability** → **ON** にする（会話から起動するにはこちらが必要）
   - **System Ability** は ON のままでよい
3. **MY AGENTS** → **KAIGO** → Edit → **Abilities** に `KaigoCORE` が含まれているか確認
4. iOS アプリ → **Sync Abilities**
5. 会話を **終了** → **新規会話** → 「お薬」または「天気」でテスト

**比較:** 同画面の `datetime` は **Enabled ON** → こちらだけ動く、という状態になっていることが多い。

---

## トラブル: 「天気」だけ発動しない

**症状:** Web チャットで「天気」「てんき」と入力 → Agent が「きょうのてんきはどうですか…」等の **一般応答**（Open-Meteo 未取得）

**前提:** 上記 **Enabled / Agent Ability** が ON であること。

**追加原因:** Trigger Words に `てんき`（ひらがな）が無い、`天気` だけ登録している等。

### 手順

1. [app.openhome.com](https://app.openhome.com/) → **MY ABILITIES** → `kaigo_core`（または `kaigo_weather`）を開く
2. **Trigger Words** に追加: `天気`, `てんき`, `今日の天気`
3. `main.py` がリポジトリ最新か確認 → Save
4. **MY AGENTS** → **KAIGO** → Edit → Abilities に当該 Skill が **ON** か確認
5. iOS アプリ → **Sync Abilities**
6. 会話を **終了** し **新規会話** で「天気」とだけ入力

### 成功時の応答例

「きょうの**えどがわく**のてんきは、くもりです。きおんはにじゅうごどくらいです。」

### まだダメなとき

| 確認 | 内容 |
|------|------|
| トリガーの表記 | `てんき`（ひらがな）と `天気`（漢字）は **別**。両方登録 |
| コード更新 | Dashboard の `main.py` を [abilities/kaigo_core/main.py](../abilities/kaigo_core/main.py) で上書き |
| 位置ファイル | 既存 `kaigo_location.json` はコード変更で自動更新されない。手動編集または削除して再作成 |

---

## トラブル: Web は喋るが DevKit スピーカーだけ無音

**Web 会話の音声 = PC のブラウザから出力。** DevKit の音声 = **Pi 側のスピーカー出力**（Bluetooth / 3.5mm / 基板直結）。Agent や Ability が壊れているわけではない。

### 切り分け

| 現象 | 意味 |
|------|------|
| Web ダッシュボードで音声が聞こえる | Agent・TTS・API キーは **正常** |
| DevKit だけ無音 | **DevKit の音声出力経路** の問題 |

### 手順 1 — Web から Bluetooth スピーカー再接続

1. [app.openhome.com](https://app.openhome.com/) → **Profile → Settings → DevKit**
2. **マイク** と **スピーカー** の両方が Connected か確認
3. スピーカーが未接続 → **Scan Bluetooth Devices** → スピーカーを選択
4. プロファイルが **a2dp-sink** か確認
5. **Restart Agent**（Web または iOS）

### 手順 2 — iOS アプリ

1. Dashboard が **Connected** か
2. **Restart DevKit**（電源 OFF → 10 秒 → ON でも可）
3. Connected Devices に **Speaker** が出るか

### 手順 3 — 物理確認（基板直結スピーカー）

音量対策で **ウレタン・テープ** を貼っていた場合、**外して** 試す（完全に音が消えていることがある）。

- 基板とスピーカーの **配線・コネクタ** が緩んでいないか
- 電源ケーブルを **抜き差し** して再起動
- スピーカー単体テスト: 同じスピーカーを **スマホ等に接続** して鳴るか

### 手順 4 — DevKit 上で Agent が動いているか

Web で会話中でも **DevKit は別セッション**。DevKit のマイクに向かって:

```
おはよう
```

iOS アプリで **Agent Toggle = ON**、**Auto Start On Power On = ON** を確認。

### 手順 5 — ソフト音量（SSH が必要）

以前うるさかった後に無音 → **ALSA 音量が 0** の可能性。SSH パスワードは [OpenHome Discord](https://discord.gg/openhome) / support@openhome.com で問い合わせ:

```bash
amixer sget Master
amixer sset Master 80%
```

### それでも無音

- OpenHome に **「Web は TTS 正常、DevKit スピーカーのみ無音」** と報告（ファームウェア版・Bluetooth か直結かを添える）
- 暫定: **音量つまみ付き Bluetooth スピーカー** を DevKit 設定からペアリング（公式推奨構成）

---

## 6. 家族通知（Phase 2 — **後回し**）

Git / リレーサーバ設定が整うまで保留。将来用ドキュメント: [notify-channels.md](notify-channels.md), [hosting-ngrok.md](hosting-ngrok.md)

---

## 7. 対話機能のテスト

Dashboard で `main.py` を更新 → Sync → **新規会話**:

| 入力 | 期待 |
|------|------|
| `かいご` | 挨拶 + 話題提案 |
| `話したい` | 「なにかお話しください」→ 傾聴応答 |
| `覚えてる？` | 最近の会話記録を要約 |
| `もう一度` | 直前の発話をリピート |
| `ジャーナル` | 日次記録（kaigo_journal） |

詳細: [abilities/kaigo_core/README.md](../abilities/kaigo_core/README.md)
