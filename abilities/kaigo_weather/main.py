"""
kaigo_weather — 天気専用 Skill (Open-Meteo)

Dashboard で必ずトリガー語を登録してください:
  天気, てんき, 今日の天気

Web チャットで「天気」とだけ入力しても、トリガーが登録されていればこの Skill が走ります。
Agent 単体はリアルタイム天気を知りません — この Skill が API を読みます。

位置: kaigo_location.json（未作成なら江戸川区で初期化）
"""

import json

import requests

from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

LOCATION_FILE = "kaigo_location.json"
EPISODES_FILE = "kaigo_episodes.jsonl"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SEC = 12

DEFAULT_LOCATION = {
    "label": "えどがわく",
    "latitude": 35.7064,
    "longitude": 139.8683,
    "name": "東京都江戸川区",
}

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


class KaigoWeatherSkill(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    #{{register capability}}

    async def _read_json(self, path: str, default):
        try:
            raw = await self.capability_worker.read_file(path, in_ability_directory=False)
            if not raw:
                return default
            return json.loads(raw)
        except Exception:
            return default

    async def _write_json(self, path: str, data: dict) -> None:
        await self.capability_worker.write_file(
            path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", in_ability_directory=False
        )

    async def _append_episode(self, snippet: str) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        try:
            tz = ZoneInfo(self.capability_worker.get_timezone())
        except Exception:
            tz = ZoneInfo("Asia/Tokyo")
        now = datetime.now(tz=tz)
        line = json.dumps(
            {
                "date": now.strftime("%Y-%m-%d"),
                "trigger": "weather",
                "transcript_snippet": (snippet or "")[:500],
                "image_path": None,
                "mood": None,
            },
            ensure_ascii=False,
        )
        await self.capability_worker.write_file(EPISODES_FILE, line + "\n", in_ability_directory=False)

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
            await self.capability_worker.speak(msg)
            await self._append_episode(msg[:200])
        except requests.RequestException as e:
            self.worker.editor_logging_handler.error(f"weather API error: {e}")
            await self.capability_worker.speak(
                "てんきをしらべられませんでした。"
                "インターネットにつながっているか、あとでもういちどきいてください。"
            )
        except Exception as e:
            self.worker.editor_logging_handler.error(f"weather error: {e}")
            await self.capability_worker.speak("てんきのじょうほうがよみとれませんでした。")

    async def run(self) -> None:
        try:
            await self._speak_weather()
        except Exception as e:
            self.worker.editor_logging_handler.error(f"kaigo_weather error: {e}")
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
