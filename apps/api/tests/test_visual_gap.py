from app.core.visual_gap import analyze_visual_observation
from app.models import GapAction, TranscriptSegment, VisualObservation


def speech(text: str = "여기서 식을 정리하겠습니다.") -> list[TranscriptSegment]:
    return [
        TranscriptSegment(
            segment_id="speech-1",
            start_ms=0,
            end_ms=12_000,
            text=text,
            confidence=0.98,
        )
    ]


def observation(**updates) -> VisualObservation:
    values = {
        "observation_id": "visual-1",
        "timestamp_ms": 5000,
        "screen_type": "board",
        "kind": "formula",
        "text": "v = v0 + at",
        "confidence": 0.96,
        "importance": 0.95,
    }
    values.update(updates)
    return VisualObservation(**values)


def test_unspoken_formula_interrupts_with_math_narration() -> None:
    gap = analyze_visual_observation(observation(), speech())

    assert gap.action == GapAction.INTERRUPT
    assert gap.safe_to_speak is True
    assert "더하기" in gap.public_description
    assert gap.source_text == "v = v0 + at"


def test_already_spoken_visual_is_indexed_without_interruption() -> None:
    gap = analyze_visual_observation(
        observation(),
        speech("v 는 v0 더하기 at, 즉 v = v0 + at 입니다."),
    )

    assert gap.action == GapAction.INDEX_ONLY
    assert gap.safe_to_speak is True
    assert gap.spoken_overlap >= 0.72


def test_low_confidence_content_is_held_and_never_leaked() -> None:
    gap = analyze_visual_observation(
        observation(text="정확하지 않은 값 18.7", confidence=0.4, kind="number"),
        speech(),
    )

    assert gap.action == GapAction.HOLD
    assert gap.safe_to_speak is False
    assert gap.public_description == ""
    assert gap.source_text is None


def test_sign_change_is_described_explicitly() -> None:
    gap = analyze_visual_observation(
        observation(text="y = 2x - 3"),
        speech("방금 식의 부호를 고치겠습니다."),
        previous_visual_text="y = 2x + 3",
    )

    assert gap.action == GapAction.INTERRUPT
    assert "수정" in gap.public_description
    assert "마이너스" in gap.public_description


def test_problem_answer_is_blocked() -> None:
    gap = analyze_visual_observation(
        observation(kind="answer", text="정답은 ④"),
        speech(),
        problem_mode=True,
    )

    assert gap.action == GapAction.HOLD
    assert gap.safe_to_speak is False
    assert gap.source_text is None


def test_verified_gemini_action_can_choose_natural_break() -> None:
    gap = analyze_visual_observation(
        observation(
            kind="concept",
            text="성운 → 원시별 → 주계열성",
            metadata={
                "verification": "corrected",
                "visible_evidence": ["칠판의 단계별 화살표"],
                "recommended_action": "DESCRIBE_AT_BREAK",
                "decision_reason": "판서 흐름이 중요하지만 현재 문장을 끊을 필요는 없습니다.",
            },
        ),
        speech("별의 탄생 과정을 살펴보겠습니다."),
    )

    assert gap.action == GapAction.DESCRIBE_AT_BREAK
    assert "판서 흐름" in gap.reason


def test_safety_policy_overrides_verified_model_answer_action() -> None:
    gap = analyze_visual_observation(
        observation(
            kind="answer",
            text="정답은 ④",
            metadata={
                "verification": "confirmed",
                "visible_evidence": ["④에 표시된 동그라미"],
                "recommended_action": "INTERRUPT",
                "decision_reason": "정답 표시가 보입니다.",
            },
        ),
        speech(),
        problem_mode=True,
    )

    assert gap.action == GapAction.HOLD
    assert gap.public_description == ""
