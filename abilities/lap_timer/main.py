"""
lap_timer — RC サーキットラップタイマー（DevKit + USB カメラのみで完結）

OpenHome Dashboard で Local Ability として登録:
  - main.py
  - devkit_functions.py
  - requirements.txt

推奨トリガー: タイム計測 / ラップタイム / 計測開始 / 計測停止 / ベスト / リセット
"""

import json

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

LAPS_FILE = "lap_timer_laps.json"
POLL_INTERVAL_SEC = 0.45
SESSION_MAX_SEC = 600
MAX_LAPS = 20


class LapTimerCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    #{{register capability}}

    def _parse_devkit_output(self, result: dict) -> dict:
        if not isinstance(result, dict):
            return {"success": False, "spoken_response": "DevKit 応答がありません。"}
        output = (result.get("output") or "").strip()
        if not output:
            return {"success": False, "spoken_response": "DevKit 応答が空です。"}
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"success": False, "spoken_response": "DevKit 応答の解析に失敗しました。"}

    async def _call_devkit(
        self, function_name: str, args: list | None = None, timeout: int = 15
    ) -> dict:
        result = await self.capability_worker.send_devkit_capability_action(
            function_name=function_name,
            args=args or [],
            timeout=timeout,
        )
        return self._parse_devkit_output(result)

    def _format_lap_speech(self, lap: dict, best_sec: float | None) -> str:
        n = lap.get("n", "?")
        sec = float(lap.get("sec", 0))
        msg = f"{n}周目、{sec:.1f}秒です。"
        if best_sec is not None and abs(sec - best_sec) < 0.05:
            msg += "ベスト更新です。"
        return msg

    async def _persist_laps(self, laps: list, best_sec: float | None) -> None:
        payload = json.dumps(
            {"laps": laps, "best_sec": best_sec},
            ensure_ascii=False,
            indent=2,
        )
        if await self.capability_worker.check_if_file_exists(LAPS_FILE, in_ability_directory=False):
            await self.capability_worker.delete_file(LAPS_FILE, in_ability_directory=False)
        await self.capability_worker.write_file(LAPS_FILE, payload, in_ability_directory=False)

    def _wants_stop(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("計測停止", "停止", "止めて", "ストップ", "終了"))

    def _wants_reset(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("リセット", "クリア", "記録消去"))

    def _wants_best(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("ベスト", "最高", "最速", "記録"))

    def _wants_start(self, text: str) -> bool:
        t = text or ""
        return any(
            k in t
            for k in (
                "タイム計測",
                "ラップタイム",
                "ラップ",
                "計測開始",
                "計測",
                "スタート",
            )
        )

    async def _speak_best(self) -> None:
        status = await self._call_devkit("poll_status", [], timeout=10)
        data = (status.get("data") or {}) if status.get("success") else {}
        best = data.get("best_sec")
        count = int(data.get("lap_count") or 0)
        if best is None or count == 0:
            await self.capability_worker.speak("まだ記録がありません。")
            return
        await self.capability_worker.speak(f"ベストラップは{best:.1f}秒です。全{count}周です。")

    async def _handle_reset(self) -> None:
        payload = await self._call_devkit("reset_session", [], timeout=15)
        await self.capability_worker.speak(
            payload.get("spoken_response") or "リセットしました。"
        )

    async def _handle_stop(self) -> None:
        payload = await self._call_devkit("stop_monitor", [], timeout=20)
        data = payload.get("data") or {}
        laps = data.get("laps") or []
        best = data.get("best_sec")
        await self._persist_laps(laps, best)
        await self.capability_worker.speak(
            payload.get("spoken_response") or "計測を止めました。"
        )

    async def _run_session(self) -> None:
        started = await self._call_devkit(
            "start_monitor",
            ["0.55", "4.0", "/dev/video0", "640", "480", "0.06"],
            timeout=20,
        )
        if not started.get("success"):
            await self.capability_worker.speak(
                started.get("spoken_response") or "計測を開始できませんでした。"
            )
            return

        await self.capability_worker.speak(
            started.get("spoken_response")
            or "計測を開始しました。ゴールラインを越えてください。"
        )

        known_count = 0
        elapsed = 0.0
        polls = int(SESSION_MAX_SEC / POLL_INTERVAL_SEC)

        for _ in range(polls):
            await self.worker.session_tasks.sleep(POLL_INTERVAL_SEC)
            elapsed += POLL_INTERVAL_SEC

            status = await self._call_devkit("poll_status", [], timeout=10)
            if not status.get("success"):
                continue

            data = status.get("data") or {}
            if data.get("error"):
                await self.capability_worker.speak("カメラエラーが発生しました。計測を止めます。")
                break

            lap_count = int(data.get("lap_count") or 0)
            if lap_count > known_count:
                last_lap = data.get("last_lap")
                best_sec = data.get("best_sec")
                if last_lap:
                    await self.capability_worker.speak(
                        self._format_lap_speech(last_lap, best_sec)
                    )
                known_count = lap_count
                await self._persist_laps(data.get("laps") or [], data.get("best_sec"))

            if lap_count >= MAX_LAPS:
                await self.capability_worker.speak(f"{MAX_LAPS}周に達したので計測を終了します。")
                break

            if not data.get("running") and elapsed > 5:
                break

        stopped = await self._call_devkit("stop_monitor", [], timeout=20)
        data = stopped.get("data") or {}
        await self._persist_laps(data.get("laps") or [], data.get("best_sec"))
        if stopped.get("spoken_response"):
            await self.capability_worker.speak(stopped["spoken_response"])

    async def run(self) -> None:
        try:
            user_text = await self.capability_worker.wait_for_complete_transcription()
            self.worker.editor_logging_handler.info(f"lap_timer: {user_text}")

            if self._wants_reset(user_text):
                await self._handle_reset()
            elif self._wants_stop(user_text):
                await self._handle_stop()
            elif self._wants_best(user_text):
                await self._speak_best()
            elif self._wants_start(user_text):
                await self._run_session()
            else:
                await self.capability_worker.speak(
                    "タイム計測、計測停止、ベスト、リセットが使えます。"
                )
        except Exception as e:
            self.worker.editor_logging_handler.error(f"lap_timer error: {e}")
            try:
                await self._call_devkit("stop_monitor", [], timeout=15)
            except Exception:
                pass
            try:
                await self.capability_worker.speak("すみません。うまくいきませんでした。")
            except Exception:
                pass
        finally:
            self.capability_worker.resume_normal_flow()

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
