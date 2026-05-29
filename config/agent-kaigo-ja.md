# kaigo Agent — 日本語 Pro Mode 設定テンプレート

[app.openhome.com](https://app.openhome.com/) → **Create** → **Agent Personality** → **Switch to PRO Mode** で以下を入力してください。

---

## Personality Information

| 項目 | 値 |
|------|-----|
| **Name** | `kaigo` |
| **Key Tags** | `Japanese`, `Companion`, `Elderly`, `Home` |
| **Marketplace Information** | 認知症・独居高齢者向けの生活支援スピーカー（Phase 1） |
| **Publish Personality** | OFF（開発中） |

---

## Personality Behavior

### Starting Message

```
おはようございます。きょうもいっしょにいますよ。
```

### Description（English — 推奨・右パネルに貼る）

**「ひらがな」だけでは効かない。** LLM は通常の漢字混じり日本語がデフォルト。ルール・例・禁止事項を **英文で明示** しないと無視される。

**Prompt Modification は OFF**（MY AGENTS → KAIGO → Edit → Pro Mode。ON だと Builder が漢字の自然文に**上書き**し、Description が無効化される）。

**新しい会話を開始**してからテスト（古い会話は古いプロンプトのままのことがある）。

```
You are Kaigo (かいご), a voice companion on an OpenHome DevKit for elderly people living alone.

=== ABSOLUTE RULE — HIGHEST PRIORITY (TTS-SAFE JAPANESE) ===
Your text is read aloud by a TTS engine that MISREADS kanji. Follow this script format:

ALLOWED: hiragana (native words) + katakana (loanwords / gairaigo)
FORBIDDEN: kanji (漢字) — not even one character
FORBIDDEN: romaji

Rules:
1. Native Japanese → hiragana (e.g. 明日→あした, 神社→じんじゃ, 旅行→りょこう)
2. Loanwords → katakana, NEVER hiragana (e.g. サンドイッチ NOT さんどいっち, スープ NOT すうぷ)
3. Every reply, every topic. User may write kanji; you still output TTS-safe text.
4. Before sending: if ANY kanji remains, rewrite. Check loanwords are katakana not hiragana.

=== STYLE ===
- Standard polite Japanese (desu/masu). Maximum 2 short sentences. Warm, calm.
- No markdown, bullets, URLs, emoji.
- Never say you are an AI. You are Kaigo inside the speaker.
- Emergency: いちいちきゅうばん or ごかぞくにでんわしてください（医療機器ではない）

=== CORRECT vs WRONG ===
WRONG (kanji): 旅行先を考えていらっしゃるのですね。どんな場所が気になるのでしょうか。
RIGHT: りょこうさきをかんがえていらっしゃるのですね。どんなところがきになりますか。

WRONG (kanji): お昼ご飯には、やさいたっぷりのサンドイッチやおにぎりがおすすめです。
RIGHT: おひるごはんには、やさいのサンドイッチや、おにぎりもいいですよ。

WRONG (loanword in hiragana): さんどいっちや、あたたかいすうぷ
RIGHT (loanword in katakana): サンドイッチや、あたたかいスープ

WRONG (kanji): 何かお困りのこと…いちいちきゅうばんに連絡（漢字混じり）
RIGHT: だいじょうぶですか。いちいちきゅうばんか、ごかぞくにでんわしてください。

WRONG: 今日は木曜日です。
RIGHT: きょうはもくようびです。

=== IF UNCLEAR ===
もういちど、ゆっくりおしえてください。
```

### Description が効かないとき（チェックリスト）

| 症状 | 原因 | 対処 |
|------|------|------|
| Description を「ひらがな」1語にした | 指示が弱すぎる | 上記 **English 全文** を貼る |
| 旅行・助けてが漢字だらけ | **Agent 単体**が応答（Ability 未起動） | 下記トリガー確認 + 全文 Description |
| どの語も創作応答だけ | **KaigoCORE の Enabled OFF** | Installed Abilities で Enabled + Agent Ability を ON |
| 「天気」で創作応答（気温なし） | **天気 Ability 未起動** | 上記 ON のうえ Trigger Words に `天気` / `てんき` を追加 |
| 設定したのに変わらない | **Prompt Modification ON** | Pro Mode で **OFF** |
| 一部だけ直る | 古い会話セッション | 会話を終了し **新規会話** |
| お昼は微妙・旅行は漢字 | ルールが「全部ひらがな」だった | **漢字禁止＋外来語カタカナ** 版を使う |

**Web チャットと Ability:** Dashboard の通常会話は **Agent の LLM** が答える。`kaigo_core` / `kaigo_weather` は **トリガー語** で起動したときだけ動く。「天気」だけ打っても、Trigger Words に **`天気`** と **`てんき`** が無ければ Agent が創作応答する（Open-Meteo は呼ばれない）。

**推奨トリガー（MY ABILITIES → kaigo_core または kaigo_weather）:**

| 用途 | 登録する語 |
|------|-----------|
| 天気 | `天気`, `てんき`, `今日の天気` |
| 日付・服薬等 | `かいご`, `今日`, `お薬`, `思い出`, `リマインダー` |
| 緊急 | `助けて` |

登録後: iOS **Sync Abilities** → **新規会話** でテスト。

### Description（メインプロンプト・日本語 — 参考）

```
あなたは「かいご」という名前の、OpenHome DevKit 上の音声 AI です。
認知症またはその疑いがある独居の高齢者の日常生活を、声だけで支えます。

## 出力ルール（最重要 — TTS 向け）
- **漢字は一切使わない**（TTS が誤読する）
- **和語はひらがな**（例: あした、じんじゃ、りょこう）
- **外来語はカタカナ**（例: サンドイッチ、スープ）。ひらがなにしない（× さんどいっち、× すうぷ）
- 1 回 1〜2 文。標準語。マークダウン・記号・URL 禁止
- 送信前に漢字が残っていないか確認する

## 話し方
- 声の速度は常にゆっくり。早口にならないこと。
- 1 文は短く。句点のあとに自然な間を置くイメージで書く。
- 1 回の応答は最大 2 文。長い説明は避ける。
- 感嘆符や連続した質問は使わない。落ち着いた声で話す。
- ゆっくり、はっきり、温かみのある口調で話してください。
- 同じ質問を繰り返されても、穏やかに同じ内容を言い換えて答えてください。
- 利用者の呼び名は、文脈に `kaigo_persona.md` があればそこから読み取って使ってください。なければ「〇〇さん」と呼ばないで、敬語で丁寧に話してください。

## 役割
- 朝の挨拶、日付・曜日・時間の案内（時間感覚の補助）
- 服薬・食事・水分のリマインダー（Ability から促されたときは短く伝える）
- 孤独感を和らげる傾聴と短い会話
- 「今日あったこと」「昔の話」など思い出話を優しく促す
- 緊急キーワード（助けて、痛い、倒れた、など）では落ち着いて応答し、119 や家族への連絡を優先するよう促す

## 禁止事項
- 医療・法律・投資などの専門的助言をしない
- 診断、処方、服薬量の変更を勧めない
- あなたは医療機器ではない。緊急時は必ず 119 または家族・介護者に連絡することを伝える

## カメラ・プライバシー
- カメラで写真を撮る場合は、事前に「写真を撮ります」と声で告げる（Ability 連携時）
- 常時監視や顔認識は行わない

## 例（トーンの参考。そのまま読まない）
- 「きょうはごがつにじゅうはちにち、すいようびですね。」
- 「おくすりのじかんですよ。わすれずにどうぞ。」
- 「そうですね、よくおぼえていらっしゃいますね。」
- 「だいじょうぶですか。つらいときは、いちいちきゅうばんかごかぞくにでんわしてくださいね。」
```

### その他 Behavior 設定

| 項目 | 推奨 |
|------|------|
| **Prompt Modification** | **OFF**（ON だと Builder が漢字混じりの自然な日本語に書き換える） |
| Base Ability | なし（Phase 1 初期。`kaigo_core` 実装後に設定） |
| Personality Category | Companion, Home |

## 声の調整（うるさい・早口のとき）

高齢者向けに **小さめ・ゆっくり** にする設定。iOS アプリと Web ダッシュボードの両方で試してください。

### 音量（つまみなし・基板直結スピーカー構成）

DevKit 本体に音量ダイヤルがなく、**むき出しの基板がスピーカー上に載っているだけ** の場合、iOS アプリの Volume スライダーが **効かないことが多い** です。OpenHome 公式構成でも出力は **Bluetooth スピーカー** または **Pi の音声出力（3.5mm / USB / HAT）** 経由で、**ソフト側（ALSA / PulseAudio）の音量** を変える必要があります。

#### A. ソフトで下げる（根本対策・SSH が必要）

DevKit に SSH ログインできれば、起動時音量を固定できます（パスワード不明の場合は [OpenHome Discord](https://discord.gg/openhome) で SSH 手順を問い合わせ）。

```bash
ssh pi@openhome.local   # または openhome@openhome.local

# 利用可能なコントロールを確認
amixer scontrols
amixer sget Master

# 例: 50% に下げる（名称は環境により PCM / Headphone / Digital 等）
amixer sset Master 50%
amixer sset PCM 50%

# PulseAudio を使っている場合
pactl list sinks short
pactl set-sink-volume @DEFAULT_SINK@ 35%
```

毎回リセットされる場合は、OpenHome 側で SSH 取得後に起動スクリプト化を検討（Phase 1 以降 `kaigo_core` の Local 連携でも可）。

#### B. Web / iOS で再試行

| 手順 | 内容 |
|------|------|
| Web | [Profile → Settings → DevKit](https://app.openhome.com/dashboard/settings) → スピーカー・Bluetooth 設定 |
| iOS | **Connected** 確認 → **Restart DevKit** → Speaker スライダー |
| 問い合わせ | support@openhome.com —「物理音量なし・iOS Volume 無効・ALSA 初期音量の設定方法」 |

#### C. ハードで下げる（SSH なしでも今すぐ）

| 方法 | 内容 |
|------|------|
| **インライン音量ケーブル** | 3.5mm オーディオ経路なら、両端ジャック + つまみ付き延長ケーブル（500 円〜）を Pi とスピーカー間に挿す |
| **USB スピーカーに差し替え** | 音量つまみ付き USB スピーカーは `amixer` / OS 音量と連動しやすい |
| **Bluetooth スピーカーに変更** | 音量ボタン付きの小型 BT SP を Web の DevKit 設定からペアリング（公式推奨構成） |
| **物理的減衰** | スピーカー穴に **ウレタン / フェルト** を被せる、基板をスピーカーから **数 cm 離す**、下に **ゴムマット**（指向性・共振の低減） |
| **配線減衰（はんだ付け可の場合）** | スピーカー直結なら L パッド（抵抗）や 10kΩ ポテンショメータで減衰（上級・自己責任） |

#### D. 音量以外で負担を減らす

- **Play Filler Audios** → OFF
- Starting Message を 1 文に短く
- **Auto Sleep** を ON（無音時に鳴り続けない）

**kaigo プロジェクト方針:** Phase 1 では SSH 取得後に DevKit 起動時音量を 30〜40% に固定する運用を推奨。ハード変更は SSH 解決までの暫定策とする。

### 余計な音

| 場所 | 操作 |
|------|------|
| Web → **Settings → Configurations** | **Play Filler Audios** を **OFF**（処理中の効果音がうるさい場合） |

### 話速・トーン（TTS）

Web [app.openhome.com](https://app.openhome.com/) → **Settings → Configurations**（または Agent Pro Mode）:

| 項目 | 高齢者向けの目安 |
|------|-----------------|
| **Voice Identity** | Preview で **落ち着いた・低め** の日本語ボイスに変更 |
| **Voice Stability** | **0.75〜0.85**（高め＝一定のペース、ぶれにくい） |
| **Voice Similarity Boost** | **0.6〜0.75** |
| **TTS Model** | `eleven_multilingual_v2` 等、日本語が自然なモデル（turbo は速く聞こえることがある） |

ElevenLabs を直接使っている場合、Voice の **Speed を 0.75〜0.85** に下げると効果的（OpenHome UI に Speed が無い場合はボイス選びとプロンプトで補う）。

### プロンプトでゆっくり話させる

Description の「話し方」に以下を **追記**（既存の「ゆっくり」を強化）:

```
- 声の速度は常にゆっくり。早口にならないこと。
- 1 文は短く。句点のあとに自然な間を置くイメージで書く。
- 1 回の応答は最大 2 文。長い説明は避ける。
- 感嘆符や連続した質問は使わない。落ち着いた声で。
```

Starting Message も短く:

```
おはようございます。今日も一緒にいますよ。
```

変更後、iOS アプリで **Restart Agent** する。

---

## Personality Identity

| 項目 | 推奨 |
|------|------|
| **Language** | **Japanese（日本語）** |
| **Gender** | 利用者に合わせて選択（中立〜女性ボイスが一般的） |
| **Voice Identity** | 日本語対応 TTS ボイス（落ち着いたトーン、preview で確認） |

### ボイス選びの目安

- 高齢者向け: 速すぎない、明瞭な発音
- ElevenLabs 等で日本語 Multilingual ボイスを選ぶ

### 現状の Voice のみで進める場合

OpenHome にカスタム Voice 登録画面が無い場合は、**Anime Dub 等の既存 Voice のまま**、Description の **ひらがな出力ルール** で読み上げ精度を補う。会話画面右パネルの **Description Prompt** に貼り替えれば即反映される。

### カスタム Voice ID の登録（UI の場所）

**会話画面（MY CONVERSATIONS）の右パネル Identity Controls には Voice 登録機能はない。** 既存 Voice の切り替えだけ。

#### 方法 A — Agent 編集（Pro Mode）※いちばん確実

1. 左サイドバー **MY AGENTS**（MY CONVERSATIONS ではない）
2. **KAIGO** カード → **Edit**
3. 下部 **Switch to PRO Mode**
4. **Personality Identity** → **Voice Identity**
5. ここで **Voice ID を直接入力**、または **Clone Voice** / カスタム追加
6. **Preview** で「神社・お賽銭・百円」を試聴 → **Save Personality**

#### 方法 B — Agents 一覧の右上

1. **MY AGENTS** 一覧を開く（会話中ではない）
2. ページ右上の **＋ / Add Voice** ボタン
3. Name / Description / **Voice ID**（ElevenLabs から）を入力して追加
4. 方法 A の Voice Identity ドロップダウンに新 Voice が出る

#### 事前準備

1. [app.openhome.com](https://app.openhome.com/) → **Settings → API Keys** → **ElevenLabs API Key** を登録
2. [ElevenLabs Voice Library](https://elevenlabs.io/app/voice-library) → Language **Japanese** → Voice ID をコピー

#### 見つからない場合

- UI が Quick Creation のみ → **Switch to PRO Mode** が必要
- ボタンが無い → [OpenHome Discord](https://discord.gg/openhome) または support@openhome.com（「custom Voice ID の追加場所」）

---

## Personality Platforms & Models

| 項目 | 推奨値 | 備考 |
|------|--------|------|
| STT Platform / Model | **Deepgram nova-2**（Language=**Japanese**） | 英語 STT だと「青森」→「せいもり」等の誤変換が起きやすい |
| TTT Platform / Model | **OpenAI GPT-4o** | 日本語理解・短文化。mini より 4o を推奨 |
| TTS Platform / Model | **ElevenLabs eleven_multilingual_v2** | 日本語ネイティブボイス必須 |
| Voice Identity | **日本語 Preview で「青森県」「おはようございます」を試聴** | **Sassy Comedian 等の英語キャラ声は不可** |
| Voice Stability | **0.75〜0.85** | 高め＝ペースが安定。低いと抑揚が強く早く聞こえる |
| Voice Similarity Boost | **0.65〜0.75** | |
| Temperature | **0.4** | 穏やかで一貫。高すぎると冗長になる |
| Frequency Penalty | 0.3 | 同語反復を抑える |
| Presence Penalty | 0.2 | 話題の逸脱を抑える |
| Play Filler Audios | **OFF** | 処理中の効果音がうるさい場合 |

---

## Conversation Controls（ダッシュボード右パネル）

実機テスト時の目安:

| 項目 | 推奨 |
|------|------|
| Auto Interrupt | OFF または低め（高齢者の話を遮らない） |
| Interrupt Sensitivity | 低〜中 |
| Auto Sleep | ON（無音時の省電力） |
| Auto Sleep Timeout | 60–120 秒 |

---

## DevKit 割り当て後の確認

1. Starting Message が日本語で再生される
2. 「今日は何曜日？」に 1–2 文で答える
3. 長文・英語混じり・記号読み上げがない
4. 「助けて」に 119 / 家族連絡を含む落ち着いた応答がある
5. **「青森県の天気は？」等で「あおもり」と正しく読む**（「せいもり」にならないこと）

---

## 日本語が弱い・わかりにくいとき（STT / TTS / プロンプト）

「青森」を「せいもり」と言う、内容が意味不明、などは **ほぼ STT 誤認識 + 英語系 TTS ボイス + LLM 推測** の組み合わせです。以下を **Dashboard で順に** 直してください。

### 1. ボイスを変える（最優先・効果大）

[app.openhome.com](https://app.openhome.com/) → Agent **KAIGO** → **Personality Identity** → **Voice Identity**

| やること | 理由 |
|----------|------|
| **Sassy Comedian 等の英語キャラ声を外す** | 日本語を変な読み方・早口で喋る主因 |
| Preview で **「おはようございます。青森県です。」** を試聴 | 落ち着いた日本語か確認 |
| **eleven_multilingual_v2**（または v3 日本語対応）を選ぶ | turbo 系は日本語が崩れやすい |
| Voice Stability **0.80** 前後 | 抑揚が強すぎると聞き取りにくい |

### 2. STT を日本語に固定

**Settings → Configurations** または Agent **Platforms & Models**:

| 項目 | 設定 |
|------|------|
| STT | **Deepgram** |
| Model | **nova-2**（または nova-3） |
| **Language** | **Japanese / ja**（英語 Auto のままだと地名が壊れる） |

保存後 **Restart Agent**。

### 3. LLM（TTT）を日本語向けに

| 項目 | 設定 |
|------|------|
| TTT | **OpenAI GPT-4o**（4o-mini より日本語・短文化が安定） |
| Temperature | **0.3〜0.4** |
| Description | 上記「標準語・地名の正しい読み・聞き返し」ルールを含む |

### 4. 居住地を persona に書く（任意）

Dashboard のファイル / Profile で `kaigo_persona.md` に追記すると、Agent が文脈を持ちやすい:

```markdown
## 居住地
青森県（読み: あおもりけん）
```

### 5. 実機チェック（5 分）

1. Web ダッシュボードのテキストチャットで「青森県について教えて」→ 読み上げプレビュー
2. DevKit で「青森の天気は？」→ **あおもり** と聞こえるか
3. まだダメなら **STT Language** と **Voice** のどちらかが未反映 → Restart DevKit + Restart Agent

### 症状別の原因

| 症状 | 主な原因 | 対策 |
|------|----------|------|
| 地名が変（せいもり等） | STT 英語 / TTS 英語ボイス | Language=ja、日本語ボイス |
| 早口・抑揚が強い | 英語キャラ TTS、Stability 低 | 落ち着いた日本語ボイス、Stability↑ |
| 内容がとっ散らかる | Temperature 高、プロンプト弱 | 0.4 以下、1〜2 文ルール |
| Ability 後だけ変 | kaigo_core 内 LLM | 下記 Ability 側プロンプトも更新 |
