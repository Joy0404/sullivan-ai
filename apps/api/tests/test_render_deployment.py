import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from starlette.requests import Request
from fastapi.testclient import TestClient

from app.core import demo_gate
from app import launch
import app.main as main


def request(headers=None):
    return Request(
        {
            "type": "http",
            "client": ("10.0.0.1", 1),
            "headers": [
                (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
            ],
        }
    )


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Real-IP": "203.0.113.1"},
        {"CF-Connecting-IP": "invalid"},
        {"CF-Connecting-IP": "1.1.1.1, 2.2.2.2"},
    ],
)
def test_render_requires_valid_edge_ip(monkeypatch, headers):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("TRUST_RENDER_PROXY", "1")
    with pytest.raises(demo_gate.DemoGateError):
        demo_gate.client_ip(request(headers))


def test_render_uses_only_documented_edge_header(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("TRUST_RENDER_PROXY", "1")
    assert (
        demo_gate.client_ip(
            request(
                {
                    "CF-Connecting-IP": "203.0.113.1",
                    "X-Real-IP": "1.1.1.1",
                    "X-Forwarded-For": "2.2.2.2",
                }
            )
        )
        == "203.0.113.1"
    )
    monkeypatch.delenv("TRUST_RENDER_PROXY")
    with pytest.raises(demo_gate.DemoGateError):
        demo_gate.client_ip(request({"CF-Connecting-IP": "203.0.113.1"}))


def test_storage_must_be_mounted_and_db_under_disk(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("DEMO_DATA_DIR", str(tmp_path))
    with pytest.raises(demo_gate.DemoGateError):
        demo_gate.limiter.consume("1.1.1.1")
    monkeypatch.setattr(demo_gate.os.path, "ismount", lambda p: Path(p) == tmp_path)
    assert demo_gate.limiter.consume("1.1.1.1") == 2
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path.parent / "outside.sqlite"))
    with pytest.raises(demo_gate.DemoGateError):
        demo_gate.limiter.consume("1.1.1.1")


def test_atomic_limit_persists_across_limiter_instances_and_days(monkeypatch):
    def attempt(_):
        try:
            return demo_gate.DailyUsageLimiter().consume("203.0.113.7")
        except demo_gate.DemoGateError as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    assert sorted(x for x in results if x != 429) == [0, 1, 2]
    assert results.count(429) == 5
    assert attempt(0) == 429
    monkeypatch.setattr(demo_gate, "usage_day", lambda: "2099-01-01")
    assert attempt(0) == 2


def test_database_failure_blocks_analysis(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path))
    with pytest.raises(demo_gate.DemoGateError) as result:
        demo_gate.limiter.consume("203.0.113.1")
    assert result.value.status_code == 503


@pytest.mark.parametrize("timeout", ["181", "600", "nan", "inf", "bad"])
def test_runtime_limits_cannot_exceed_public_policy(monkeypatch, timeout):
    monkeypatch.setenv("ANALYSIS_TIMEOUT_SECONDS", timeout)
    monkeypatch.setenv("DEMO_DAILY_LIMIT", "100")
    assert demo_gate.analysis_timeout_seconds() <= 180
    assert demo_gate.limiter.limit() == 3


def test_launch_initializes_disk_then_drops_privileges(monkeypatch):
    events = []
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("PORT", "8765")
    monkeypatch.setattr(launch.os, "geteuid", lambda: 0)
    monkeypatch.setattr(launch.os.path, "ismount", lambda p: True)
    monkeypatch.setattr(launch.os, "chown", lambda *a: events.append(("chown", a)))
    monkeypatch.setattr(launch.os, "setgroups", lambda *a: events.append(("groups", a)))
    monkeypatch.setattr(launch.os, "setgid", lambda *a: events.append(("gid", a)))
    monkeypatch.setattr(launch.os, "setuid", lambda *a: events.append(("uid", a)))
    monkeypatch.setattr(launch.os, "execv", lambda *a: events.append(("exec", a)))
    launch.main()
    assert [e[0] for e in events] == ["chown", "groups", "gid", "uid", "exec"]
    assert "8765" in events[-1][1][1]
    assert "--no-proxy-headers" in events[-1][1][1]


def test_validation_does_not_echo_submitted_secrets():
    client = TestClient(main.app)
    sid = client.post("/v1/lectures", json={"title": "test"}).json()["session_id"]
    response = client.post(
        f"/v1/lectures/{sid}/video-link",
        json={
            "url": "https://youtu.be/R0dqsl3Vgns",
            "access_code": {"private": "do-not-echo"},
        },
    )
    assert response.status_code == 422 and "do-not-echo" not in response.text


def test_paid_agent_requires_consent_and_uses_shared_quota(monkeypatch):
    from app.models import AgentTurnResponse

    monkeypatch.setenv("GEMINI_API_KEY", "test-provider")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "test-code")
    calls = []

    async def fake(*a, **kw):
        calls.append(1)
        return AgentTurnResponse(
            action="pause", title="test", response_text="test", decision_reason="test"
        )

    monkeypatch.setattr(main, "run_agent_turn", fake)
    client = TestClient(main.app)
    sid = client.post("/v1/lectures", json={"title": "test"}).json()["session_id"]
    url = f"/v1/lectures/{sid}/agent-turn"
    data = {"message": "test", "access_code": "test-code"}
    assert client.post(url, json=data).status_code == 400
    data["analysis_consent"] = True
    assert [client.post(url, json=data).status_code for _ in range(4)] == [
        200,
        200,
        200,
        429,
    ]
    assert len(calls) == 3
