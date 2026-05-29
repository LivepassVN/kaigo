"""
kaigo 家族通知 — Webhook POST（fire-and-forget）

OpenHome Skill / Background の両方から import する。
zip アップロード時は main.py または background.py と同梱すること。

送信条件: enabled=true かつ consent_given=true かつ webhook_url 設定済み
"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional

import requests

FAMILY_FILE = "kaigo_family.json"
EPISODES_FILE = "kaigo_episodes.jsonl"
NOTIFY_TIMEOUT_SEC = 12

DEFAULT_FAMILY = {
    "enabled": False,
    "consent_given": False,
    "resident_label": "利用者",
    "webhook_url": "",
    "webhook_secret": "",
    "notify_on_emergency": True,
    "notify_daily_summary": True,
    "daily_summary_time": "21:00",
    "last_daily_sent_date": None,
}


async def _read_file(cw, filename: str) -> str:
    if not await cw.check_if_file_exists(filename, in_ability_directory=False):
        return ""
    raw = await cw.read_file(filename, in_ability_directory=False)
    return (raw or "").strip()


async def _write_replace(cw, filename: str, content: str) -> None:
    if await cw.check_if_file_exists(filename, in_ability_directory=False):
        await cw.delete_file(filename, in_ability_directory=False)
    await cw.write_file(filename, content, in_ability_directory=False)


async def ensure_family_config(cw) -> dict:
    raw = await _read_file(cw, FAMILY_FILE)
    if not raw:
        await _write_replace(
            cw,
            FAMILY_FILE,
            json.dumps(DEFAULT_FAMILY, ensure_ascii=False, indent=2),
        )
        return dict(DEFAULT_FAMILY)
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except Exception:
        data = dict(DEFAULT_FAMILY)
        await _write_replace(
            cw,
            FAMILY_FILE,
            json.dumps(data, ensure_ascii=False, indent=2),
        )
    merged = dict(DEFAULT_FAMILY)
    merged.update(data)
    return merged


async def save_family_config(cw, config: dict) -> None:
    await _write_replace(
        cw,
        FAMILY_FILE,
        json.dumps(config, ensure_ascii=False, indent=2),
    )


def _notify_allowed(config: dict, event: str) -> bool:
    if not config.get("enabled") or not config.get("consent_given"):
        return False
    url = (config.get("webhook_url") or "").strip()
    if not url:
        return False
    if event == "emergency" and not config.get("notify_on_emergency", True):
        return False
    if event == "daily_summary" and not config.get("notify_daily_summary", True):
        return False
    return True


def _parse_hm(value: str):
    if not value or ":" not in value:
        return None
    parts = value.strip().split(":")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


async def _post_webhook(worker, config: dict, payload: dict) -> bool:
    url = (config.get("webhook_url") or "").strip()
    secret = (config.get("webhook_secret") or "").strip()

    def _post():
        headers = {"Content-Type": "application/json", "User-Agent": "kaigo/1.0"}
        if secret:
            headers["X-Kaigo-Secret"] = secret
        resp = requests.post(url, json=payload, headers=headers, timeout=NOTIFY_TIMEOUT_SEC)
        resp.raise_for_status()

    try:
        await asyncio.to_thread(_post)
        worker.editor_logging_handler.info(f"family notify sent: {payload.get('event')}")
        return True
    except Exception as e:
        worker.editor_logging_handler.error(f"family notify failed: {e}")
        return False


def build_emergency_payload(config: dict, user_text: str, now: datetime) -> dict:
    label = (config.get("resident_label") or "利用者").strip() or "利用者"
    snippet = (user_text or "").strip()[:500]
    return {
        "event": "emergency",
        "timestamp": now.isoformat(),
        "resident_label": label,
        "message": f"【緊急】{label}さんから助けを求める声がありました。",
        "details": {
            "transcript_snippet": snippet or "緊急キーワード検知",
            "action_hint": "119番または家族・介護者へ連絡を確認してください。",
        },
    }


async def _read_today_episodes(cw, today: str) -> List[dict]:
    raw = await _read_file(cw, EPISODES_FILE)
    if not raw:
        return []
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("date") == today:
            rows.append(row)
    return rows


async def _read_daily_json(cw, today: str) -> Optional[dict]:
    filename = f"kaigo_daily_{today}.json"
    raw = await _read_file(cw, filename)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def build_daily_payload(config: dict, today: str, daily: Optional[dict], episodes: List[dict]) -> dict:
    label = (config.get("resident_label") or "利用者").strip() or "利用者"
    summary = ""
    highlights = []
    if daily:
        summary = (daily.get("summary") or "").strip()
        highlights = daily.get("highlights") or []

    emergency_today = [e for e in episodes if e.get("trigger") == "emergency"]
    voice_today = [e for e in episodes if e.get("trigger") == "voice"]

    if not summary and voice_today:
        snippets = [
            (e.get("transcript_snippet") or "").strip()
            for e in voice_today[-3:]
            if (e.get("transcript_snippet") or "").strip()
        ]
        summary = " / ".join(snippets)[:1000]

    if not summary:
        summary = "きょうの会話記録はまだありません。"

    message = f"【日次】{label}さん — {today}\n{summary[:800]}"
    if emergency_today:
        message = f"【日次・緊急あり】{label}さん — {today}\n{summary[:800]}"

    return {
        "event": "daily_summary",
        "timestamp": datetime.now().astimezone().isoformat(),
        "date": today,
        "resident_label": label,
        "message": message,
        "details": {
            "summary": summary[:1000],
            "highlights": highlights[:10],
            "episode_count": len(episodes),
            "emergency_count": len(emergency_today),
            "emergency_snippets": [
                (e.get("transcript_snippet") or "")[:200] for e in emergency_today
            ],
        },
    }


async def notify_emergency(worker, cw, user_text: str) -> bool:
    config = await ensure_family_config(cw)
    if not _notify_allowed(config, "emergency"):
        return False
    now = datetime.now().astimezone()
    payload = build_emergency_payload(config, user_text, now)
    return await _post_webhook(worker, config, payload)


async def notify_test(worker, cw) -> bool:
    config = await ensure_family_config(cw)
    if not _notify_allowed(config, "emergency"):
        return False
    now = datetime.now().astimezone()
    label = (config.get("resident_label") or "利用者").strip() or "利用者"
    payload = {
        "event": "test",
        "timestamp": now.isoformat(),
        "resident_label": label,
        "message": f"【テスト】{label}さんの kaigo 家族通知の接続テストです。",
        "details": {"note": "設定が正しければこのメッセージが届きます。"},
    }
    return await _post_webhook(worker, config, payload)


async def maybe_send_daily_summary(worker, cw, now: datetime) -> bool:
    config = await ensure_family_config(cw)
    if not _notify_allowed(config, "daily_summary"):
        return False

    today = now.strftime("%Y-%m-%d")
    if config.get("last_daily_sent_date") == today:
        return False

    hm = _parse_hm(config.get("daily_summary_time") or "21:00")
    if not hm:
        return False
    h, m = hm
    if now.hour != h or now.minute != m:
        return False

    daily = await _read_daily_json(cw, today)
    episodes = await _read_today_episodes(cw, today)
    payload = build_daily_payload(config, today, daily, episodes)
    sent = await _post_webhook(worker, config, payload)
    if sent:
        config["last_daily_sent_date"] = today
        await save_family_config(cw, config)
    return sent
