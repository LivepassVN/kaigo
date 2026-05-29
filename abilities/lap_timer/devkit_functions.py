"""
DevKit-side lap detection for RC circuit timer (UVC camera + OpenCV).

State is persisted to /tmp/lap_timer_state.json so the Skill can poll while
the monitor thread runs on the Pi.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from devkit_utils.devkit_logging import web_logger as log

STATE_PATH = Path("/tmp/lap_timer_state.json")
DEFAULT_DEVICE = "/dev/video0"

_monitor_thread: threading.Thread | None = None
_monitor_stop = threading.Event()
_state_lock = threading.Lock()


def _print_payload(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _default_state() -> dict[str, Any]:
    return {
        "running": False,
        "started_at": None,
        "line_y_pct": 0.55,
        "min_lap_sec": 4.0,
        "device": DEFAULT_DEVICE,
        "width": 640,
        "height": 480,
        "laps": [],
        "best_sec": None,
        "last_motion_at": None,
        "error": None,
    }


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return _default_state()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        base = _default_state()
        base.update(data if isinstance(data, dict) else {})
        return base
    except Exception:
        return _default_state()


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _motion_in_band(gray, prev_gray, line_y: int, band: int, width: int) -> int:
    import cv2

    y0 = max(0, line_y - band)
    y1 = min(gray.shape[0], line_y + band)
    roi = gray[y0:y1, :]
    prev_roi = prev_gray[y0:y1, :]
    diff = cv2.absdiff(roi, prev_roi)
    _, thresh = cv2.threshold(diff, 28, 255, cv2.THRESH_BINARY)
    return int(cv2.countNonZero(thresh))


def _monitor_loop(
    device: str,
    width: int,
    height: int,
    line_y_pct: float,
    min_lap_sec: float,
    motion_ratio: float,
) -> None:
    import cv2

    state = _load_state()
    state["running"] = True
    state["error"] = None
    state["started_at"] = datetime.now().isoformat(timespec="seconds")
    state["laps"] = []
    state["best_sec"] = None
    _save_state(state)

    dev: int | str = int(device) if str(device).isdigit() else device
    cap = cv2.VideoCapture(dev)
    if not cap.isOpened():
        state = _load_state()
        state["running"] = False
        state["error"] = f"Cannot open camera: {device}"
        _save_state(state)
        log.error("lap_timer: camera open failed device=%s", device)
        return

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        for _ in range(8):
            cap.read()

        line_y = int(height * line_y_pct)
        band = max(8, height // 24)
        area = width * (band * 2)
        threshold_pixels = int(area * motion_ratio)

        prev_gray = None
        last_lap_at = time.monotonic()
        session_start = last_lap_at
        lap_count = 0

        log.info(
            "lap_timer monitor: line_y=%s band=%s threshold=%s min_lap=%ss",
            line_y,
            band,
            threshold_pixels,
            min_lap_sec,
        )

        while not _monitor_stop.is_set():
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            if prev_gray is None:
                prev_gray = gray
                time.sleep(0.03)
                continue

            motion = _motion_in_band(gray, prev_gray, line_y, band, width)
            prev_gray = gray
            now = time.monotonic()

            if motion >= threshold_pixels and (now - last_lap_at) >= min_lap_sec:
                if lap_count == 0:
                    lap_sec = round(now - session_start, 2)
                else:
                    lap_sec = round(now - last_lap_at, 2)

                lap_count += 1
                last_lap_at = now

                with _state_lock:
                    state = _load_state()
                    laps = state.get("laps") or []
                    best = state.get("best_sec")
                    laps.append(
                        {
                            "n": lap_count,
                            "sec": lap_sec,
                            "at": datetime.now().isoformat(timespec="seconds"),
                        }
                    )
                    if best is None or lap_sec < best:
                        best = lap_sec
                    state["laps"] = laps
                    state["best_sec"] = best
                    state["last_motion_at"] = state["laps"][-1]["at"]
                    _save_state(state)

                log.info("lap_timer: lap %s %.2fs motion=%s", lap_count, lap_sec, motion)

            time.sleep(0.03)

    except Exception as exc:
        log.exception("lap_timer monitor failed")
        state = _load_state()
        state["running"] = False
        state["error"] = str(exc)
        _save_state(state)
    finally:
        cap.release()
        state = _load_state()
        state["running"] = False
        _save_state(state)
        log.info("lap_timer monitor stopped")


def start_monitor(
    line_y_pct: str = "0.55",
    min_lap_sec: str = "4.0",
    device: str = DEFAULT_DEVICE,
    width: str = "640",
    height: str = "480",
    motion_ratio: str = "0.06",
) -> None:
    metric = "start_monitor"
    global _monitor_thread

    if _monitor_thread is not None and _monitor_thread.is_alive():
        _monitor_stop.set()
        _monitor_thread.join(timeout=3.0)

    _monitor_stop.clear()

    try:
        ly = float(line_y_pct)
        mls = float(min_lap_sec)
        w, h = int(width), int(height)
        mr = float(motion_ratio)
    except ValueError as exc:
        _print_payload(
            {
                "success": False,
                "metric": metric,
                "spoken_response": "設定値が正しくありません。",
                "data": {},
                "error": {"code": "bad_args", "message": str(exc)},
            }
        )
        return

    try:
        import cv2  # noqa: F401
    except ImportError as exc:
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

    state = _default_state()
    state.update(
        {
            "line_y_pct": ly,
            "min_lap_sec": mls,
            "device": device,
            "width": w,
            "height": h,
        }
    )
    _save_state(state)

    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(device, w, h, ly, mls, mr),
        daemon=True,
    )
    _monitor_thread.start()
    time.sleep(0.4)

    state = _load_state()
    if state.get("error"):
        _print_payload(
            {
                "success": False,
                "metric": metric,
                "spoken_response": "カメラが見つかりませんでした。",
                "data": state,
                "error": {"code": "camera_open_failed", "message": state["error"]},
            }
        )
        return

    _print_payload(
        {
            "success": True,
            "metric": metric,
            "spoken_response": "計測を開始しました。ゴールラインを越えてください。",
            "data": {"running": state.get("running"), "line_y_pct": ly, "min_lap_sec": mls},
            "error": None,
        }
    )


def poll_status() -> None:
    metric = "poll_status"
    state = _load_state()
    laps = state.get("laps") or []
    last = laps[-1] if laps else None
    _print_payload(
        {
            "success": True,
            "metric": metric,
            "spoken_response": "",
            "data": {
                "running": bool(state.get("running")),
                "lap_count": len(laps),
                "laps": laps,
                "last_lap": last,
                "best_sec": state.get("best_sec"),
                "error": state.get("error"),
            },
            "error": None,
        }
    )


def stop_monitor() -> None:
    metric = "stop_monitor"
    global _monitor_thread

    _monitor_stop.set()
    if _monitor_thread is not None and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=4.0)
    _monitor_thread = None

    state = _load_state()
    state["running"] = False
    _save_state(state)

    laps = state.get("laps") or []
    best = state.get("best_sec")
    spoken = "計測を止めました。"
    if laps and best is not None:
        spoken += f"全{len(laps)}周。ベストは{best:.1f}秒です。"

    _print_payload(
        {
            "success": True,
            "metric": metric,
            "spoken_response": spoken,
            "data": {"lap_count": len(laps), "best_sec": best, "laps": laps},
            "error": None,
        }
    )


def reset_session() -> None:
    metric = "reset_session"
    global _monitor_thread

    if _monitor_thread is not None and _monitor_thread.is_alive():
        _monitor_stop.set()
        _monitor_thread.join(timeout=4.0)
    _monitor_thread = None
    _monitor_stop.clear()

    state = _default_state()
    _save_state(state)

    _print_payload(
        {
            "success": True,
            "metric": metric,
            "spoken_response": "ラップ記録をリセットしました。",
            "data": {"lap_count": 0},
            "error": None,
        }
    )


FUNCTION_REGISTRY = {
    "start_monitor": start_monitor,
    "poll_status": poll_status,
    "stop_monitor": stop_monitor,
    "reset_session": reset_session,
}


def main() -> None:
    if len(sys.argv) < 2:
        _print_payload(
            {
                "success": False,
                "metric": "dispatch",
                "spoken_response": "ラップタイマー機能が指定されていません。",
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
                "spoken_response": "その機能は使えません。",
                "data": {},
                "error": {"code": "unknown_function", "message": name},
            }
        )
        sys.exit(1)
    fn(*args)


if __name__ == "__main__":
    main()
