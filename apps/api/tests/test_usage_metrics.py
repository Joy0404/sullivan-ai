"""Provider-boundary usage regression tests; all generation responses are mocked."""
import asyncio
import json
from uuid import UUID

import httpx
import pytest

from app.adapters import gemini_agent, video_link
from app.adapters.usage_metrics import capture_usage, logger, metered_post, parse_usage
from app.core.demo import build_demo_package
from app.core.lecture_agent import LectureAgent
from app.models import AnalysisPackageInput, LectureCreate


@pytest.mark.parametrize("provider_api,body", [
    ("generate_content", {"usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20, "thoughtsTokenCount": 7, "cachedContentTokenCount": 30, "totalTokenCount": 127}}),
    ("interactions", {"usage": {"total_input_tokens": 100, "total_output_tokens": 20, "total_thought_tokens": 7, "total_cached_tokens": 30, "total_tokens": 127}}),
])
def test_documented_provider_counters_are_preserved_without_double_counting(provider_api: str, body: dict) -> None:
    usage = parse_usage(body, provider_api=provider_api)
    assert (usage.input_tokens, usage.output_tokens, usage.reasoning_tokens, usage.cache_tokens, usage.total_tokens) == (100, 20, 7, 30, 127)
    assert usage.measurement == "measured"


@pytest.mark.parametrize("body", [None, [], {}, {"usageMetadata": None}, {"usageMetadata": {"promptTokenCount": True, "candidatesTokenCount": -1, "totalTokenCount": "12"}}])
def test_missing_or_invalid_usage_is_unmeasured_and_never_zero_filled(body: object) -> None:
    usage = parse_usage(body, provider_api="generate_content")
    assert usage.total_tokens is None and usage.input_tokens is None
    assert usage.measurement == "미측정"


def test_partial_usage_keeps_unknown_counters_null_and_explicit_zero() -> None:
    usage = parse_usage({"usageMetadata": {"promptTokenCount": 10, "cachedContentTokenCount": 0}}, provider_api="generate_content")
    assert usage.input_tokens == 10 and usage.cache_tokens == 0
    assert usage.output_tokens is usage.reasoning_tokens is usage.total_tokens is None
    assert usage.measurement == "measured"


@pytest.mark.parametrize("failure", ["parse", "http", "transport", "invalid_json"])
def test_failed_attempts_are_recorded_without_request_response_or_exception_content(failure: str, caplog: pytest.LogCaptureFixture) -> None:
    secret = "PRIVATE_QUESTION_SUBTITLE_VIDEO_AND_KEY"

    def provider(request: httpx.Request) -> httpx.Response:
        if failure == "transport":
            raise httpx.ConnectError(secret, request=request)
        if failure == "invalid_json":
            return httpx.Response(200, text=secret)
        return httpx.Response(429 if failure == "http" else 200, json={"private": secret, "usageMetadata": {"totalTokenCount": 43}})

    def parser(body: object) -> None:
        raise ValueError(secret)

    async def run() -> list[dict]:
        with capture_usage() as records:
            async with httpx.AsyncClient(transport=httpx.MockTransport(provider)) as client:
                with pytest.raises((ValueError, httpx.HTTPError)):
                    await metered_post(client, "https://provider.example/" + secret, model="gemini-2.5-flash", stage="question", provider_api="generate_content", parse_response=parser, json={"text": secret}, headers={"x-goog-api-key": secret})
        return records

    logger.addHandler(caplog.handler)
    try:
        records = asyncio.run(run())
    finally:
        logger.removeHandler(caplog.handler)
    assert len(records) == 1
    record = records[0]
    assert record["success"] is False
    assert record["total_tokens"] == (43 if failure in {"parse", "http"} else None)
    assert record["measurement"] == ("measured" if failure in {"parse", "http"} else "미측정")
    assert secret not in json.dumps(records) and secret not in caplog.text
    assert record["operation_id"] != record["request_id"]
    UUID(record["operation_id"])
    UUID(record["request_id"])


def test_video_fallback_keeps_both_stages_and_every_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []
    package = AnalysisPackageInput().model_dump_json()

    def provider(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        if len(calls) <= 2:
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": package if len(calls) == 1 else "invalid-json"}]}}], "usageMetadata": {"totalTokenCount": 11}})
        return httpx.Response(200, json={"output_text": package, "usage": {"total_tokens": 13}})

    original = httpx.AsyncClient
    monkeypatch.setattr(video_link.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(provider), **kwargs))
    with capture_usage() as records:
        asyncio.run(video_link._analyze_gemini_video_source("https://fixture.example/PRIVATE_SOURCE.mp4", mime_type="video/mp4", title="PRIVATE_TITLE", subject="PRIVATE_SUBJECT", problem_mode=False, api_key="PRIVATE_KEY"))
    assert [r["stage"] for r in records] == ["analysis", "verification", "analysis", "verification"]
    assert [r["attempt"] for r in records] == [1, 1, 2, 2]
    assert [r["retry"] for r in records] == [False, False, True, True]
    assert [r["success"] for r in records] == [True, False, True, True]
    assert [r["total_tokens"] for r in records] == [11, 11, 13, 13]
    assert len({r["operation_id"] for r in records}) == 1
    assert len({r["request_id"] for r in records}) == 4
    assert "PRIVATE" not in json.dumps(records)


def test_question_generation_is_instrumented_without_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    def provider(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps({"action": "pause", "title": "보류", "response_text": "근거 부족", "decision_reason": "근거 부족", "confidence": 0.5})}]}}]})

    agent = LectureAgent()
    session = agent.create_session(LectureCreate(title="PRIVATE_LECTURE"))
    snapshot = agent.analyze(session.session_id, build_demo_package())
    original = httpx.AsyncClient
    monkeypatch.setattr(gemini_agent.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(provider), **kwargs))
    with capture_usage() as records:
        asyncio.run(gemini_agent.run_agent_turn(snapshot, message="PRIVATE_QUESTION", current_time_ms=1000, api_key_override="PRIVATE_KEY"))
    assert len(records) == 1 and records[0]["stage"] == "question"
    assert records[0]["measurement"] == "미측정" and records[0]["success"] is True
    assert "PRIVATE" not in json.dumps(records)
