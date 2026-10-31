import os

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.models import (
    AnalysisPackageInput,
    StudyGuide,
    TranscriptSegment,
    VisualObservation,
)


client = TestClient(app)


def create_session(problem_mode: bool = False) -> str:
    response = client.post(
        "/v1/lectures",
        json={
            "title": "Sullivan AI API 테스트",
            "subject": "통합",
            "source_label": "테스트 자료",
            "preferred_mode": "auto",
            "problem_mode": problem_mode,
        },
    )
    assert response.status_code == 201
    return response.json()["session_id"]


def test_health_reports_raw_video_storage_disabled() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["raw_video_storage"] == "disabled"


def test_demo_analysis_and_passage_navigation_api() -> None:
    session_id = create_session()
    demo = client.post(f"/v1/lectures/{session_id}/demo-analysis")

    assert demo.status_code == 200
    snapshot = demo.json()
    assert snapshot["active_mode"] == "mixed"
    assert snapshot["held_count"] == 1
    assert "초신성" in snapshot["study_guide"]["overview"]
    assert len(snapshot["study_guide"]["glossary"]) >= 4

    navigation = client.post(
        f"/v1/lectures/{session_id}/navigate",
        json={"command": "밑줄 문장 읽어줘", "current_sentence_id": None},
    )
    assert navigation.status_code == 200
    assert "강사가 강조한 문장" in navigation.json()["message"]


def test_missing_session_returns_404() -> None:
    response = client.get("/v1/lectures/does-not-exist")

    assert response.status_code == 404


def test_public_video_link_registers_without_fake_analysis(monkeypatch) -> None:
    monkeypatch.delenv("LINK_ANALYZER_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    session_id = create_session()

    response = client.post(
        f"/v1/lectures/{session_id}/video-link",
        json={
            "url": "https://media.example.com/lesson.mp4",
            "rights_confirmed": True,
            "request_analysis": False,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["playback_kind"] == "direct"
    assert result["analysis_status"] == "registered-only"
    assert result["snapshot"] is None


def test_star_sample_registers_without_live_analysis_then_loads_demo(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    session_id = create_session()
    registered = client.post(
        f"/v1/lectures/{session_id}/video-link",
        json={
            "url": "https://www.youtube.com/watch?v=R0dqsl3Vgns",
            "rights_confirmed": True,
            "request_analysis": False,
        },
    )

    assert registered.status_code == 200
    assert registered.json()["analysis_status"] == "registered-only"

    demo = client.post(f"/v1/lectures/{session_id}/demo-analysis")
    asset = demo.json()["assets"][0]
    assert asset["processing_status"] == "indexed"
    assert "사전에 준비" in asset["note"]


def test_video_link_requires_rights_confirmation() -> None:
    session_id = create_session()

    response = client.post(
        f"/v1/lectures/{session_id}/video-link",
        json={
            "url": "https://media.example.com/lesson.mp4",
            "rights_confirmed": False,
        },
    )

    assert response.status_code == 400


def test_local_video_analysis_requires_separate_cloud_consent() -> None:
    session_id = create_session()

    response = client.post(
        f"/v1/lectures/{session_id}/video-file-analysis",
        data={
            "asset_id": "video-consent-test",
            "rights_confirmed": "true",
            "cloud_analysis_consent": "false",
            "gemini_api_key": "test-key",
        },
        files={"video": ("lesson.mp4", b"not-sent-to-provider", "video/mp4")},
    )

    assert response.status_code == 400
    assert "별도 동의" in response.json()["detail"]


def test_local_video_analysis_uses_temporary_file_and_indexes_result(monkeypatch) -> None:
    session_id = create_session()
    asset_id = "video-local-analysis-test"
    registered = client.post(
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
    assert registered.status_code == 201
    observed: dict[str, object] = {}

    async def fake_analysis(file_path: str, **kwargs) -> AnalysisPackageInput:
        observed["file_path"] = file_path
        observed["exists_during_analysis"] = os.path.exists(file_path)
        with open(file_path, "rb") as source:
            observed["content"] = source.read()
        observed["kwargs"] = kwargs
        return AnalysisPackageInput(
            transcript_segments=[
                TranscriptSegment(
                    segment_id="speech-1",
                    start_ms=0,
                    end_ms=5000,
                    text="강사는 세포의 구조를 설명합니다.",
                    confidence=0.96,
                )
            ],
            visual_observations=[
                VisualObservation(
                    observation_id="visual-1",
                    timestamp_ms=3000,
                    screen_type="slide",
                    kind="concept",
                    text="세포막, 세포질, 핵",
                    confidence=0.95,
                    importance=0.9,
                    annotation="화면에 세포의 세 구성 요소가 표시됩니다.",
                    metadata={
                        "verification": "confirmed",
                        "visible_evidence": ["세포막", "세포질", "핵"],
                    },
                )
            ],
            study_guide=StudyGuide(overview="세포의 기본 구조를 설명한 강의입니다."),
        )

    monkeypatch.setattr(
        main_module, "analyze_uploaded_video_with_gemini", fake_analysis
    )
    # Public deployment: only the server key is used, behind the trial code.
    monkeypatch.setenv("GEMINI_API_KEY", "temporary-test-key")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "trial-code")
    main_module.limiter.reset()
    response = client.post(
        f"/v1/lectures/{session_id}/video-file-analysis",
        data={
            "asset_id": asset_id,
            "rights_confirmed": "true",
            "cloud_analysis_consent": "true",
            "access_code": "trial-code",
        },
        files={"video": ("lesson.mp4", b"fake-video-bytes", "video/mp4")},
    )

    assert response.status_code == 200
    result = response.json()
    assert observed["exists_during_analysis"] is True
    assert observed["content"] == b"fake-video-bytes"
    assert not os.path.exists(str(observed["file_path"]))
    assert observed["kwargs"]["api_key"] == "temporary-test-key"
    assert result["transcript_segments"][0]["text"].startswith("강사는")
    assert result["assets"][0]["processing_status"] == "indexed"
    assert "원본은 저장하지 않습니다" in result["assets"][0]["note"]
    assert result["cleanup_status"] == "deleted"


def test_video_link_blocks_local_network_targets() -> None:
    session_id = create_session()

    response = client.post(
        f"/v1/lectures/{session_id}/video-link",
        json={
            "url": "http://127.0.0.1/private-video.mp4",
            "rights_confirmed": True,
        },
    )

    assert response.status_code == 400
