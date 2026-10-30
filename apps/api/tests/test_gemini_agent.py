import json

from fastapi.testclient import TestClient

from app.adapters.gemini_agent import build_grounded_context, sanitize_agent_result
from app.core.demo import build_demo_package
from app.core.lecture_agent import LectureAgent
from app.main import app
from app.models import AgentTurnResponse, LectureCreate


def build_snapshot(*, problem_mode: bool = False):
    lecture_agent = LectureAgent()
    session = lecture_agent.create_session(
        LectureCreate(
            title="에이전트 테스트 강의",
            subject="통합과학",
            source_label="테스트",
            problem_mode=problem_mode,
        )
    )
    return lecture_agent.analyze(session.session_id, build_demo_package())


def test_grounded_context_excludes_held_source_and_redacts_personal_data() -> None:
    snapshot = build_snapshot()
    snapshot.transcript_segments[0].text += " student@example.com 010-1234-5678"
    held = next(item for item in snapshot.visual_gaps if not item.safe_to_speak)
    held.source_text = "외부로 보내면 안 되는 내부 관측값"

    context = build_grounded_context(snapshot)
    serialized = json.dumps(context, ensure_ascii=False)

    assert "source_text" not in serialized
    assert "외부로 보내면 안 되는 내부 관측값" not in serialized
    assert "경계 질량 수치 후보" not in serialized
    assert "student@example.com" not in serialized
    assert "010-1234-5678" not in serialized
    assert "[개인정보 비공개]" in serialized


def test_problem_mode_overrides_model_final_answer() -> None:
    snapshot = build_snapshot(problem_mode=True)
    raw = {
        "action": "answer",
        "title": "정답",
        "response_text": "정답은 3번입니다.",
        "decision_reason": "모델 판단",
        "target_timestamp_ms": None,
        "paragraph_indices": [],
        "grounding": ["추측"],
        "confidence": 0.99,
    }

    result = sanitize_agent_result(raw, snapshot=snapshot, message="정답만 알려줘")

    assert result.title == "풀이 방향"
    assert "3번" not in result.response_text
    assert result.confidence == 1.0


def test_low_confidence_turn_is_held_and_does_not_speak() -> None:
    snapshot = build_snapshot()
    raw = {
        "action": "seek",
        "title": "불확실한 이동",
        "response_text": "어딘가로 이동합니다.",
        "decision_reason": "근거가 약함",
        "target_timestamp_ms": 999_999_999,
        "paragraph_indices": [],
        "grounding": [],
        "confidence": 0.4,
    }

    result = sanitize_agent_result(raw, snapshot=snapshot, message="관련 부분으로 가줘")

    assert result.action == "pause"
    assert result.safe_to_speak is False
    assert "확신" in result.decision_reason


def test_seek_timestamp_is_snapped_to_verified_lecture_time() -> None:
    snapshot = build_snapshot()
    raw = {
        "action": "seek",
        "title": "관련 구간 이동",
        "response_text": "주계열성 설명 구간으로 이동합니다.",
        "decision_reason": "주계열성 발화 구간을 사용했습니다.",
        "target_timestamp_ms": 325_555,
        "paragraph_indices": [],
        "grounding": ["중심에서 수소 핵융합이 시작되면 주계열 단계에 들어갑니다."],
        "confidence": 0.95,
    }

    result = sanitize_agent_result(raw, snapshot=snapshot, message="주계열성 부분으로 가줘")

    assert result.action == "seek"
    assert result.target_timestamp_ms == 318_000
    assert result.safe_to_speak is True


def test_agent_endpoint_falls_back_when_no_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = TestClient(app)
    created = client.post(
        "/v1/lectures",
        json={
            "title": "키 없는 테스트",
            "subject": "통합",
            "source_label": "테스트",
            "preferred_mode": "auto",
            "problem_mode": False,
        },
    )
    session_id = created.json()["session_id"]

    response = client.post(
        f"/v1/lectures/{session_id}/agent-turn",
        json={"message": "3줄로 요약해줘", "current_time_ms": 0},
    )

    assert response.status_code == 503
    assert "로컬 보조 모드" in response.json()["detail"]


def test_agent_endpoint_returns_a_verified_tool_action(monkeypatch) -> None:
    async def fake_turn(snapshot, *, message, current_time_ms, api_key_override=None):
        assert snapshot.session.title == "행동 실행 테스트"
        assert message == "요약을 읽어줘"
        assert current_time_ms == 12_000
        return AgentTurnResponse(
            action="read_summary",
            title="세 줄 요약",
            response_text="검증된 강의 요약입니다.",
            decision_reason="사용자가 요약 낭독을 요청했습니다.",
            grounding=["강의 핵심 요약"],
            confidence=0.96,
        )

    monkeypatch.setattr("app.main.run_agent_turn", fake_turn)
    client = TestClient(app)
    created = client.post(
        "/v1/lectures",
        json={
            "title": "행동 실행 테스트",
            "subject": "통합",
            "source_label": "테스트",
            "preferred_mode": "auto",
            "problem_mode": False,
        },
    )

    response = client.post(
        f"/v1/lectures/{created.json()['session_id']}/agent-turn",
        json={"message": "요약을 읽어줘", "current_time_ms": 12_000},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "gemini-agent"
    assert response.json()["action"] == "read_summary"
