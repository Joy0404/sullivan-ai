import asyncio
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

import app.adapters.video_link as video_link_module
import app.main as main_module
from app.adapters.video_link import LinkAnalyzerError, analyze_uploaded_video_with_gemini
from app.main import app
from app.models import (
    AgentTurnResponse,
    AnalysisPackageInput,
    StudyGuide,
    TranscriptSegment,
    VisualObservation,
)


client = TestClient(app)
WEB_DIR = Path(__file__).resolve().parents[2] / "web"
SAMPLE_URL = "https://www.youtube.com/watch?v=R0dqsl3Vgns"


@pytest.fixture(autouse=True)
def public_demo_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "server-test-key")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "trial-code")
    monkeypatch.delenv("DEMO_DAILY_LIMIT", raising=False)
    monkeypatch.delenv("ANALYSIS_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("ALLOWED_SAMPLE_VIDEO_IDS", raising=False)
    main_module.limiter.reset()
    yield
    main_module.limiter.reset()


def analysis_package() -> AnalysisPackageInput:
    return AnalysisPackageInput(
        transcript_segments=[
            TranscriptSegment(
                segment_id="speech-1",
                start_ms=0,
                end_ms=5000,
                text="강사는 별의 탄생을 설명합니다.",
                confidence=0.96,
            )
        ],
        visual_observations=[
            VisualObservation(
                observation_id="visual-1",
                timestamp_ms=3000,
                screen_type="slide",
                kind="concept",
                text="성운, 원시별",
                confidence=0.95,
                importance=0.9,
                annotation="화면에 성운과 원시별이 표시됩니다.",
                metadata={"verification": "confirmed", "visible_evidence": ["성운", "원시별"]},
            )
        ],
        study_guide=StudyGuide(overview="별의 탄생을 설명한 강의입니다."),
    )


def create_session() -> str:
    response = client.post(
        "/v1/lectures",
        json={
            "title": "공개 체험 관문 테스트",
            "subject": "통합",
            "source_label": "테스트",
            "preferred_mode": "auto",
            "problem_mode": False,
        },
    )
    return response.json()["session_id"]


def prepare_upload() -> tuple[str, str]:
    session_id = create_session()
    asset_id = f"video-{session_id[-6:]}"
    client.post(
        f"/v1/lectures/{session_id}/assets",
        json={
            "asset_id": asset_id,
            "name": "lesson.mp4",
            "kind": "video",
            "media_type": "video/mp4",
            "size_bytes": 16,
            "metadata": {"client_local_playback": True},
        },
    )
    return session_id, asset_id


def upload(session_id: str, asset_id: str, *, code: str | None = "trial-code", ip: str = "203.0.113.7", extra=None):
    data = {
        "asset_id": asset_id,
        "rights_confirmed": "true",
        "cloud_analysis_consent": "true",
    }
    if code is not None:
        data["access_code"] = code
    data.update(extra or {})
    return client.post(
        f"/v1/lectures/{session_id}/video-file-analysis",
        data=data,
        files={"video": ("lesson.mp4", b"fake-video-bytes", "video/mp4")},
        headers={"X-Real-IP": ip},
    )


def use_fake_upload_analysis(monkeypatch, observed: dict | None = None):
    async def fake(file_path: str, **kwargs) -> AnalysisPackageInput:
        if observed is not None:
            observed["file_path"] = file_path
            observed["kwargs"] = kwargs
        return analysis_package()

    monkeypatch.setattr(main_module, "analyze_uploaded_video_with_gemini", fake)


@pytest.mark.parametrize(
    ("code", "status", "phrase"),
    [(None, 401, "체험 코드가 필요"), ("", 401, "체험 코드가 필요"), ("wrong", 403, "올바르지 않습니다")],
)
def test_upload_analysis_requires_matching_trial_code(monkeypatch, code, status, phrase) -> None:
    called = []
    monkeypatch.setattr(main_module, "analyze_uploaded_video_with_gemini", lambda *a, **k: called.append(1))
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id, code=code)

    assert response.status_code == status
    assert phrase in response.json()["detail"]
    assert called == []


