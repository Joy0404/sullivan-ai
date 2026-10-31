"""Atomic shared demo quota on PostgreSQL; credentials remain runtime-only."""

from pathlib import Path
import os
import threading

import psycopg
from psycopg.conninfo import conninfo_to_dict


class UsageStorageError(Exception):
    pass


_schema_lock = threading.Lock()
_ready_dsn = None
MIGRATION = Path(__file__).resolve().parents[1] / "db/migrations/001_demo_usage.sql"
MIGRATION_LOCK = 739421081


def _connect(dsn):
    # Do not put credentials, connection exceptions or raw connection strings in logs.
    config = conninfo_to_dict(dsn)
    if os.getenv("RENDER") == "true":
        config["sslmode"] = "require"
    return psycopg.connect(**config, connect_timeout=5, prepare_threshold=None)


def _setup(dsn):
    global _ready_dsn
    with _schema_lock:
        if _ready_dsn == dsn:
            return
        direct = os.getenv("DATABASE_URL_UNPOOLED", "").strip()
        host = conninfo_to_dict(direct or dsn).get("host", "")
        if "-pooler." in host and not direct:
            # A migration uses a direct connection; a pre-provisioned table can
            # still be used with a pooled app URL and no migration credentials.
            with _connect(dsn) as db:
                found = db.execute(
                    "SELECT to_regclass('public.demo_usage')"
                ).fetchone()[0]
                if found is None:
                    raise UsageStorageError("체험 횟수 DB 초기 설정이 필요합니다.")
        else:
            with _connect(direct or dsn) as db:
                db.execute("SET LOCAL statement_timeout = '5s'")
                db.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK,))
                db.execute(MIGRATION.read_text())
        _ready_dsn = dsn


def access(dsn: str, identity: str, day: str, limit: int, consume: bool):
    """Return used count, or None when this IP/day has exhausted the allowance."""
    try:
        _setup(dsn)
        with _connect(dsn) as db:
            db.execute("SET LOCAL statement_timeout = '5s'")
            db.execute("SET LOCAL lock_timeout = '3s'")
            if consume:
                row = db.execute(
                    """
                    INSERT INTO public.demo_usage (ip_hash, usage_day, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (ip_hash, usage_day)
                    DO UPDATE SET count = demo_usage.count + 1
                    WHERE demo_usage.count < %s
                    RETURNING count
                """,
                    (identity, day, limit),
                ).fetchone()
                if row is None:
                    return None
                db.execute("DELETE FROM public.demo_usage WHERE usage_day < %s", (day,))
                return row[0]
            row = db.execute(
                "SELECT count FROM public.demo_usage WHERE ip_hash=%s AND usage_day=%s",
                (identity, day),
            ).fetchone()
            used = row[0] if row else 0
            return used if used < limit else None
    except UsageStorageError:
        raise
    except (psycopg.Error, OSError, ValueError):
        raise UsageStorageError(
            "체험 횟수 DB에 연결할 수 없어 실제 분석을 중단했습니다."
        ) from None
