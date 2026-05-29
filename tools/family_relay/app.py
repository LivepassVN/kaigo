"""
kaigo 家族通知リレー — Webhook 受信 → Slack / Discord / LINE Messaging API 転送

LINE Notify は 2025-03-31 終了。LINE 通知は Messaging API を使用。

環境変数（いずれか1つ以上）:
  KAIGO_WEBHOOK_SECRET
  SLACK_WEBHOOK_URL
  DISCORD_WEBHOOK_URL
  LINE_CHANNEL_ACCESS_TOKEN + LINE_TO_USER_ID
"""

import os
from datetime import datetime

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

KAIGO_SECRET = os.environ.get("KAIGO_WEBHOOK_SECRET", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_TO_USER_ID = os.environ.get("LINE_TO_USER_ID", "")
PORT = int(os.environ.get("PORT", "8080"))


def _check_secret() -> bool:
    if not KAIGO_SECRET:
        return True
    return request.headers.get("X-Kaigo-Secret") == KAIGO_SECRET


def _format_message(data: dict) -> str:
    event = data.get("event", "unknown")
    label = data.get("resident_label", "利用者")
    message = (data.get("message") or "").strip()
    ts = data.get("timestamp") or datetime.now().isoformat()
    lines = [message or f"[{event}] {label}", f"時刻: {ts}"]
    details = data.get("details") or {}
    if details.get("transcript_snippet"):
        lines.append(f"発話: {details['transcript_snippet']}")
    if details.get("summary"):
        lines.append(f"要約: {details['summary']}")
    if details.get("emergency_count"):
        lines.append(f"本日の緊急: {details['emergency_count']}件")
    return "\n".join(lines)


def _send_slack(text: str) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    resp = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": text[:3000]},
        timeout=15,
    )
    resp.raise_for_status()


def _send_discord(text: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    resp = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": text[:2000]},
        timeout=15,
    )
    resp.raise_for_status()


def _send_line_messaging_api(text: str) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_TO_USER_ID:
        return
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": LINE_TO_USER_ID,
            "messages": [{"type": "text", "text": text[:5000]}],
        },
        timeout=15,
    )
    resp.raise_for_status()


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "kaigo-family-relay",
            "channels": {
                "slack": bool(SLACK_WEBHOOK_URL),
                "discord": bool(DISCORD_WEBHOOK_URL),
                "line_messaging_api": bool(LINE_CHANNEL_ACCESS_TOKEN and LINE_TO_USER_ID),
            },
        }
    )


@app.post("/kaigo/notify")
def kaigo_notify():
    if not _check_secret():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    text = _format_message(data)
    app.logger.info("notify event=%s", data.get("event"))

    senders = []
    if SLACK_WEBHOOK_URL:
        senders.append(("slack", _send_slack))
    if DISCORD_WEBHOOK_URL:
        senders.append(("discord", _send_discord))
    if LINE_CHANNEL_ACCESS_TOKEN and LINE_TO_USER_ID:
        senders.append(("line", _send_line_messaging_api))

    if not senders:
        return jsonify({"ok": True, "forwarded": False, "note": "no channels configured"})

    errors = []
    for name, fn in senders:
        try:
            fn(text)
        except Exception as e:
            errors.append(f"{name}: {e}")

    if len(errors) == len(senders):
        return jsonify({"ok": False, "errors": errors}), 502

    if errors:
        return jsonify({"ok": True, "forwarded": True, "warnings": errors})

    return jsonify({"ok": True, "forwarded": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