def test_upload_analysis_is_disabled_without_server_trial_code(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_ACCESS_CODE")
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 503
    assert "체험 코드가 설정되지 않아" in response.json()["detail"]


def test_upload_analysis_without_server_key_is_not_reported_as_done(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY")
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 503
    assert "Gemini API 키가 설정되지 않아" in response.json()["detail"]


def test_upload_uses_only_the_server_key(monkeypatch) -> None:
    observed: dict = {}
    use_fake_upload_analysis(monkeypatch, observed)
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id, extra={"gemini_api_key": "visitor-key"})

    assert response.status_code == 200
    assert observed["kwargs"]["api_key"] == "server-test-key"
    assert "visitor-key" not in response.text
    assert "server-test-key" not in response.text


def test_daily_limit_blocks_fourth_analysis_per_ip(monkeypatch) -> None:
    use_fake_upload_analysis(monkeypatch)

    remaining = []
    for _ in range(3):
        session_id, asset_id = prepare_upload()
        response = upload(session_id, asset_id)
        assert response.status_code == 200
        remaining.append(response.json()["remaining_trials"])
    session_id, asset_id = prepare_upload()
    blocked = upload(session_id, asset_id)
    other_visitor = upload(session_id, asset_id, ip="198.51.100.9")

    assert remaining == [2, 1, 0]
    assert blocked.status_code == 429
    assert "오늘 체험 횟수를 모두 사용했어요" in blocked.json()["detail"]
    assert other_visitor.status_code == 200


def test_wrong_code_does_not_use_up_daily_trials(monkeypatch) -> None:
    use_fake_upload_analysis(monkeypatch)
    for _ in range(5):
        session_id, asset_id = prepare_upload()
        assert upload(session_id, asset_id, code="wrong").status_code == 403

    session_id, asset_id = prepare_upload()
    assert upload(session_id, asset_id).status_code == 200


def test_oversized_upload_is_rejected_without_using_a_trial(monkeypatch) -> None:
    use_fake_upload_analysis(monkeypatch)
    monkeypatch.setenv("MAX_UPLOAD_VIDEO_BYTES", "4")
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 413
    assert "크기 제한" in response.json()["detail"]
    monkeypatch.delenv("MAX_UPLOAD_VIDEO_BYTES")
    for _ in range(3):
        session_id, asset_id = prepare_upload()
        assert upload(session_id, asset_id).status_code == 200


def test_default_upload_limit_is_100mb() -> None:
    assert main_module.DEFAULT_MAX_UPLOAD_VIDEO_BYTES == 100 * 1024 * 1024


def test_analysis_timeout_stops_and_still_deletes_temporary_file(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_TIMEOUT_SECONDS", "0.05")
    observed: dict = {}

    async def slow(file_path: str, **kwargs) -> AnalysisPackageInput:
        observed["file_path"] = file_path
        try:
            await asyncio.sleep(5)
        finally:
            observed["cancelled_cleanup_ran"] = True
        return analysis_package()

    monkeypatch.setattr(main_module, "analyze_uploaded_video_with_gemini", slow)
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 504
    assert "3분" in response.json()["detail"]
    assert observed["cancelled_cleanup_ran"] is True
    assert not os.path.exists(observed["file_path"])
    snapshot = client.get(f"/v1/lectures/{session_id}").json()
    assert snapshot["assets"][0]["processing_status"] != "indexed"


def test_provider_delete_failure_is_reported_not_hidden(monkeypatch) -> None:
    async def leaves_copy(file_path: str, **kwargs) -> AnalysisPackageInput:
        kwargs["cleanup_report"]["provider"] = "delete-failed"
        return analysis_package()

    monkeypatch.setattr(main_module, "analyze_uploaded_video_with_gemini", leaves_copy)
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 200
    assert response.json()["cleanup_status"] == "delete-failed"
    assert "삭제를 확인하지 못했습니다" in response.json()["cleanup_message"]


def test_failed_analysis_with_failed_delete_mentions_both(monkeypatch) -> None:
    async def fails(file_path: str, **kwargs) -> AnalysisPackageInput:
        kwargs["cleanup_report"]["provider"] = "delete-failed"
        raise LinkAnalyzerError("Gemini 영상 분석에 실패했습니다.")

    monkeypatch.setattr(main_module, "analyze_uploaded_video_with_gemini", fails)
    session_id, asset_id = prepare_upload()

    response = upload(session_id, asset_id)

    assert response.status_code == 502
    assert "분석에 실패" in response.json()["detail"]
    assert "삭제를 확인하지 못했습니다" in response.json()["detail"]


@pytest.mark.parametrize(("delete_status", "expected"), [(200, "deleted"), (500, "delete-failed")])
def test_gemini_file_is_deleted_even_when_analysis_fails(monkeypatch, tmp_path, delete_status, expected) -> None:
    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
            return httpx.Response(delete_status, json={})
        return httpx.Response(404)

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        video_link_module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler)),
    )

    async def upload_then_fail(client, *, upload_state, **kwargs):
        upload_state["file_name"] = "files/test-upload"
        raise LinkAnalyzerError("Gemini가 업로드 영상을 처리하지 못했습니다.")

    monkeypatch.setattr(video_link_module, "_upload_gemini_video_file", upload_then_fail)
    video = tmp_path / "lesson.mp4"
    video.write_bytes(b"x")
    report: dict[str, str] = {}

    with pytest.raises(LinkAnalyzerError):
        asyncio.run(
            analyze_uploaded_video_with_gemini(
                str(video),
                display_name="lesson.mp4",
                mime_type="video/mp4",
                title="t",
                subject="s",
                problem_mode=False,
                api_key="server-test-key",
                cleanup_report=report,
            )
        )

    assert deleted == ["/v1beta/files/test-upload"]
    assert report["provider"] == expected


