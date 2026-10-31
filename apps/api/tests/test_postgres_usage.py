from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from app.core import demo_gate, postgres_usage


@pytest.fixture
def pg_database(monkeypatch):
    dsn = os.getenv("TEST_DATABASE_URL", "")
    if not dsn:
        pytest.skip("A dedicated local Postgres test database is not configured")
    config = conninfo_to_dict(dsn)
    # Integration tests must never mutate the user's Neon project or production.
    if (
        config.get("host") not in {"localhost", "127.0.0.1", "::1"}
        or config.get("dbname") != "sullivan_test"
    ):
        pytest.fail(
            "TEST_DATABASE_URL must identify the isolated local sullivan_test database"
        )
    monkeypatch.setenv("DATABASE_URL", dsn)
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", dsn)
    return dsn


def test_render_postgres_needs_no_persistent_disk(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@db.invalid/demo")
    observed = []
    monkeypatch.setattr(postgres_usage, "access", lambda *a: observed.append(a) or 1)
    monkeypatch.setattr(
        demo_gate.os.path,
        "ismount",
        lambda p: pytest.fail("Free hosting must not require a disk"),
    )
    assert demo_gate.limiter.consume("203.0.113.1") == 2
    assert observed[0][-1] is True


def test_database_error_fails_closed_without_credential_echo(monkeypatch):
    marker = "private-input-that-must-not-appear"
    monkeypatch.setenv("DATABASE_URL", marker)
    with pytest.raises(demo_gate.DemoGateError) as failure:
        demo_gate.limiter.consume("203.0.113.1")
    assert failure.value.status_code == 503
    assert marker not in failure.value.message


def test_postgres_exhaustion_maps_to_daily_message(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@db.invalid/demo")
    monkeypatch.setattr(postgres_usage, "access", lambda *a: None)
    with pytest.raises(demo_gate.DemoGateError) as failure:
        demo_gate.limiter.consume("203.0.113.1")
    assert failure.value.status_code == 429
    assert "오늘 체험 횟수" in failure.value.message


def test_render_enforces_tls_for_database_connections(monkeypatch):
    observed = []
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(
        postgres_usage.psycopg, "connect", lambda **kwargs: observed.append(kwargs)
    )
    postgres_usage._connect("postgresql://test@db.invalid/demo?sslmode=disable")
    assert observed[0]["sslmode"] == "require"
    assert observed[0]["connect_timeout"] == 5
    assert observed[0]["prepare_threshold"] is None


def test_postgres_quota_is_atomic_for_concurrent_clients(pg_database):
    identity = "integration-" + uuid4().hex

    def attempt(_):
        try:
            return demo_gate.DailyUsageLimiter().consume(identity)
        except demo_gate.DemoGateError as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(attempt, range(8)))
    assert sorted(x for x in outcomes if x != 429) == [0, 1, 2]
    assert outcomes.count(429) == 5


def test_postgres_quota_survives_runtime_reinitialization(pg_database, monkeypatch):
    identity = "integration-" + uuid4().hex
    assert demo_gate.DailyUsageLimiter().consume(identity) == 2
    monkeypatch.setattr(postgres_usage, "_ready_dsn", None)
    assert demo_gate.DailyUsageLimiter().consume(identity) == 1
    assert demo_gate.DailyUsageLimiter().consume(identity) == 0
    with pytest.raises(demo_gate.DemoGateError) as failure:
        demo_gate.DailyUsageLimiter().consume(identity)
    assert failure.value.status_code == 429


def test_postgres_quota_resets_on_korean_day_change(pg_database, monkeypatch):
    identity = "integration-" + uuid4().hex
    monkeypatch.setattr(demo_gate, "usage_day", lambda: "2099-01-01")
    for _ in range(3):
        demo_gate.limiter.consume(identity)
    with pytest.raises(demo_gate.DemoGateError):
        demo_gate.limiter.consume(identity)
    monkeypatch.setattr(demo_gate, "usage_day", lambda: "2099-01-02")
    assert demo_gate.limiter.consume(identity) == 2


def test_postgres_availability_check_does_not_consume(pg_database):
    identity = "integration-" + uuid4().hex
    demo_gate.limiter.ensure_available(identity)
    assert [demo_gate.limiter.consume(identity) for _ in range(3)] == [2, 1, 0]
