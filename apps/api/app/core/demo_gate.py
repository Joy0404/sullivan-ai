"""Public-demo guard for real Gemini analysis.

Real analysis spends the server's Gemini quota, so on the public deployment it
runs only when the visitor (1) ticked the analysis consent, (2) typed the trial
code that matches ``DEMO_ACCESS_CODE`` and (3) has not used up the per-IP daily
allowance. Samples never pass through this gate.

The daily counter lives in process memory: it resets on restart/redeploy and
is exact only while the service runs as a single instance.
"""

import hmac
import os
import threading
from datetime import datetime, timedelta, timezone

from fastapi import Request

KST = timezone(timedelta(hours=9))
DEFAULT_DAILY_LIMIT = 3
DEFAULT_SAMPLE_VIDEO_IDS = ("R0dqsl3Vgns", "thJxqtTgSNY")
DEFAULT_ANALYSIS_TIMEOUT_SECONDS = 180

DAILY_LIMIT_MESSAGE = "오늘 체험 횟수를 모두 사용했어요. 내일 다시 시도해 주세요."
CONSENT_MESSAGE = "실제 AI 분석을 하려면 분석 동의에 직접 체크해 주세요."
CODE_MISSING_MESSAGE = "실제 AI 분석에는 체험 코드가 필요합니다. 샘플은 코드 없이 이용할 수 있어요."
CODE_WRONG_MESSAGE = "체험 코드가 올바르지 않습니다. 실제 분석은 실행하지 않았습니다."
DEMO_DISABLED_MESSAGE = "이 서버에는 체험 코드가 설정되지 않아 실제 AI 분석을 사용할 수 없습니다. 샘플은 그대로 이용할 수 있어요."
KEY_MISSING_MESSAGE = "서버에 Gemini API 키가 설정되지 않아 실제 AI 분석을 실행하지 않았습니다."
SAMPLE_ONLY_MESSAGE = "공개 체험에서는 지정된 샘플 YouTube 영상만 실제 분석할 수 있습니다."


class DemoGateError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def server_gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def analysis_timeout_seconds() -> float:
    try:
        return float(os.getenv("ANALYSIS_TIMEOUT_SECONDS", DEFAULT_ANALYSIS_TIMEOUT_SECONDS))
    except ValueError:
        return float(DEFAULT_ANALYSIS_TIMEOUT_SECONDS)


def allowed_sample_video_ids() -> set[str]:
    raw = os.getenv("ALLOWED_SAMPLE_VIDEO_IDS", "")
    ids = {item.strip() for item in raw.split(",") if item.strip()}
    return ids or set(DEFAULT_SAMPLE_VIDEO_IDS)


def check_access_code(submitted: str | None) -> None:
    """Raise unless the submitted trial code matches DEMO_ACCESS_CODE."""
    expected = os.getenv("DEMO_ACCESS_CODE", "").strip()
    if not expected:
        raise DemoGateError(503, DEMO_DISABLED_MESSAGE)
    candidate = (submitted or "").strip()
    if not candidate:
        raise DemoGateError(401, CODE_MISSING_MESSAGE)
    if not hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8")):
        raise DemoGateError(403, CODE_WRONG_MESSAGE)


def client_ip(request: Request) -> str:
    """Best-effort visitor IP behind Railway's proxy.

    Railway's edge sets ``X-Real-IP``. Without it, the right-most
    ``X-Forwarded-For`` entry is the one added by the closest proxy, so a
    visitor cannot spoof it by sending their own header.
    """
    header_name = os.getenv("CLIENT_IP_HEADER", "X-Real-IP")
    direct = request.headers.get(header_name, "").strip()
    if direct:
        return direct
    forwarded = [part.strip() for part in request.headers.get("X-Forwarded-For", "").split(",") if part.strip()]
    if forwarded:
        return forwarded[-1]
    return request.client.host if request.client else "unknown"


class DailyUsageLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._day = ""
        self._counts: dict[str, int] = {}

    @staticmethod
    def limit() -> int:
        try:
            return max(0, int(os.getenv("DEMO_DAILY_LIMIT", DEFAULT_DAILY_LIMIT)))
        except ValueError:
            return DEFAULT_DAILY_LIMIT

    def _roll_day(self) -> None:
        today = datetime.now(KST).strftime("%Y-%m-%d")
        if today != self._day:
            self._day = today
            self._counts = {}

    def ensure_available(self, ip: str) -> None:
        with self._lock:
            self._roll_day()
            if self._counts.get(ip, 0) >= self.limit():
                raise DemoGateError(429, DAILY_LIMIT_MESSAGE)

    def consume(self, ip: str) -> int:
        """Record one started analysis; returns the remaining count."""
        with self._lock:
            self._roll_day()
            used = self._counts.get(ip, 0)
            if used >= self.limit():
                raise DemoGateError(429, DAILY_LIMIT_MESSAGE)
            self._counts[ip] = used + 1
            return self.limit() - used - 1

    def reset(self) -> None:
        with self._lock:
            self._day = ""
            self._counts = {}


limiter = DailyUsageLimiter()
