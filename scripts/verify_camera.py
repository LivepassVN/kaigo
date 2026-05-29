#!/usr/bin/env python3
"""
OpenHome DevKit 上で ELP-USBFHD06H-L170（UVC USB）の接続を確認するスクリプト。

Usage:
    python3 verify_camera.py [--device /dev/video0] [--output PATH] [--width W] [--height H]
    python3 verify_camera.py --list

Exit codes:
    0 = 撮影成功
    1 = opencv-python 未インストール
    2 = カメラ初期化・撮影失敗
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

DEFAULT_DEVICE = "/dev/video0"
WARMUP_FRAMES = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify ELP-USBFHD06H-L170 (UVC USB) via OpenCV/V4L2",
    )
    parser.add_argument(
        "--device",
        default=DEFAULT_DEVICE,
        help=f"V4L2 device path or index (default: {DEFAULT_DEVICE})",
    )
    parser.add_argument(
        "--output",
        default="/tmp/kaigo_camera_test.jpg",
        help="Output JPEG path (default: /tmp/kaigo_camera_test.jpg)",
    )
    parser.add_argument("--width", type=int, default=640, help="Capture width (default: 640)")
    parser.add_argument("--height", type=int, default=480, help="Capture height (default: 480)")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List /dev/video* devices and exit",
    )
    return parser.parse_args()


def list_video_devices() -> int:
    devices = sorted(glob.glob("/dev/video*"))
    if not devices:
        print("No /dev/video* devices found.", file=sys.stderr)
        return 2
    print("Available V4L2 devices:")
    for dev in devices:
        print(f"  {dev}")
    print("\nELP-USBFHD06H-L170 is typically /dev/video0 when only one USB camera is connected.")
    return 0


def resolve_device(device: str) -> int | str:
    if device.isdigit():
        return int(device)
    return device


def capture_with_opencv(device: int | str, output_path: Path, width: int, height: int) -> None:
    import cv2

    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera device: {device}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    for _ in range(WARMUP_FRAMES):
        cap.read()

    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        raise RuntimeError("Failed to capture frame from USB camera")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), frame):
        raise RuntimeError(f"Failed to write JPEG: {output_path}")


def main() -> int:
    args = parse_args()

    if args.list:
        return list_video_devices()

    output_path = Path(args.output)
    device = resolve_device(args.device)

    try:
        import cv2  # noqa: F401
    except ImportError:
        print(
            "FAIL: opencv-python is not installed.\n"
            "  Run on DevKit: pip install opencv-python-headless\n"
            "  Or use fswebcam: fswebcam -d /dev/video0 -r 640x480 /tmp/kaigo_camera_test.jpg",
            file=sys.stderr,
        )
        return 1

    try:
        capture_with_opencv(device, output_path, args.width, args.height)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        print(
            "Hint: check USB cable, run 'v4l2-ctl --list-devices', "
            "try --device /dev/video0 or --list",
            file=sys.stderr,
        )
        return 2

    if not output_path.is_file() or output_path.stat().st_size == 0:
        print(f"FAIL: output file missing or empty: {output_path}", file=sys.stderr)
        return 2

    print(f"OK: saved {output_path} ({output_path.stat().st_size} bytes) from {args.device}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
