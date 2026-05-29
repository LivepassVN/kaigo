# kaigo Phase 1 機能要件

詳細計画はプロジェクト計画書を参照。Phase 1 = **声対話 + USB カメラ（任意）**。

## 必須（MVP）

| # | 機能 | Ability |
|---|------|---------|
| 1 | 定型ルーティン・日付案内 | kaigo_core |
| 2 | 服薬・食事・水分リマインダー | kaigo_core (background) |
| 3 | 傾聴・短い会話（persona + エピソード文脈、話題提案、想起） | Agent + kaigo_core |
| 4 | 思い出話の促し・保存 | kaigo_core |
| 5 | 緊急キーワード応答 | kaigo_core |
| 6 | **天気・気温案内** | kaigo_core（Open-Meteo） |
| 7 | 日次ジャーナル | kaigo_journal |
| 8 | 声トリガー撮影（カメラ接続時） | kaigo_vision |
| 9 | `kaigo_persona.md` 更新 | kaigo_core |
| 10 | エピソード JSONL | kaigo_core / kaigo_vision |

## Phase 2 以降

- 家族ダッシュボード・通知・画像共有（**後回し** — git / リレーサーバ待ち）
- IoT 全般（`devkit_functions.py` 統合）

## 成功指標

- 声だけで服薬リマインダーと日付確認ができる
- 1 日 1 回以上、日常会話が `kaigo_daily_*.json` に残る
- `kaigo_persona.md` が更新され Agent に反映される
