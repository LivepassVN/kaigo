"""
DevKit-side camera capture for ELP-USBFHD06H-L170 (UVC / OpenCV).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from devkit_utils.devkit_logging import web_logger as log

SNAPSHOT_DIR = Path("/tmp/kaigo_snapshots")
DEFAULT_DEVICE = "/dev/video0"


def _print_payload(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def capture_snapshot(width: str = "640", height: str = "480", device: str = DEFAULT_DEVICE) -> None:
    metric = "capture_snapshot"
    log.info("capture_snapshot: device=%s %sx%s", device, width, height)
    try:
        import cv2
    except ImportError as exc:
        log.exception("opencv not installed")
        _print_payload(
            {
                "success": False,
                "metric": metric,
                "spoken_response": "カメラ用のソフトウェアが入っていません。",
                "data": {},
                "error": {"code": "missing_opencv", "message": str(exc)},
            }
        )
        return

    w, h = int(width), int(height)
    dev: int | str = int(device) if str(device).isdigit() else device

    cap = cv2.VideoCapture(dev)
    if not cap.isOpened():
        _print_payload(
            {
                "success": False,
                "metric": metric,
                "spoken_response": "カメラが見つかりませんでした。",
                "data": {"device": device},
                "error": {"code": "camera_open_failed", "message": f"Cannot open {device}"},
            }
        )
        return

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        for _ in range(5):
            cap.read()
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to capture frame")

        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = SNAPSHOT_DIR / f"kaigo_{ts}.jpg"
        if not cv2.imwrite(str(out_path), frame):
            raise RuntimeError(f"Failed to write {out_path}")

        _print_payload(
            {
                "success": True,
                "metric": metric,
                "spoken_response": "写真を撮りました。",
                "data": {"path": str(out_path), "width": w, "height": h, "device": device},
                "error": None,
            }
        )
    except Exception as exc:
        log.exception("capture_snapshot failed")
        _print_payload(
            {
                "success": False,
                "metric": metric,
                "spoken_response": "写真を撮れませんでした。",
                "data": {},
                "error": {"code": "capture_error", "message": str(exc)},
            }
        )
    finally:
        cap.release()


FUNCTION_REGISTRY = {
    "capture_snapshot": capture_snapshot,
}


def main() -> None:
    if len(sys.argv) < 2:
        _print_payload(
            {
                "success": False,
                "metric": "dispatch",
                "spoken_response": "カメラ機能が指定されていません。",
                "data": {},
                "error": {"code": "missing_function", "message": "No function name"},
            }
        )
        sys.exit(1)

    name = sys.argv[1]
    args = sys.argv[2:]
    fn = FUNCTION_REGISTRY.get(name)
    if fn is None:
        _print_payload(
            {
                "success": False,
                "metric": "dispatch",
                "spoken_response": "そのカメラ機能は使えません。",
                "data": {},
                "error": {"code": "unknown_function", "message": name},
            }
        )
        sys.exit(1)
    fn(*args)


if __name__ == "__main__":
    main()
