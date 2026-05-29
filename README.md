# kaigo — 認知症独居支援スピーカー

OpenHome DevKit 向けの **Phase 1** プロジェクトです。高齢者本人向けの **声対話** を中心に、任意で **カメラ**（在宅シグナル・エピソード写真）を足します。会話・思い出・画像を永続保存し、将来の **仏壇 AI**（声・人格・エピソードの再現）に渡せるデータ基盤を Phase 1 から整えます。

開発基盤: [OpenHome Ability](https://docs.openhome.com/introduction)（Python）+ [Local Ability](https://docs.openhome.com/local-ability)（`picamera2` / `devkit_functions.py`）

---

## Phase 境界

| フェーズ | スコープ | 含む / 含まない |
|----------|----------|-----------------|
| **Phase 1** | 声対話 + カメラ（任意） | DevKit・マイク・スピーカー・Camera Module。**家族ダッシュボード・外部 IoT は含まない** |
| **Phase 2** | 家族・見守り | 日次サマリー、緊急通知、画像共有（オプトイン） |
| **Phase 3 以降** | IoT 全般 | ドア・ボタン・温湿度等 — **`devkit_functions.py` 経由で統合** |

Phase 3 向けの `device_events[]` は [docs/data-schema.md](docs/data-schema.md) に予約済みです。センサー追加の **唯一の入口** は各 Local Ability の `devkit_functions.py` とし、Skill 側からは統一 API で呼び出す方針です（実装は Phase 3）。

---

## リポジトリ構成

```
kaigo/
├── README.md
├── config/                    # Agent プロンプト・テンプレート
├── docs/
│   ├── requirements.md        # Phase 1 機能一覧
│   ├── data-schema.md         # 永続データ・エクスポート
│   ├── privacy.md             # プライバシー・倫理
│   └── deploy.md              # Ability 登録手順
└── abilities/
    ├── kaigo_core/            # Skill: ルーティン・リマインダー・傾聴・緊急
    ├── kaigo_journal/         # Skill: 日次ジャーナル
    ├── kaigo_vision/          # Local: picamera2・スナップショット
    └── lap_timer/             # （別デモ）RC ラップタイマー
```

---

## クイックスタート（Phase 1）

| 順 | 内容 |
|----|------|
| 1 | [iOS コンパニオンアプリ](https://apps.apple.com/jp/app/openhome-voice-ai-devkit/id6755683119) をインストールし、DevKit を Wi-Fi オンボード |
| 2 | Raspberry Pi に **Camera Module** を接続（任意・[セットアップ](docs/setup-devkit-camera.md)） |
| 3 | [app.openhome.com](https://app.openhome.com/) で Agent **kaigo** を作成（[config/agent-kaigo-ja.md](config/agent-kaigo-ja.md)） |
| 4 | Abilities を登録 → Sync → 実機で声テスト（[docs/deploy.md](docs/deploy.md)） |

**制約:** Live Editor では Local Ability（カメラ）は動きません。`kaigo_vision` は **DevKit 実機** で検証してください。

---

## Abilities（Phase 1）

| Ability | 種別 | 用途 |
|---------|------|------|
| [kaigo_core](abilities/kaigo_core/) | Skill + Background | ルーティン・リマインダー・思い出・緊急・persona 更新 |
| [kaigo_journal](abilities/kaigo_journal/) | Skill | 日次 `kaigo_daily_*.json` |
| [kaigo_vision](abilities/kaigo_vision/) | **Local** | 声トリガー撮影・定期スナップショット（任意） |
| [kaigo_weather](abilities/kaigo_weather/) | Skill（任意） | 天気案内（Open-Meteo） |
| [lap_timer](abilities/lap_timer/) | Local | **別デモ** — RC ラップタイマー（kaigo 本体とは独立） |

---

## ハードウェア（Phase 1 推奨）

| 部品 | 用途 |
|------|------|
| OpenHome DevKit（または Pi 5 + OpenHome OS） | 本体 |
| Raspberry Pi Camera Module 3（または互換） | 在宅シグナル・エピソード写真（任意） |
| DevKit マイク / BT スピーカー | 声対話 |
| microSD（十分な容量） | 画像・ログ |

---

## 倫理・プライバシー

本システムは **医療機器ではありません**。緊急時は **119 番・家族・介護者** が本体です。カメラ・会話記録・仏壇 AI 転用の同意については [docs/privacy.md](docs/privacy.md) を必ず読んでください。

---

## ドキュメント

- [機能要件（Phase 1）](docs/requirements.md)
- [データスキーマ・エクスポート](docs/data-schema.md)
- [プライバシー・倫理](docs/privacy.md)
- [デプロイ手順](docs/deploy.md)
- [DevKit + カメラ](docs/setup-devkit-camera.md)

## 参考リンク

- [OpenHome Dashboard](https://app.openhome.com/)
- [Local Ability（picamera2）](https://docs.openhome.com/local-ability)
- [永続メモリ](https://docs.openhome.com/guides/best-practices/persistent-memory)
- [Agent Memory 注入](https://docs.openhome.com/agent_memory_context_injection.md)
- [公式 abilities 例](https://github.com/openhome-dev/abilities/tree/dev)
