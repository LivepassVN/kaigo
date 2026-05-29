"""
kaigo_core — リマインダー Background Daemon

kaigo_reminders.json をポーリングし、時刻になったら音声で知らせる。
"""

import json
from datetime import datetime
from time import time
from zoneinfo import ZoneInfo

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

REMINDERS_FILE = "kaigo_reminders.json"
POLL_SECONDS = 30.0


class KaigoCoreBackground(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None
    background_daemon_mode: bool = False

    #{{register capability}}

    async def _read_reminders(self):
        if not await self.capability_worker.check_if_file_exists(REMINDERS_FILE, in_ability_directory=False):
            return []
        raw = await self.capability_worker.read_file(REMINDERS_FILE, in_ability_directory=False)
        if not (raw or "").strip():
            return []
        try:
            data = json.loads(raw)
            items = data.get("reminders", [])
            return items if isinstance(items, list) else []
        except Exception as e:
            self.worker.editor_logging_handler.error(f"kaigo reminders parse error: {e}")
            return []

    async def _write_reminders(self, reminders: list) -> None:
        payload = json.dumps({"reminders": reminders}, ensure_ascii=False, indent=2)
        if await self.capability_worker.check_if_file_exists(REMINDERS_FILE, in_ability_directory=False):
            await self.capability_worker.delete_file(REMINDERS_FILE, in_ability_directory=False)
        await self.capability_worker.write_file(REMINDERS_FILE, payload, in_ability_directory=False)

    def _parse_hm(self, value: str):
        if not value or ":" not in value:
            return None
        parts = value.strip().split(":")
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None

    async def _fire_reminder(self, reminder: dict, today: str) -> None:
        label = reminder.get("label", "予定")
        msg = f"おしらせです。{label}のじかんです。"
        # Background から send_interrupt_signal() すると Agent が無音で固まることがあるため speak のみ
        await self.capability_worker.speak(msg)
        reminder["last_fired_date"] = today
        self.worker.editor_logging_handler.info(f"kaigo reminder fired: {reminder.get('id')} {label}")

    async def watch_loop(self) -> None:
        self.worker.editor_logging_handler.info(f"{time()}: kaigo_core background started")

        while True:
            try:
                tz_name = self.capability_worker.get_timezone()
                try:
                    tz = ZoneInfo(tz_name)
                except Exception:
                    tz = ZoneInfo("Asia/Tokyo")

                now = datetime.now(tz=tz)
                today = now.strftime("%Y-%m-%d")
                weekday = now.weekday()

                reminders = await self._read_reminders()
                changed = False

                for reminder in reminders:
                    if not reminder.get("enabled"):
                        continue
                    days = reminder.get("days") or list(range(7))
                    if weekday not in days:
                        continue
                    if reminder.get("last_fired_date") == today:
                        continue

                    hm = self._parse_hm(reminder.get("time", ""))
                    if not hm:
                        continue
                    h, m = hm
                    if now.hour == h and now.minute == m:
                        await self._fire_reminder(reminder, today)
                        changed = True

                if changed:
                    await self._write_reminders(reminders)

            except Exception as e:
                self.worker.editor_logging_handler.error(f"kaigo background error: {e}")

            await self.worker.session_tasks.sleep(POLL_SECONDS)

    def call(self, worker: AgentWorker, background_daemon_mode: bool):
        self.worker = worker
        self.background_daemon_mode = background_daemon_mode
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.watch_loop())
