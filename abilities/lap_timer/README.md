# lap_timer — DevKit 単体 RC ラップタイマー

USB カメラ + OpenHome DevKit だけでラップ計測。Mac / PC は不要（Dashboard 登録時のみブラウザ使用）。

## 構成

```
[USB カメラ] → DevKit (OpenCV 動体検知)
                    ↓
              lap_timer Ability (Skill)
                    ↓
              DevKit スピーカーで「3周目、12.1秒」
```

| ファイル | 役割 |
|----------|------|
| `main.py` | Skill — 音声トリガー、ポーリング、読み上げ |
| `devkit_functions.py` | Pi 上でカメラ監視スレッド、ライン通過検知 |
| `requirements.txt` | `opencv-python-headless` |

## Dashboard 登録

1. [app.openhome.com](https://app.openhome.com/) → **Create → Ability**
2. Category: **Local**
3. `main.py`, `devkit_functions.py`, `requirements.txt` をアップロード
4. トリガー: `タイム計測`, `ラップタイム`, `計測開始`, `計測停止`, `ベスト`, `リセット`
5. Agent に Ability を追加 → iOS **Sync Abilities**

Agent プロンプト: [config/agent-lap-timer-ja.md](../../config/agent-lap-timer-ja.md)

## 物理セットアップ

1. **USB カメラ**を DevKit の USB ポートに接続（ELP 等 UVC 対応）
2. カメラをサーキット**真上または斜め上**に固定（ゴールラインが画面中央付近に入る）
3. ゴールラインに**白または黄色のテープ**（動体検知が効きやすい）
4. RC 車はテープを越えるたびに 1 ラップ（最低 4 秒間隔）

検知ラインは画面高さの **55%** 付近（`devkit_functions.py` の `line_y_pct=0.55`）。ずれる場合は Dashboard から `start_monitor` の第 1 引数を `0.45`〜`0.65` で調整。

## 音声コマンド

| 言い方 | 動作 |
|--------|------|
| 「タイム計測」「ラップタイム」 | 計測開始（最大 20 周 or 10 分） |
| 「計測停止」 | 計測終了 + ベスト読み上げ |
| 「ベスト」 | 現在のベストラップ |
| 「リセット」 | 記録クリア |

## データ

`lap_timer_laps.json` — Ability 永続領域に保存（Dashboard / Profile で確認可）

## トラブル

| 症状 | 対策 |
|------|------|
| カメラが見つからない | USB 差し直し、Sync Abilities、黒 USB ポートを試す |
| ラップが取れない | カメラ位置・照明・テープのコントラストを調整。`motion_ratio` を `0.04` に下げる |
| 誤検知が多い | `min_lap_sec` を `5.0` に、`motion_ratio` を `0.08` に |
| 計測中に止めたい | 「計測停止」（別トリガー。計測 Skill 終了後）または 20 周で自動停止 |

## 動画撮影のコツ

1. DevKit + カメラ + ミニサーキットだけを写す
2. 「タイム計測」と言ってから 3 周走らせる
3. ベスト更新の読み上げを録音
4. Web ダッシュボードは映さなくて OK（DevKit 完結を強調）