def link(session_id: str, url: str, *, consent=True, code="trial-code"):
    return client.post(
        f"/v1/lectures/{session_id}/video-link",
        json={
            "url": url,
            "rights_confirmed": True,
            "request_analysis": True,
            "analysis_consent": consent,
            "access_code": code,
        },
        headers={"X-Real-IP": "203.0.113.20"},
    )


def use_fake_link_analysis(monkeypatch, observed: dict | None = None):
    async def fake(url: str, **kwargs) -> AnalysisPackageInput:
        if observed is not None:
            observed["url"] = url
            observed["kwargs"] = kwargs
        return analysis_package()

    monkeypatch.setattr(main_module, "analyze_video_link", fake)


def test_link_analysis_requires_consent(monkeypatch) -> None:
    use_fake_link_analysis(monkeypatch)

    response = link(create_session(), SAMPLE_URL, consent=False)

    assert response.status_code == 400
    assert "동의" in response.json()["detail"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://media.example.com/lesson.mp4",
    ],
)
def test_link_analysis_only_allows_listed_samples(monkeypatch, url) -> None:
    use_fake_link_analysis(monkeypatch)

    response = link(create_session(), url)

    assert response.status_code == 400
    assert "샘플" in response.json()["detail"]


def test_link_analysis_requires_trial_code(monkeypatch) -> None:
    use_fake_link_analysis(monkeypatch)

    assert link(create_session(), SAMPLE_URL, code="wrong").status_code == 403
    assert link(create_session(), SAMPLE_URL, code=None).status_code == 401


def test_listed_sample_link_runs_with_server_key_and_counts(monkeypatch) -> None:
    observed: dict = {}
    use_fake_link_analysis(monkeypatch, observed)

    results = [link(create_session(), "https://youtu.be/thJxqtTgSNY") for _ in range(4)]

    assert [item.status_code for item in results] == [200, 200, 200, 429]
    assert results[0].json()["analysis_status"] == "completed"
    assert observed["kwargs"]["api_key_override"] == "server-test-key"


def test_link_analysis_timeout_is_reported(monkeypatch) -> None:
    monkeypatch.setenv("ANALYSIS_TIMEOUT_SECONDS", "0.05")

    async def slow(url: str, **kwargs):
        await asyncio.sleep(5)

    monkeypatch.setattr(main_module, "analyze_video_link", slow)

    response = link(create_session(), SAMPLE_URL)

    assert response.status_code == 504
    assert "3분" in response.json()["detail"]


def test_allowed_samples_can_be_configured(monkeypatch) -> None:
    use_fake_link_analysis(monkeypatch)
    monkeypatch.setenv("ALLOWED_SAMPLE_VIDEO_IDS", "dQw4w9WgXcQ")

    assert link(create_session(), "https://youtu.be/dQw4w9WgXcQ").status_code == 200
    assert link(create_session(), SAMPLE_URL).status_code == 400


def agent_turn(session_id: str, code: str | None):
    return client.post(
        f"/v1/lectures/{session_id}/agent-turn",
        json={"message": "요약을 읽어줘", "current_time_ms": 0, "access_code": code, "gemini_api_key": "visitor-key"},
    )


def test_agent_turn_needs_trial_code_to_use_server_key(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_turn(snapshot, **kwargs):
        calls.append(kwargs)
        return AgentTurnResponse(
            action="read_summary",
            title="요약",
            response_text="요약입니다.",
            decision_reason="요청",
            grounding=["요약"],
            confidence=0.96,
        )

    monkeypatch.setattr(main_module, "run_agent_turn", fake_turn)
    session_id = create_session()

    missing = agent_turn(session_id, None)
    wrong = agent_turn(session_id, "wrong")
    allowed = agent_turn(session_id, "trial-code")

    assert missing.status_code == 401 and "로컬 보조 모드" in missing.json()["detail"]
    assert wrong.status_code == 403 and "로컬 보조 모드" in wrong.json()["detail"]
    assert allowed.status_code == 200
    assert len(calls) == 1
    assert "api_key_override" not in calls[0]


def test_web_app_is_served_from_same_origin() -> None:
    page = client.get("/")
    script = client.get("/app.js")
    health = client.get("/health")

    assert page.status_code == 200 and "<html" in page.text.lower()
    assert script.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["real_analysis_access"] == "trial-code-required"
    assert "server-test-key" not in health.text
    assert "trial-code" not in health.text.replace("trial-code-required", "")


def test_web_code_has_no_localhost_or_port_8000_calls() -> None:
    for path in [*WEB_DIR.glob("*.js"), WEB_DIR / "index.html"]:
        text = path.read_text(encoding="utf-8")
        assert "localhost" not in text, path.name
        assert ":8000" not in text, path.name
        assert "127.0.0.1" not in text, path.name
