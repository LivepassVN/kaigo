# DevKit オンボード + USB カメラ + 日本語 Agent セットアップ

Phase 1 の開発環境を整えるための手順書です。以下 3 つを完了させてください。

1. OpenHome DevKit の Wi-Fi オンボード
2. **ELP-USBFHD06H-L170**（USB カメラ）の接続と動作確認
3. [app.openhome.com](https://app.openhome.com/) で日本語 Agent（kaigo）の作成

---

## 前提条件

| 項目 | 内容 |
|------|------|
| OpenHome アカウント | [app.openhome.com](https://app.openhome.com/) で作成済み |
| iOS 端末（推奨） | iOS 17.0 以降 — [コンパニオンアプリ](https://apps.apple.com/jp/app/openhome-voice-ai-devkit/id6755683119) 必須 |
| 自宅 Wi-Fi | SSID とパスワードを用意 |
| カメラ | **ELP-USBFHD06H-L170**（USB 2.0 UVC、170° 魚眼、1080p）— [config/camera.md](../config/camera.md) |
| microSD | 画像・ログ保存用に十分な容量 |

### 参考リンク

- [DevKit オンボード（iOS アプリ）](https://docs.openhome.com/devkit/devkit-onboarding-app.md)
- [DevKit オンボード（ターミナル）](https://docs.openhome.com/devkit/devkit-setup-terminal.md)
- [Local Ability](https://docs.openhome.com/local-ability)（USB カメラは OpenCV / V4L2 で `devkit_functions.py` から制御）
- [Agent 作成ガイド](https://docs.openhome.com/building-agents/creating-an-agent.md)

---

## 1. DevKit オンボード

### 方法 A: iOS コンパニオンアプリ（推奨）

1. App Store から [OpenHome - Voice AI DevKit](https://apps.apple.com/jp/app/openhome-voice-ai-devkit/id6755683119) をインストール
2. DevKit の電源を入れる
3. アプリを開き **Get Started** をタップ
4. **Find and Connect Your DevKit** — 一覧から DevKit を選び **Connect Device**
5. 接続音が鳴ったら **Yes, I heard it**
6. 自宅 Wi-Fi を選びパスワードを入力 → 接続確認音を待つ
7. OpenHome アカウントでサインイン（Apple / Google / メール）
8. 設定完了後、Agent のウェルカムメッセージが DevKit から再生される
9. アプリのダッシュボードで DevKit が **Connected** になっていることを確認

### 方法 B: ターミナル（iOS 端末がない場合）

```bash
# 1. 依存ライブラリ
pip install bleak

# 2. OpenHome クライアントを取得
# https://docs.openhome.com/devkit/devkit-setup-terminal.md のリンクから
# openhome_client.py をダウンロード

# 3. 対話式オンボード（リポジトリ同梱スクリプト）
bash scripts/onboard-terminal.sh
```

ターミナル手順の概要:

| オプション | 操作 |
|-----------|------|
| 1 | DevKit をスキャン |
| 2 | 接続 |
| 3–4 | Wi-Fi 一覧取得・表示 |
| 5 | Wi-Fi 接続（番号 + パスワード） |
| 6 | 接続状態確認 |
| 10 | OpenHome API キーを設定 |

API キーは [Dashboard → Settings → API Keys](https://app.openhome.com/dashboard/settings) から取得します。

### オンボード完了チェック

- [ ] DevKit が [Dashboard → DevKit](https://app.openhome.com/dashboard/devkit) に表示される
- [ ] DevKit から Agent の開始メッセージが聞こえる
- [ ] コンパニオンアプリ / ダッシュボードで **Connected** 状態

---

## 2. USB カメラ接続（ELP-USBFHD06H-L170）

Phase 1 では DevKit に **USB カメラ（ELP-USBFHD06H-L170）** を追加します。CSI カメラではなく **UVC（ドライバ不要）** です。GPIO センサー等は Phase 3 以降です。

機種詳細: [config/camera.md](../config/camera.md)

### 2.1 物理接続

1. ELP-USBFHD06H-L170 のレンズ保護フィルムを剥がす
2. USB ケーブルを DevKit（Raspberry Pi）の **USB 2.0 ポート（黒）** に接続
   - **青い USB 3.0 ポートは避ける** — ELP は USB 2.0 機器のため、認識しない・すぐ切れることがある
   - Pi 5: 本体横の **黒** が USB 2.0、**青** が USB 3.0
   - USB ハブ経由の場合は **給電付きハブ** を推奨（カメラ消費電流 140–190 mA）
   - DevKit のマイク用 USB とポートが競合する場合は、空いているポートを使う
3. カメラを設置（170° 魚眼のため、部屋全体が広く写る。プライバシーに配慮した位置・角度にする）

> ELP-USBFHD06H-L170 は UVC 準拠のため、OpenHome DevKit 上で追加ドライバは不要です。`picamera2` / CSI カメラ用の設定は **不要** です。

### 2.2 DevKit への SSH 接続

ホスト名は **`openhome.local`**（例: `192.168.1.89`）です。`raspberrypi.local` ではありません。

```bash
ssh pi@openhome.local
# または
ssh openhome@openhome.local
```

**パスワードについて**

- OpenHome 公式ドキュメントに **デフォルト SSH パスワードは記載されていません**
- 試す順序:
  1. [app.openhome.com](https://app.openhome.com/) の **OpenHome アカウントのパスワード**（オンボード時と同じ）
  2. DevKit 同梱のクイックスタート / 箱内の資料
  3. 上記で入らない場合 → [OpenHome Discord](https://discord.gg/openhome) で SSH 認証情報を問い合わせ
- 入力中 **画面に文字は表示されません**（`*` も出ない）。そのまま打って Enter
- `pi` / `raspberry` は **2022 年以降の Raspberry Pi OS では使えない** ことが多い

**SSH なしで進める場合**

- iOS アプリの **Sync Abilities** で Local Ability を DevKit に同期（`kaigo_vision` 実装後）
- カメラの `lsusb` 確認だけなら、HDMI + USB キーボードを DevKit に直接接続してローカルログインも可能

### 2.3 カメラ認識確認

DevKit に SSH（または直接ログイン）後:

```bash
# USB デバイス一覧（ELP または UVC と表示される）
lsusb

# V4L2 デバイス一覧
ls -l /dev/video*
v4l2-ctl --list-devices   # v4l-utils がある場合
```

ELP が 1 台だけのとき、通常は `/dev/video0` です。

```bash
python3 /tmp/verify_camera.py --list
```

### 2.4 依存パッケージ（DevKit 上）

```bash
pip install opencv-python-headless
# または apt: sudo apt install python3-opencv
# 代替（OpenCV なし）: sudo apt install fswebcam
```

### 2.5 動作確認

```bash
# ローカル PC から DevKit へスクリプトをコピー（IP は環境に合わせて変更）
scp scripts/verify_camera.py pi@<DEVKIT_IP>:/tmp/

# DevKit 上で実行
ssh pi@<DEVKIT_IP>
pip install opencv-python-headless   # 未インストールの場合
python3 /tmp/verify_camera.py --device /dev/video0
```

成功時の出力例:

```
OK: saved /tmp/kaigo_camera_test.jpg (12345 bytes) from /dev/video0
```

生成された JPEG を PC に取得して目視確認:

```bash
scp pi@<DEVKIT_IP>:/tmp/kaigo_camera_test.jpg .
open kaigo_camera_test.jpg   # macOS
```

**OpenCV を使わない場合**（fswebcam）:

```bash
fswebcam -d /dev/video0 -r 640x480 --no-banner /tmp/kaigo_camera_test.jpg
```

### カメラ接続チェック

- [ ] `lsusb` で UVC カメラが表示される
- [ ] `/dev/video0`（または `--list` で表示されたデバイス）が存在する
- [ ] `scripts/verify_camera.py` が `OK:` で終了する
- [ ] 保存された JPEG が正常に表示される（魚眼の広角が確認できる）

### トラブルシューティング

#### カメラがまったく認識されない（`lsusb` にも出ない）

**追加作業は OS 設定ではなく、接続・電源の確認が中心です。** UVC カメラはドライバインストール不要ですが、USB として列挙されるまで OS は何もできません。

**Step 0 — 確認場所**

- 確認は **Mac ではなく DevKit 上**（SSH または DevKit に直接キーボード接続）で行ってください
- `vcgencmd get_camera` は **CSI カメラ専用** で、USB カメラには使えません

**Step 1 — 黒い USB 2.0 ポートへ変更**

1. カメラ以外の USB 機器（マイク・Bluetooth ドングル等）を **いったんすべて外す**
2. ELP を **黒い USB 2.0 ポート** に直接差す（延長・ハブなし）
3. 別の黒ポートも試す

**Step 2 — 差し込みながらカーネルログを見る**

DevKit に SSH 接続し、別ターミナルで:

```bash
sudo dmesg -w
```

この状態でカメラを抜き差しする。正常なら次のような行が出ます:

```
usb ... new full-speed USB device ...
uvcvideo: Found UVC 1.00 device ...
```

**ログに何も出ない** → ケーブル・ポート・カメラ本体の物理問題の可能性大  
**`error -71` / `-110` / `device descriptor read`** → **電源不足** の可能性大（下記 Step 3）

**Step 3 — 電源を確認**

- DevKit 付属の **公式 5V 電源** を使用（スマホ充電器は避ける）
- カメラ + マイク + スピーカーを同時接続すると USB バスが足りないことがある  
  → **カメラだけ** 接続して `lsusb` を再確認
- それでもダメなら **給電付き USB 2.0 ハブ** 経由でカメラだけ給電

**Step 4 — ケーブル・カメラ単体テスト**

- ELP 付属 USB ケーブルを **Mac / PC** に差し、`lsusb` または「カメラ」アプリで認識するか確認
- PC で認識する → DevKit 側のポート or 電源問題
- PC でも認識しない → ケーブル or カメラ故障

**Step 5 — DevKit 上で列挙確認**

```bash
lsusb
lsusb -t
ls -l /dev/video*
```

`lsusb` に `0483:...` や `Sonix` / `Generic` / `USB Camera` 等が出れば USB 認識 OK。  
`/dev/video0` が無い場合:

```bash
sudo modprobe uvcvideo
ls -l /dev/video*
sudo usermod -aG video $USER   # 実行後ログアウト・再ログイン
```

**Step 6 — それでも認識しない場合**

| 確認項目 | 内容 |
|---------|------|
| OpenHome OS の更新 | `sudo apt update && sudo apt upgrade` 後に再起動 |
| USB autosuspend | `echo -1 \| sudo tee /sys/module/usbcore/parameters/autosuspend`（一時的） |
| Discord サポート | [OpenHome Discord](https://discord.gg/openhome) に `dmesg` 抜粋を共有 |

#### その他の症状

| 症状 | 対処 |
|------|------|
| `/dev/video0` がない（lsusb には出る） | `sudo modprobe uvcvideo`。`video` グループにユーザ追加 |
| 別カメラと `/dev/video1` になる | `verify_camera.py --device /dev/video1` を指定 |
| `ModuleNotFoundError: cv2` | `pip install opencv-python-headless` |
| 真っ暗 / 真っ白 | レンズフィルム、露出設定。魚眼のため画面端は歪むのが正常 |
| 帯域・CPU 負荷が高い | 解像度を下げる（`-r 640x480`）。Phase 1 の定期撮影も低解像度推奨 |
| Permission denied | ユーザーを `video` グループに追加: `sudo usermod -aG video $USER` → 再ログイン |

---

## 3. 日本語 Agent（kaigo）の作成

[app.openhome.com](https://app.openhome.com/) で Phase 1 用 Agent を **Pro Mode** で作成します。

### 3.1 作成手順

1. ダッシュボード左サイドバー → **Create** → **Agent Personality**
2. **Switch to PRO Mode** をクリック
3. [config/agent-kaigo-ja.md](../config/agent-kaigo-ja.md) の各項目をコピーして入力
4. **Save Personality**
5. [Dashboard → DevKit](https://app.openhome.com/dashboard/devkit) でこの Agent を DevKit に割り当て

### 3.2 必須設定（Pro Mode）

| セクション | 設定 |
|-----------|------|
| **Personality Information** | 名前: `kaigo`（任意の表示名） |
| **Personality Behavior** | Starting Message / Description → `config/agent-kaigo-ja.md` 参照 |
| **Personality Identity** | Language: **Japanese（日本語）** / Voice: 落ち着いた日本語 TTS |
| **Platforms & Models** | STT・TTS が日本語対応の組み合わせ（下表参照） |

#### 推奨モデル構成

Dashboard → **Settings → Model Configuration** で API キーを設定したうえで、Agent ごとに以下を目安に選びます。

| モジュール | 推奨 | 備考 |
|-----------|------|------|
| STT | Deepgram（多言語）または AssemblyAI | 日本語の認識精度を実機で確認 |
| TTT（LLM） | OpenAI GPT-4o / Claude 等 | Temperature **0.3–0.5**（穏やかで一貫した応答） |
| TTS | ElevenLabs 等の日本語対応ボイス | 高齢者向け: ゆっくり・はっきりした声 |

### 3.3 DevKit への Agent 割り当て

1. iOS コンパニオンアプリ、または Web ダッシュボードの DevKit 設定を開く
2. **Agent** / **Personality** 一覧から `kaigo` を選択
3. DevKit を再起動または **Restart Agent**（表示がある場合）
4. 日本語の Starting Message が再生されることを確認

### 3.4 動作確認（声対話）

DevKit に向かって以下を試します。

| 試すフレーズ | 期待する動作 |
|-------------|-------------|
| 「おはよう」 | 日本語で短く挨拶 |
| 「今日は何曜日？」 | 日付・曜日を口頭で案内 |
| 「助けて」 | 落ち着いた応答（緊急時は 119 / 家族連絡を案内） |

### Agent 作成チェック

- [ ] Pro Mode で Agent を保存した
- [ ] Language が **Japanese** になっている
- [ ] Starting Message が日本語で再生される
- [ ] 短い質問に 1–2 文で応答する（長文にならない）
- [ ] DevKit に Agent が割り当てられている

---

## セットアップ完了の定義

以下がすべて満たされたら `setup-devkit-camera` は完了です。

1. DevKit が Wi-Fi 経由で OpenHome ダッシュボードに接続されている
2. ELP-USBFHD06H-L170 が `verify_camera.py` で JPEG 保存に成功する
3. 日本語 Agent `kaigo` が DevKit に割り当てられ、声対話ができる

---

## 次のステップ

- `kaigo_vision` Local Ability の実装（OpenCV / V4L2 で ELP-USBFHD06H-L170 連携）— 計画 todo `ability-kaigo-vision`
- `kaigo_core` でルーティン・リマインダー実装 — 計画 todo `ability-kaigo-core`
- データスキーマ定義 — 計画 todo `init-kaigo-repo`
