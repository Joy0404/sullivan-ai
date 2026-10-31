"""Durable, fail-closed access control for paid analysis and agent turns."""

from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import ipaddress
import math
import os
from pathlib import Path
import sqlite3

from fastapi import Request
from app.core import postgres_usage

KST = timezone(timedelta(hours=9))
DEFAULT_DAILY_LIMIT = 3
DEFAULT_SAMPLE_VIDEO_IDS = ("R0dqsl3Vgns", "thJxqtTgSNY")
DEFAULT_ANALYSIS_TIMEOUT_SECONDS = 180
MAX_VIDEO_BYTES = 100_000_000
DAILY_LIMIT_MESSAGE = "오늘 체험 횟수를 모두 사용했어요. 내일 다시 시도해 주세요."
CONSENT_MESSAGE = "실제 AI 분석을 하려면 분석 동의에 직접 체크해 주세요."
CODE_MISSING_MESSAGE = (
    "실제 AI 분석에는 체험 코드가 필요합니다. 샘플은 코드 없이 이용할 수 있어요."
)
CODE_WRONG_MESSAGE = "체험 코드가 올바르지 않습니다. 실제 분석은 실행하지 않았습니다."
DEMO_DISABLED_MESSAGE = "이 서버에는 체험 코드가 설정되지 않아 실제 AI 분석을 사용할 수 없습니다. 샘플은 그대로 이용할 수 있어요."
KEY_MISSING_MESSAGE = (
    "서버에 Gemini API 키가 설정되지 않아 실제 AI 분석을 실행하지 않았습니다."
)
SAMPLE_ONLY_MESSAGE = (
    "공개 체험에서는 지정된 샘플 YouTube 영상만 실제 분석할 수 있습니다."
)


class DemoGateError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def server_gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def analysis_timeout_seconds() -> float:
    try:
        value = float(
            os.getenv("ANALYSIS_TIMEOUT_SECONDS", DEFAULT_ANALYSIS_TIMEOUT_SECONDS)
        )
        return max(0.01, min(value, 180)) if math.isfinite(value) else 180.0
    except ValueError:
        return 180.0


def allowed_sample_video_ids() -> set[str]:
    raw = os.getenv("ALLOWED_SAMPLE_VIDEO_IDS", "")
    return {item.strip() for item in raw.split(",") if item.strip()} or set(
        DEFAULT_SAMPLE_VIDEO_IDS
    )


def check_access_code(submitted: str | None) -> None:
    expected = os.getenv("DEMO_ACCESS_CODE", "").strip()
    candidate = (submitted or "").strip()
    if not expected:
        raise DemoGateError(503, DEMO_DISABLED_MESSAGE)
    if not candidate:
        raise DemoGateError(401, CODE_MISSING_MESSAGE)
    if not hmac.compare_digest(candidate.encode(), expected.encode()):
        raise DemoGateError(403, CODE_WRONG_MESSAGE)


def client_ip(request: Request) -> str:
    # Render's public edge overwrites CF-Connecting-IP. Do not fall back to
    # caller-supplied X-Real-IP/True-Client-IP/X-Forwarded-For headers.
    if os.getenv("RENDER") == "true":
        if os.getenv("TRUST_RENDER_PROXY") != "1":
            raise DemoGateError(503, "Render 접속 IP 확인 설정이 필요합니다.")
        try:
            return str(
                ipaddress.ip_address(request.headers.get("cf-connecting-ip", ""))
            )
        except ValueError:
            raise DemoGateError(
                503, "접속 IP를 확인하지 못해 실제 분석을 중단했습니다."
            ) from None
    return request.client.host if request.client else "unknown"


def usage_day() -> str:
    return datetime.now(KST).date().isoformat()


def usage_path() -> Path:
    path = Path(os.getenv("DEMO_USAGE_DB", "data/demo_usage.sqlite"))
    if os.getenv("RENDER") == "true":
        raise DemoGateError(503, "실제 분석을 위한 DATABASE_URL 설정이 필요합니다.")
    return path


class DailyUsageLimiter:
    @staticmethod
    def limit() -> int:
        try:
            return max(0, min(3, int(os.getenv("DEMO_DAILY_LIMIT", "3"))))
        except ValueError:
            return 3

    def _access(self, ip: str, consume: bool) -> int:
        day = usage_day()  # one date per transaction, including midnight boundaries
        identity = hashlib.sha256(f"{day}:{ip}".encode()).hexdigest()
        limit = self.limit()
        if limit <= 0:
            raise DemoGateError(429, DAILY_LIMIT_MESSAGE)
        dsn = os.getenv("DATABASE_URL", "").strip()
        if dsn:
            try:
                used = postgres_usage.access(dsn, identity, day, limit, consume)
            except postgres_usage.UsageStorageError as error:
                raise DemoGateError(503, str(error)) from None
            if used is None:
                raise DemoGateError(429, DAILY_LIMIT_MESSAGE)
            return limit - used
        path = usage_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path, timeout=10)) as db, db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS usage (ip TEXT, day TEXT, count INTEGER NOT NULL, PRIMARY KEY(ip, day))"
                )
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    "SELECT count FROM usage WHERE ip=? AND day=?", (identity, day)
                ).fetchone()
                used = row[0] if row else 0
                if used >= self.limit():
                    raise DemoGateError(429, DAILY_LIMIT_MESSAGE)
                if consume:
                    db.execute(
                        "INSERT INTO usage VALUES (?, ?, 1) ON CONFLICT(ip, day) DO UPDATE SET count=count+1",
                        (identity, day),
                    )
                    db.execute("DELETE FROM usage WHERE day < ?", (day,))
                return self.limit() - used - int(consume)
        except (sqlite3.Error, OSError):
            raise DemoGateError(
                503, "체험 횟수를 확인할 수 없어 실제 분석을 중단했습니다."
            ) from None

    def ensure_available(self, ip: str) -> None:
        self._access(ip, False)

    def consume(self, ip: str) -> int:
        return self._access(ip, True)

    def reset(self) -> None:
        """Test/development helper; never reset quota on service startup."""
        if os.getenv("RENDER") == "true" or os.getenv("DATABASE_URL"):
            raise DemoGateError(
                503, "공개 서비스에서는 체험 횟수를 초기화할 수 없습니다."
            )
        path = usage_path()
        if path.exists():
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("DELETE FROM usage")


limiter = DailyUsageLimiter()
