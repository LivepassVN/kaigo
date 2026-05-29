"""
kaigo_journal — 日次ジャーナル JSON 保存 + エピソード連携

推奨トリガー: ジャーナル / 今日の記録 / 日記 / きょうの記録
"""

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

EPISODES_FILE = "kaigo_episodes.jsonl"
_KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

_SUMMARY_SYSTEM = (
    "Summarize the user's day in 1-2 warm sentences for an elderly care journal. "
    "Output hiragana only, NO kanji. Loanwords in katakana."
)

_TTS_FIX = "Rewrite in hiragana only, no kanji. Output text only."


class KaigoJournalCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    #{{register capability}}

    def _today_key(self) -> str:
        tz_name = self.capability_worker.get_timezone()
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Asia/Tokyo")
        return datetime.now(tz=tz).strftime("%Y-%m-%d")

    def _daily_filename(self) -> str:
        return f"kaigo_daily_{self._today_key()}.json"

    async def _write_replace(self, filename: str, content: str) -> None:
        if await self.capability_worker.check_if_file_exists(filename, in_ability_directory=False):
            await self.capability_worker.delete_file(filename, in_ability_directory=False)
        await self.capability_worker.write_file(filename, content, in_ability_directory=False)

    async def _append_episode(self, snippet: str) -> None:
        today = self._today_key()
        line = json.dumps(
            {
                "date": today,
                "trigger": "journal",
                "transcript_snippet": (snippet or "")[:500],
                "image_path": None,
                "mood": None,
            },
            ensure_ascii=False,
        )
        await self.capability_worker.write_file(EPISODES_FILE, line + "\n", in_ability_directory=False)

    def _tts_safe(self, text: str) -> str:
        spoken = (text or "").strip()[:300]
        if _KANJI_RE.search(spoken):
            spoken = self.capability_worker.text_to_text_response(spoken, [], _TTS_FIX)
            spoken = (spoken or "").strip()[:300]
        return spoken

    async def run(self) -> None:
        try:
            await self.capability_worker.wait_for_complete_transcription()
            await self.capability_worker.speak("きょうのことを、みじかく教えてください。")
            entry = await self.capability_worker.user_response()

            if not (entry or "").strip():
                await self.capability_worker.speak("また話したくなったら、こえをかけてください。")
                return

            summary = self.capability_worker.text_to_text_response(
                entry.strip(), [], _SUMMARY_SYSTEM
            )
            summary = self._tts_safe(summary.strip()[:1000])

            today = self._today_key()
            payload = {
                "date": today,
                "summary": summary,
                "highlights": [entry.strip()[:200]],
                "device_events": [],
            }
            await self._write_replace(
                self._daily_filename(),
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            await self._append_episode(entry.strip())
            await self.capability_worker.speak("きょうのきろくを残しました。ありがとうございます。")
            if summary:
                await self.capability_worker.speak(f"きろくは、{summary[:120]}、ですね。")
        except Exception as e:
            self.worker.editor_logging_handler.error(f"kaigo_journal error: {e}")
            try:
                await self.capability_worker.speak("すみません。きろくを残せませんでした。")
            except Exception:
                pass
        finally:
            self.capability_worker.resume_normal_flow()

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
