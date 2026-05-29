"""
kaigo_vision — 声トリガー撮影（ELP USB カメラ / OpenCV）

Local Ability: main.py + devkit_functions.py
推奨トリガー: 写真を撮って / 写真
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

EPISODES_FILE = "kaigo_episodes.jsonl"


class KaigoVisionCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    #{{register capability}}

    def _today(self) -> str:
        tz_name = self.capability_worker.get_timezone()
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Asia/Tokyo")
        return datetime.now(tz=tz).strftime("%Y-%m-%d")

    async def _append_episode(self, image_path: str) -> None:
        line = json.dumps(
            {
                "date": self._today(),
                "trigger": "photo",
                "transcript_snippet": "",
                "image_path": image_path,
                "mood": None,
            },
            ensure_ascii=False,
        )
        await self.capability_worker.write_file(
            EPISODES_FILE, line + "\n", in_ability_directory=False
        )

    def _spoken_from_result(self, result: dict) -> str:
        if not isinstance(result, dict) or not result.get("success"):
            return "写真を撮れませんでした。カメラの接続を確認してください。"
        output = (result.get("output") or "").strip()
        if not output:
            return "写真を撮りました。"
        try:
            payload = json.loads(output)
            if payload.get("success"):
                return payload.get("spoken_response") or "写真を撮りました。"
        except json.JSONDecodeError:
            pass
        return "写真を撮りました。"

    async def run(self) -> None:
        await self.capability_worker.speak("写真を撮ります。")

        result = await self.capability_worker.send_devkit_capability_action(
            function_name="capture_snapshot",
            args=["640", "480"],
            timeout=30,
        )
        spoken = self._spoken_from_result(result)
        await self.capability_worker.speak(spoken)

        output = (result.get("output") or "").strip()
        try:
            payload = json.loads(output)
            path = payload.get("data", {}).get("path")
            if path:
                await self._append_episode(path)
        except json.JSONDecodeError:
            pass

        note = await self.capability_worker.user_response()
        if note and note.strip():
            line = json.dumps(
                {
                    "date": self._today(),
                    "trigger": "photo_voice",
                    "transcript_snippet": note.strip()[:500],
                    "image_path": None,
                    "mood": None,
                },
                ensure_ascii=False,
            )
            await self.capability_worker.write_file(
                EPISODES_FILE, line + "\n", in_ability_directory=False
            )

        self.capability_worker.resume_normal_flow()

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
