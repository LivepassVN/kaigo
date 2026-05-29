"""
kaigo_core — ルーティン・リマインダー・傾聴対話・思い出・緊急・kaigo_persona.md

OpenHome Dashboard で Skill / Background Daemon として 2 ファイルを登録:
  - main.py      → Skill
  - background.py → Background Daemon

推奨トリガー: かいご / 今日 / お薬 / 思い出 / 天気 / 話したい / 覚えてる / 助けて
"""

import json
import re
from datetime import datetime
from time import time
from zoneinfo import ZoneInfo

import requests

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

PERSONA_FILE = "kaigo_persona.md"
REMINDERS_FILE = "kaigo_reminders.json"
EPISODES_FILE = "kaigo_episodes.jsonl"
LOCATION_FILE = "kaigo_location.json"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SEC = 12

DEFAULT_LOCATION = {
    "label": "えどがわく",
    "latitude": 35.7064,
    "longitude": 139.8683,
    "name": "東京都江戸川区",
}

# Open-Meteo WMO weather codes → TTS 向けひらがな
WMO_HIRA = {
    0: "はれ",
    1: "おおむねはれ",
    2: "ところどころくもり",
    3: "くもり",
    45: "きり",
    48: "きり",
    51: "きりさめ",
    53: "きりさめ",
    55: "きりさめ",
    56: "あらあめ",
    57: "あらあめ",
    61: "よわいあめ",
    63: "あめ",
    65: "つよいあめ",
    66: "あらあめ",
    67: "つよいあらあめ",
    71: "ゆき",
    73: "ゆき",
    75: "おおゆき",
    77: "ゆきあられ",
    80: "にわかあめ",
    81: "にわかあめ",
    82: "つよいにわかあめ",
    85: "にわかゆき",
    86: "つよいにわかゆき",
    95: "らい",
    96: "らい",
    99: "つよいらい",
}

_KANJI_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

_TTS_SAFE_SYSTEM = (
    "Elderly care voice output for broken TTS. NO kanji. "
    "Native Japanese words in hiragana. Loanwords in katakana (サンドイッチ, スープ) — never hiragana loanwords. "
    "Max 2 warm sentences. "
    "Example: おひるごはんには、やさいのサンドイッチや、あたたかいスープもいかがですか。"
)

_TTS_FIX_SYSTEM = (
    "Rewrite for TTS. Remove ALL kanji (use hiragana). "
    "Keep or fix loanwords to katakana (NOT hiragana): サンドイッチ not さんどいっち, スープ not すうぷ. "
    "Output the rewritten text only, no explanation."
)

_CHAT_SYSTEM = (
    "You are Kaigo, a warm voice companion for an elderly person living alone. "
    "Listen empathetically. Reply in 1-2 short sentences. NO kanji — hiragana only, loanwords in katakana. "
    "Use the persona and past episodes in context when relevant. Do not give medical advice. "
    "If they seem lonely, stay with them gently. Never rush."
)

_RECALL_SYSTEM = (
    "Summarize the user's recent conversation snippets for them, warmly, in 1-2 hiragana sentences. "
    "NO kanji. Help them feel their stories are remembered."
)

_TOPIC_SYSTEM = (
    "Suggest one gentle conversation topic for an elderly person. "
    "Use persona favorite topics or time of day if given. ONE short question, hiragana only, NO kanji."
)


def _has_kanji(text: str) -> bool:
    return bool(_KANJI_RE.search(text or ""))


EMERGENCY_PATTERNS = (
    "助けて",
    "たすけて",
    "痛い",
    "いたい",
    "倒れた",
    "倒れ",
    "苦しい",
    "くるしい",
    "救急",
    "火事",
)

