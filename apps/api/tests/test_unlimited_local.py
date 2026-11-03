from fastapi.testclient import TestClient
from app.main import app
from app.core.demo_gate import DailyUsageLimiter, DemoGateError
import pytest


def test_local_test_mode_allows_repeated_requests_and_keeps_code_gate(monkeypatch):
    monkeypatch.setenv("LOCAL_TEST_UNLIMITED", "1")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "test-code")
    limiter = DailyUsageLimiter()
    assert [limiter.consume("local-test") for _ in range(10)] == [None] * 10
    from app.core.demo_gate import check_access_code
    with pytest.raises(DemoGateError):
        check_access_code("wrong")
    assert TestClient(app).get("/health").json()["daily_trial_limit"] == "unlimited"


def test_unlimited_mode_fails_closed_on_render_or_shared_database(monkeypatch):
    monkeypatch.setenv("LOCAL_TEST_UNLIMITED", "1")
    monkeypatch.setenv("RENDER", "true")
    with pytest.raises(DemoGateError):
        DailyUsageLimiter().consume("127.0.0.1")
    monkeypatch.delenv("RENDER")
    monkeypatch.setenv("DATABASE_URL", "configured")
    with pytest.raises(DemoGateError):
        DailyUsageLimiter().consume("127.0.0.1")
