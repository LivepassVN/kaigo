# kaigo_weather

**天気専用 Skill。** Open-Meteo から江戸川区（または `kaigo_location.json`）の天気を読み上げます。

`kaigo_core` に天気トリガーを足す代わりに、こちらだけ登録しても構いません。

## なぜ必要か

Web チャットで「天気」と入力しても **Agent が一般応答** するのは、Ability の **トリガー語が未登録** のためです。  
OpenHome は Dashboard に登録した語が含まれるときだけ Skill を起動します。

## OpenHome への登録（5 分）

1. [app.openhome.com](https://app.openhome.com/) → **MY ABILITIES** → **Create → Ability**
2. 名前: `kaigo_weather`、Category: **Skill**
3. `main.py` を Live Editor に貼り付け（または zip アップロード）→ **Save**
4. **Trigger Words** に次を **すべて** 追加:
   - `天気`
   - `てんき`
   - `今日の天気`
5. **MY AGENTS** → **KAIGO** → **Edit** → **Abilities** に `kaigo_weather` を追加 → Save
6. iOS アプリ → **Sync Abilities**
7. **新しい会話** を開始してテスト

## テスト

| 入力 | 期待 |
|------|------|
| `天気` | 「きょうの**えどがわく**のてんきは、…きおんは…どくらいです。」 |
| `てんき` | 同上（ひらがなトリガーも必須） |
| `今日の天気` | 同上 |

**成功の目安:** Agent の創作応答（「きょうのてんきはどうですか…」）ではなく、**具体的な気温・天候** が返る。

## 位置の変更

`kaigo_location.json` を Dashboard のファイル機能で編集。テンプレート: [config/kaigo_location.template.json](../../config/kaigo_location.template.json)

## kaigo_core との関係

- 両方に天気トリガーを付けると **二重起動** する可能性があります。**どちらか一方** に天気トリガーを付けてください。
- `kaigo_core` だけ使う場合は、そちらの Trigger Words に `天気` / `てんき` を追加すれば `kaigo_weather` は不要です。