DEFAULT_REMINDERS = {
    "reminders": [
        {
            "id": "med_morning",
            "label": "あさのおくすり",
            "time": "08:00",
            "days": [0, 1, 2, 3, 4, 5, 6],
            "enabled": True,
            "last_fired_date": None,
        },
        {
            "id": "lunch",
            "label": "おひるごはん",
            "time": "12:00",
            "days": [0, 1, 2, 3, 4, 5, 6],
            "enabled": True,
            "last_fired_date": None,
        },
        {
            "id": "water_afternoon",
            "label": "すいぶほきゅう",
            "time": "15:00",
            "days": [0, 1, 2, 3, 4, 5, 6],
            "enabled": True,
            "last_fired_date": None,
        },
    ]
}

_MONTHS_HIRA = (
    "",
    "いちがつ",
    "にがつ",
    "さんがつ",
    "しがつ",
    "ごがつ",
    "ろくがつ",
    "しちがつ",
    "はちがつ",
    "くがつ",
    "じゅうがつ",
    "じゅういちがつ",
    "じゅうにがつ",
)
_WEEKDAYS_HIRA = (
    "げつようび",
    "かようび",
    "すいようび",
    "もくようび",
    "きんようび",
    "どようび",
    "にちようび",
)
_DIGITS_HIRA = ("れい", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう")


def _num_hira(n: int) -> str:
    if n < 0:
        return str(n)
    if n < 10:
        return _DIGITS_HIRA[n]
    if n < 20:
        return "じゅう" + (_DIGITS_HIRA[n - 10] if n > 10 else "")
    if n < 100:
        tens, ones = divmod(n, 10)
        head = _DIGITS_HIRA[tens] + "じゅう" if tens > 1 else "じゅう"
        return head + (_DIGITS_HIRA[ones] if ones else "")
    return str(n)


def _clock_hira(hm: str) -> str:
    if not hm or ":" not in hm:
        return hm or ""
    parts = hm.strip().split(":")
    try:
        h, m = int(parts[0]), int(parts[1])
    except ValueError:
        return hm
    text = f"{_num_hira(h)}じ"
    if m:
        text += f"{_num_hira(m)}ふん"
    return text


class KaigoCoreCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None
    _last_spoken: str = ""

    #{{register capability}}

    async def _speak(self, msg: str) -> None:
        text = (msg or "").strip()
        if text:
            self._last_spoken = text
        await self.capability_worker.speak(msg)

    def _tz_now(self):
        tz_name = self.capability_worker.get_timezone()
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Asia/Tokyo")
        return datetime.now(tz=tz), tz_name

    async def _write_replace_file(self, filename: str, content: str) -> None:
        if await self.capability_worker.check_if_file_exists(filename, in_ability_directory=False):
            await self.capability_worker.delete_file(filename, in_ability_directory=False)
        await self.capability_worker.write_file(filename, content, in_ability_directory=False)

    async def _read_json(self, filename: str, default):
        if not await self.capability_worker.check_if_file_exists(filename, in_ability_directory=False):
            return default
        raw = await self.capability_worker.read_file(filename, in_ability_directory=False)
        if not (raw or "").strip():
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.worker.editor_logging_handler.warning(f"Corrupt JSON: {filename}")
            return default

    async def _write_json(self, filename: str, data) -> None:
        await self._write_replace_file(
            filename,
            json.dumps(data, ensure_ascii=False, indent=2),
        )

    async def _ensure_reminders(self):
        data = await self._read_json(REMINDERS_FILE, None)
        if not data or not isinstance(data.get("reminders"), list):
            await self._write_json(REMINDERS_FILE, DEFAULT_REMINDERS)
            return DEFAULT_REMINDERS
        return data

    async def _ensure_persona(self):
        if not await self.capability_worker.check_if_file_exists(PERSONA_FILE, in_ability_directory=False):
            template = await self._read_persona_template()
            await self._write_replace_file(PERSONA_FILE, template)
        await self._ensure_location()

    async def _read_persona_template(self) -> str:
        return """# kaigo_persona

## 呼び名
（未設定）

## 好きな話題
- （これから記録）

## 避ける話題
- （これから記録）

## 居住地
（未設定）

## 口調メモ
- ゆっくり、はっきり、温かみのある敬語
- 標準語。地名は正しい読みで（青森＝あおもり）
"""

    async def _append_episode(self, trigger: str, snippet: str) -> None:
        now, _ = self._tz_now()
        line = json.dumps(
            {
                "date": now.strftime("%Y-%m-%d"),
                "trigger": trigger,
                "transcript_snippet": (snippet or "")[:500],
                "image_path": None,
                "mood": None,
            },
            ensure_ascii=False,
        )
        await self.capability_worker.write_file(EPISODES_FILE, line + "\n", in_ability_directory=False)

    async def _read_episodes_raw(self) -> str:
        if not await self.capability_worker.check_if_file_exists(EPISODES_FILE, in_ability_directory=False):
            return ""
        raw = await self.capability_worker.read_file(EPISODES_FILE, in_ability_directory=False)
        return (raw or "").strip()

    async def _read_recent_episodes(self, limit: int = 8) -> list:
        raw = await self._read_episodes_raw()
        if not raw:
            return []
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows[-limit:]

    async def _read_persona_text(self) -> str:
        if not await self.capability_worker.check_if_file_exists(PERSONA_FILE, in_ability_directory=False):
            return ""
        raw = await self.capability_worker.read_file(PERSONA_FILE, in_ability_directory=False)
        return (raw or "").strip()

    def _parse_persona_name(self, persona: str) -> str:
        m = re.search(r"## 呼び名\s*\n(.+?)(?:\n##|\Z)", persona, re.DOTALL)
        if not m:
            return ""
        name = m.group(1).strip().split("\n")[0].strip()
        if not name or name in ("（未設定）", "(未設定)"):
            return ""
        return name.replace("さん", "").strip()

    async def _build_dialogue_context(self) -> str:
        parts = []
        persona = await self._read_persona_text()
        if persona:
            parts.append(f"[persona]\n{persona[:800]}")
        episodes = await self._read_recent_episodes(6)
        voice_eps = [
            e
            for e in episodes
            if e.get("trigger") in ("voice", "memory", "weather") and (e.get("transcript_snippet") or "").strip()
        ]
        if voice_eps:
            lines = [
                f"- {e.get('date', '?')}: {(e.get('transcript_snippet') or '')[:120]}"
                for e in voice_eps[-5:]
            ]
            parts.append("[recent episodes]\n" + "\n".join(lines))
        now, _ = self._tz_now()
        parts.append(f"[now] {now.strftime('%Y-%m-%d %H:%M')}")
        return "\n\n".join(parts)

    def _is_greeting_only(self, text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return True
        stripped = t
        for k in ("おはよう", "こんにちは", "こんばんは", "かいご", "こんにちわ"):
            stripped = stripped.replace(k, "")
        stripped = re.sub(r"[、。.！!？?\s]", "", stripped)
        return len(stripped) < 2

    def _wants_recall(self, text: str) -> bool:
        t = text or ""
        return any(
            k in t
            for k in (
                "覚えてる",
                "覚えている",
                "おぼえて",
                "前に話",
                "前の話",
                "最近の話",
                "記録して",
                "何話した",
                "なに話した",
            )
        )

    def _wants_chat(self, text: str) -> bool:
        t = text or ""
        return any(
            k in t
            for k in (
                "話したい",
                "話し相手",
                "はなしたい",
                "退屈",
                "つまらない",
                "寂しい",
                "さみしい",
                "なんか話",
                "何か話",
                "付き合",
                "つきあって",
                "陪って",
                "おしゃべり",
            )
        )

    def _wants_repeat(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("もう一度", "もういちど", "聞こえ", "きこえ", "なんて言", "何て言"))

    def _wants_goodbye(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("さようなら", "またね", "おやすみ", "バイバイ", "ばいばい", "終わり", "終了"))

    def _is_emergency(self, text: str) -> bool:
        t = (text or "").strip()
        return any(p in t for p in EMERGENCY_PATTERNS)

    def _wants_weather(self, text: str) -> bool:
        t = text or ""
        return any(
            k in t
            for k in (
                "天気",
                "てんき",
                "気温",
                "きおん",
                "降水",
                "雨",
                "あめ",
                "雪",
                "ゆき",
                "暑",
                "寒",
                "熱中",
            )
        )

    def _wants_datetime(self, text: str) -> bool:
        t = text or ""
        if self._wants_weather(t) or self._wants_reminders(t):
            return False
        return any(
            k in t for k in ("何曜日", "何日", "日付", "今日", "きょう", "曜日", "何時", "今何時")
        )

    def _wants_reminders(self, text: str) -> bool:
        t = text or ""
        return any(
            k in t
            for k in (
                "リマインダー",
                "お薬",
                "服薬",
                "薬の時間",
                "予定",
                "アラーム",
                "水分",
                "食事",
                "ごはん",
                "水を",
            )
        )

    def _wants_memory(self, text: str) -> bool:
        t = text or ""
        return any(k in t for k in ("思い出", "昔", "記録", "覚えて"))

    def _wants_name_update(self, text: str) -> bool:
        return "呼んで" in (text or "") or "名前は" in (text or "")

    async def _ensure_location(self):
        data = await self._read_json(LOCATION_FILE, None)
        if not data or data.get("latitude") is None or data.get("longitude") is None:
            await self._write_json(LOCATION_FILE, DEFAULT_LOCATION)
            return DEFAULT_LOCATION
        return data

    def _fetch_weather(self, lat: float, lon: float) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation",
            "timezone": "Asia/Tokyo",
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT_SEC)
        resp.raise_for_status()
        return resp.json()

    def _weather_description(self, code: int) -> str:
        return WMO_HIRA.get(int(code), "くもり")

    def _build_weather_speech(self, payload: dict, label: str) -> str:
        current = payload.get("current") or {}
        temp = current.get("temperature_2m")
        code = int(current.get("weather_code") or 0)
        precip = float(current.get("precipitation") or 0)
        desc = self._weather_description(code)

        parts = [f"きょうの{label}のてんきは、{desc}です。"]
        if temp is not None:
            parts.append(f"きおんは{_num_hira(int(round(temp)))}どくらいです。")

        if code in (71, 73, 75, 77, 85, 86) or precip >= 1.0:
            parts.append("ゆきやあめにごちゅういください。")
        elif code in (61, 63, 65, 80, 81, 82, 95, 96, 99):
            parts.append("かさがあるとあんしんです。")
        elif temp is not None and temp >= 30:
            parts.append("あついので、すいぶほきゅうをわすれずに。")
        elif temp is not None and temp <= 3:
            parts.append("さむいので、あたたかくしてください。")

        return "".join(parts[:3])

    async def _speak_weather(self) -> None:
        loc = await self._ensure_location()
        label = (loc.get("label") or "ちほう").strip() or "ちほう"
        try:
            lat = float(loc["latitude"])
            lon = float(loc["longitude"])
            payload = self._fetch_weather(lat, lon)
            msg = self._build_weather_speech(payload, label)
            await self._speak(msg)
            await self._append_episode("weather", msg[:200])
        except requests.RequestException as e:
            self.worker.editor_logging_handler.error(f"weather API error: {e}")
            await self._speak(
                "てんきをしらべられませんでした。"
                "インターネットにつながっているか、あとでもういちどきいてください。"
            )
        except Exception as e:
            self.worker.editor_logging_handler.error(f"weather error: {e}")
            await self._speak("てんきのじょうほうがよみとれませんでした。")

    async def _speak_datetime(self) -> None:
        now, _ = self._tz_now()
        wd = _WEEKDAYS_HIRA[now.weekday()]
        msg = (
            f"きょうは{_MONTHS_HIRA[now.month]}{_num_hira(now.day)}にち、{wd}です。"
            f"いまは{_num_hira(now.hour)}じ{_num_hira(now.minute)}ふんごろです。"
        )
        await self._speak(msg)

    async def _speak_reminders(self, user_text: str = "") -> None:
        data = await self._ensure_reminders()
        enabled = [r for r in data.get("reminders", []) if r.get("enabled")]
        if not enabled:
            await self._speak("ゆうこうなリマインダーはありません。")
            return

        t = user_text or ""
        med_focus = any(k in t for k in ("お薬", "服薬", "薬"))
        if med_focus:
            enabled = [
                r
                for r in enabled
                if "薬" in (r.get("label") or "") or str(r.get("id", "")).startswith("med")
            ] or enabled

        parts = []
        for r in enabled[:5]:
            parts.append(f"{_clock_hira(r.get('time', '??:??'))}に{r.get('label', 'よてい')}")

        if med_focus:
            prefix = "おくすりのじかんです。"
        else:
            prefix = "よていです。"

        await self._speak(prefix + "。".join(parts) + "。")

    async def _handle_memory(self, user_text: str) -> None:
        await self._speak("そうですね。たいせつなことを、みじかくおしえてください。")
        memory = await self.capability_worker.user_response()
        if memory and memory.strip():
            await self._append_episode("memory", memory.strip())
            await self._speak("ありがとうございます。たいせつにおぼえておきますね。")
        else:
            await self._speak("また話したくなったら、こえをかけてください。")

    async def _handle_recall(self) -> None:
        episodes = await self._read_recent_episodes(10)
        snippets = [
            e
            for e in episodes
            if (e.get("transcript_snippet") or "").strip()
            and e.get("trigger") in ("voice", "memory", "weather")
        ]
        if not snippets:
            await self._speak(
                "まだお話のきろくはすくないです。"
                "きょうのできごとを、よければお聞かせください。"
            )
            return
        context = "\n".join(
            f"{e.get('date', '?')}: {(e.get('transcript_snippet') or '')[:150]}" for e in snippets[-6:]
        )
        raw = self.capability_worker.text_to_text_response(
            "最近の記録をやさしく思い出させて",
            [context],
            _RECALL_SYSTEM,
        )
        spoken = await self._to_tts_safe_speech((raw or "").strip(), context)
        if spoken:
            await self._speak(spoken)
        else:
            latest = snippets[-1].get("transcript_snippet", "")[:120]
            await self._speak(f"この前は、{latest}、というお話がありましたね。")

    async def _chat_respond(self, user_message: str) -> None:
        msg = (user_message or "").strip()
        if not msg:
            return
        context = await self._build_dialogue_context()
        spoken = await self._to_tts_safe_speech(msg, context, _CHAT_SYSTEM)
        if spoken:
            await self._speak(spoken)
        await self._append_episode("voice", msg[:500])

    async def _handle_chat(self, user_text: str = "") -> None:
        if (user_text or "").strip() and not self._is_greeting_only(user_text):
            await self._chat_respond(user_text)
            return
        await self._speak("はい、きいています。なにかお話しください。")
        reply = await self.capability_worker.user_response()
        if reply and reply.strip():
            await self._chat_respond(reply.strip())
        else:
            topic = await self._suggest_topic()
            if topic:
                await self._speak(topic)

    async def _suggest_topic(self) -> str:
        context = await self._build_dialogue_context()
        now, _ = self._tz_now()
        hint = "朝" if now.hour < 11 else "昼" if now.hour < 17 else "夜"
        raw = self.capability_worker.text_to_text_response(
            f"{hint}の時間帯",
            [context],
            _TOPIC_SYSTEM,
        )
        return await self._to_tts_safe_speech((raw or "").strip(), context, _TOPIC_SYSTEM)

    async def _handle_repeat(self) -> None:
        if self._last_spoken:
            await self._speak(self._last_spoken)
        else:
            await self._speak("さきほどのことばが、まだありません。なにかお話しください。")

    async def _handle_goodbye(self) -> None:
        persona = await self._read_persona_text()
        name = self._parse_persona_name(persona)
        suffix = f"{name}さん、" if name else ""
        await self._speak(
            f"{suffix}わかりました。"
            "またいつでも、こえをかけてくださいね。"
            "おだいじに。"
        )

    async def _handle_name_update(self, user_text: str) -> None:
        m = re.search(r"(?:呼んで|名前は)\s*(.+?)(?:です|だよ|と呼|で)?$", user_text.strip())
        name = (m.group(1).strip() if m else "") or user_text.strip()
        name = name.replace("ください", "").replace("お願い", "").strip()
        if len(name) > 20:
            name = name[:20]
        if not name:
            await self._speak("おなまえをもういちどおしえてください。")
            return
        content = f"""# kaigo_persona

## 呼び名
{name}

## 好きな話題
- （これから記録）

## 避ける話題
- （これから記録）

## 居住地
（未設定）

## 口調メモ
- ゆっくり、はっきり、温かみのある敬語
- 標準語。地名は正しい読みで（青森＝あおもり）
"""
        await self._write_replace_file(PERSONA_FILE, content)
        await self._speak(f"わかりました。{name}、とよびますね。")

    async def _handle_emergency(self, user_text: str = "") -> None:
        snippet = (user_text or "").strip()[:500] or "緊急キーワード検知"
        await self._append_episode("emergency", snippet)
        await self._speak(
            "だいじょうぶですか。つらいときは、いちいちきゅうばんかごかぞくにでんわしてください。"
            "わたしはいりょうききではないので、ちょくせつおたすけすることはできません。"
        )

    async def _handle_greeting(self, user_text: str) -> None:
        now, _ = self._tz_now()
        hour = now.hour
        if hour < 11:
            greet = "おはようございます。"
        elif hour < 17:
            greet = "こんにちは。"
        else:
            greet = "こんばんは。"
        persona = await self._read_persona_text()
        name = self._parse_persona_name(persona)
        if name:
            greet = f"{greet}{name}さん、"
        await self._speak(
            f"{greet}きょうもいっしょにいます。"
            "お話ししたいときは、そのまま話しかけてください。"
        )
        topic = await self._suggest_topic()
        if topic:
            await self._speak(topic)

    async def _to_tts_safe_speech(
        self, user_text: str, context: str = "", system: str = _TTS_SAFE_SYSTEM
    ) -> str:
        spoken = self.capability_worker.text_to_text_response(
            user_text, [context] if context else [], system
        )
        spoken = (spoken or "").strip()[:200]
        if _has_kanji(spoken):
            spoken = self.capability_worker.text_to_text_response(
                spoken, [], _TTS_FIX_SYSTEM
            )
            spoken = (spoken or "").strip()[:200]
        return spoken

    async def run(self) -> None:
        try:
            await self._ensure_persona()
            await self._ensure_reminders()

            user_text = await self.capability_worker.wait_for_complete_transcription()
            self.worker.editor_logging_handler.info(f"kaigo_core: {user_text}")

            if self._is_emergency(user_text):
                await self._handle_emergency(user_text)
                return

            if self._wants_repeat(user_text):
                await self._handle_repeat()
                return

            if self._wants_goodbye(user_text):
                await self._handle_goodbye()
                return

            if self._wants_recall(user_text):
                await self._handle_recall()
                return

            if self._wants_weather(user_text):
                await self._speak_weather()
            elif self._wants_reminders(user_text):
                await self._speak_reminders(user_text)
            elif self._wants_datetime(user_text):
                await self._speak_datetime()
            elif self._wants_memory(user_text):
                await self._handle_memory(user_text)
                return
            elif self._wants_name_update(user_text):
                await self._handle_name_update(user_text)
            elif self._wants_chat(user_text):
                await self._handle_chat(user_text)
                return
            elif self._is_greeting_only(user_text):
                await self._handle_greeting(user_text)
            elif (user_text or "").strip():
                await self._handle_chat(user_text)
            else:
                await self._handle_chat("")
        except Exception as e:
            self.worker.editor_logging_handler.error(f"kaigo_core error: {e}")
            try:
                await self._speak("すみません。うまくいきませんでした。")
            except Exception:
                pass
        finally:
            self.capability_worker.resume_normal_flow()

    def call(self, worker: AgentWorker):
        self.worker = worker
        self.capability_worker = CapabilityWorker(self)
        self.worker.session_tasks.create(self.run())
