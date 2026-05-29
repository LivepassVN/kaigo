# Phase 1 カメラ — ELP-USBFHD06H-L170

## 機種

| 項目 | 仕様 |
|------|------|
| **型番** | ELP-USBFHD06H-L170 |
| **接続** | USB 2.0（UVC、ドライバ不要） |
| **センサー** | Sony IMX323（1/2.9 inch, 2MP） |
| **解像度** | 最大 1920×1080 @ 30fps（H.264 / MJPEG / YUY2） |
| **レンズ** | 魚眼 170°（HFOV 約 130°） |
| **低照度** | 0.01 lux |
| **マイク** | 内蔵デジタル MIC（Phase 1 では DevKit マイクを優先） |
| **OS** | Linux（UVC）— Raspberry Pi / OpenHome DevKit で Plug & Play |

## DevKit 上のデバイス

- 通常 `/dev/video0`（他に USB カメラがある場合は `/dev/video1` 等）
- 確認: `v4l2-ctl --list-devices` または `ls -l /dev/video*`

## Phase 1 での使い方

- **検証**: `scripts/verify_camera.py`（OpenCV / V4L2）
- **Ability**: `kaigo_vision` は `picamera2` ではなく **OpenCV + V4L2** で実装予定
- **解像度**: 定期スナップショットは低解像度（例: 640×480）を推奨（計画の非侵襲方針）

## 参考

- [ELP 製品ページ（USBFHD06H シリーズ）](https://www.elpcctv.com/elp-2mp-full-hd-1080p-h264-low-light-wide-angle-usb-camera-module-with-21mm-lens-p-504.html)
- [Raspberry Pi USB Webcam ガイド](http://raspberrypi-guide.github.io/electronics/using-usb-webcams)
