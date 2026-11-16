import pytest

from app.core.visual_gap import analyze_visual_observation, normalize_critical_text
from app.models import GapAction, TranscriptSegment, VisualComponent, VisualObservation


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


@pytest.mark.parametrize("visual,spoken", [
    ("화면의 긴 조건은 모두 같고 식 오른쪽 숫자는 7 입니다.", "화면의 긴 조건은 모두 같고 식 오른쪽 숫자는 8 입니다."),
    ("화면의 긴 조건은 모두 같고 식은 y = 2x + 3 입니다.", "화면의 긴 조건은 모두 같고 식은 y = 2x - 3 입니다."),
    ("화면의 긴 조건은 모두 같고 x < 7 입니다.", "화면의 긴 조건은 모두 같고 x <= 7 입니다."),
    ("화면의 긴 조건은 모두 같고 x > 7 입니다.", "화면의 긴 조건은 모두 같고 x >= 7 입니다."),
    ("화면의 긴 조건은 모두 같고 거리는 7 m 입니다.", "화면의 긴 조건은 모두 같고 거리는 7 cm 입니다."),
    ("화면의 긴 조건은 모두 같고 시간은 7 s 입니다.", "화면의 긴 조건은 모두 같고 시간은 7 ms 입니다."),
    ("화면의 긴 조건은 모두 같고 x = 7, y = 8 입니다.", "화면의 긴 조건은 모두 같고 x = 8, y = 7 입니다."),
])
def test_critical_difference_overrides_high_text_overlap_and_model_index(visual: str, spoken: str) -> None:
    gap = analyze_visual_observation(observation(text=visual, metadata={
        "verification": "confirmed", "recommended_action": "INDEX_ONLY",
        "visible_evidence": [visual],
    }), speech(spoken))
    assert gap.spoken_overlap >= .72
    assert gap.action == GapAction.INTERRUPT
    assert gap.safe_to_speak


@pytest.mark.parametrize("visual,spoken", [
    ("2x + 1 = 7", "2x 더하기 1은 7"),
    ("속도는 7 m 입니다", "속도는 7 미터 입니다"),
    ("화면 조건 x <= 7 입니다", "화면 조건 x ≤ 7 입니다"),
])
def test_communicated_critical_values_keep_index_only(visual: str, spoken: str) -> None:
    gap = analyze_visual_observation(observation(text=visual), speech(spoken))
    assert gap.action == GapAction.INDEX_ONLY


def component(ident: str, text: str, **updates) -> VisualComponent:
    values = dict(component_id=ident, text=text, kind="formula", confidence=.98,
                  verification="confirmed", visible_evidence=[text])
    values.update(updates)
    return VisualComponent(**values)


def test_partial_component_narrates_only_confirmed_text_and_notice_together() -> None:
    gap = analyze_visual_observation(observation(
        text="x = 7 그리고 PRIVATE_CANDIDATE_18.7", annotation="PRIVATE_CANDIDATE_18.7",
        metadata={"verification": "confirmed", "decision_reason": "PRIVATE_CANDIDATE_18.7"},
        components=[component("known", "x = 7"), component("held", "PRIVATE_CANDIDATE_18.7",
                    confidence=.4, location="vertical_axis_unit", verification="uncertain")],
    ), speech("x = 7"))
    assert gap.safe_to_speak and gap.action == GapAction.DESCRIBE_AT_BREAK
    assert gap.source_text == "x = 7"
    assert "PRIVATE_CANDIDATE" not in gap.model_dump_json()
    assert "‘세로축의 단위’ 부분은 확실치 않아서 설명을 보류하겠습니다." in gap.public_description
    assert gap.public_description.count(gap.hold_notices[0].text) == 1


@pytest.mark.parametrize("location,label", [
    ("formula_right_number", "식 오른쪽의 숫자"),
    ("underlined_sentence", "밑줄 친 문장"),
    ("unknown", "이 장면의 판서"),
    ("PRIVATE_PROVIDER_LOCATION_777", "이 장면의 판서"),
])
def test_fully_held_components_have_only_allowlisted_separate_notice(location: str, label: str) -> None:
    gap = analyze_visual_observation(observation(
        text="PRIVATE_CANDIDATE_777", metadata={"verification": "confirmed"},
        components=[component("uncertain", "PRIVATE_CANDIDATE_777", confidence=.5,
                              location=location, verification="uncertain")],
    ), speech())
    assert gap.action == GapAction.HOLD and not gap.safe_to_speak
    assert gap.public_description == "" and gap.source_text is None
    assert gap.hold_notices[0].text == f"‘{label}’ 부분은 확실치 않아서 설명을 보류하겠습니다."
    assert "PRIVATE" not in gap.model_dump_json()


def test_parent_low_confidence_overrides_confirmed_components() -> None:
    gap = analyze_visual_observation(observation(
        confidence=.71, text="PRIVATE_PARENT_777", metadata={"verification": "confirmed"},
        components=[component("known", "PRIVATE_PARENT_777")],
    ), speech())
    assert gap.action == GapAction.HOLD and not gap.safe_to_speak
    assert not gap.public_description and gap.source_text is None
    assert gap.hold_notices[0].text.startswith("‘이 장면의 판서’")


@pytest.mark.parametrize("updates", [{"verification": "uncertain"}, {"verification": "disagreed"},
                                     {"visible_evidence": []}, {"confidence": .71}])
def test_component_does_not_borrow_parent_confidence_or_evidence(updates: dict) -> None:
    gap = analyze_visual_observation(observation(
        text="PRIVATE_PART_777", metadata={"verification": "confirmed", "visible_evidence": ["다른 부분"]},
        components=[component("part", "PRIVATE_PART_777", **updates)],
    ), speech())
    assert gap.action == GapAction.HOLD and gap.source_text is None
    assert "PRIVATE" not in gap.model_dump_json()


def test_unverified_parent_cannot_publish_confirmed_component() -> None:
    gap = analyze_visual_observation(observation(text="PRIVATE_777", components=[component("part", "PRIVATE_777")]), speech())
    assert gap.action == GapAction.HOLD and not gap.safe_to_speak


def test_problem_answer_never_uses_uncertainty_notice_even_with_low_confidence() -> None:
    gap = analyze_visual_observation(observation(kind="answer", text="PRIVATE_ANSWER_777", confidence=.5), speech(), problem_mode=True)
    assert gap.action == GapAction.HOLD and gap.hold_notices == []
    assert "PRIVATE" not in gap.model_dump_json()


def test_annotation_cannot_replace_verified_numeric_reading() -> None:
    gap = analyze_visual_observation(observation(text="x = 7", annotation="x = 8"), speech("x = 9"))
    assert "8" not in gap.public_description and "7" in gap.public_description


def test_prior_matching_equation_does_not_hide_current_numeric_contradiction() -> None:
    segments = [
        TranscriptSegment(segment_id="prior", start_ms=0, end_ms=3500, text="2x + 1 = 7", confidence=.99),
        TranscriptSegment(segment_id="current", start_ms=5500, end_ms=8500, text="2x + 1 = 8", confidence=.99),
    ]
    gap = analyze_visual_observation(observation(timestamp_ms=6500, text="2x + 1 = 7"), segments)
    assert gap.spoken_overlap == 1  # Broad context contains the old equation.
    assert gap.action == GapAction.INTERRUPT


@pytest.mark.parametrize('visual,spoken',[
    ('2x + 1 = 7','1x + 2 = 7'),
    ('2x - 1 = 7','1x - 2 = 7'),
    ('x = 5m, y = 10s','x = 10s, y = 5m'),
])
def test_same_number_multiset_does_not_conceal_operand_or_unit_binding_changes(visual,spoken):
    gap=analyze_visual_observation(observation(text=visual,metadata={'verification':'confirmed','recommended_action':'INDEX_ONLY'}),speech(spoken))
    assert gap.action==GapAction.INTERRUPT


def test_nearest_speech_wins_over_older_matching_numeric_context() -> None:
    segments = [
        TranscriptSegment(segment_id="prior", start_ms=0, end_ms=3500, text="2x + 1 = 7", confidence=.99),
        TranscriptSegment(segment_id="latest", start_ms=5500, end_ms=6500, text="2x + 1 = 8", confidence=.99),
    ]
    gap = analyze_visual_observation(observation(timestamp_ms=7000, text="2x + 1 = 7"), segments)
    assert gap.action == GapAction.INTERRUPT


@pytest.mark.parametrize('visual,spoken', [
    ('2x + 1 = 7', '이 엑스 더하기 일은 칠입니다'),
    ('2x + 1 = 7', '이엑스 더하기 일은 칠입니다.'),
    ('2x + 1 = 7', '이 식은 이 엑스 더하기 일은 칠입니다. 다음을 보겠습니다.'),
    ('x = 7', '엑스는 칠입니다'),
    ('2y + 1 = 7', '이 와이 더하기 일은 칠입니다'),
    ('2z + 1 = 7', '이 제트 더하기 일은 칠입니다'),
    ('12x + 1 = 27', '십이 엑스 더하기 일은 이십칠입니다'),
])
def test_spoken_korean_math_matches_the_confirmed_board(visual: str, spoken: str) -> None:
    gap = analyze_visual_observation(observation(text=visual), speech(spoken))
    assert gap.action == GapAction.INDEX_ONLY
    assert gap.spoken_overlap == 1
    assert gap.safe_to_speak and gap.source_text == visual


@pytest.mark.parametrize('spoken', [
    '이 엑스 더하기 일은 팔입니다',
    '일 엑스 더하기 이는 칠입니다',
    '이 엑스 빼기 일은 칠입니다',
    '이 엑스 더하기 일은 칠십입니다',
    '이 엑스 더하기 일은 칠 점 오입니다',
    '십 이 엑스 더하기 일은 칠입니다',
    '이 엑스 더하기 일은 칠.오입니다',
    '이 엑스 더하기 일은 칠,오입니다',
    '이 엑스 더하기 일은 칠 . 오입니다',
])
def test_different_or_unsupported_spoken_korean_values_still_interrupt(spoken: str) -> None:
    gap = analyze_visual_observation(observation(text='2x + 1 = 7', metadata={
        'verification': 'confirmed', 'recommended_action': 'INDEX_ONLY',
    }), speech(spoken))
    assert gap.action == GapAction.INTERRUPT
    assert gap.safe_to_speak and '7' in gap.public_description


@pytest.mark.parametrize('text', [
    '이 영상은 칠판의 내용을 설명합니다.',
    '이 문장의 일은 칠 일을 설명합니다.',
    '이 엑스 표시를 보세요.',
])
def test_korean_numeral_syllables_in_prose_are_not_rewritten(text: str) -> None:
    assert normalize_critical_text(text) == text


def test_spaced_composite_coefficient_is_not_matched_by_its_last_digit() -> None:
    gap = analyze_visual_observation(observation(text='7x + 1 = 7'),
                                     speech('이십 칠 엑스 더하기 일은 칠입니다'))
    assert gap.action == GapAction.INTERRUPT


def test_korean_math_matching_preserves_low_confidence_and_answer_blocking() -> None:
    spoken = speech('이 엑스 더하기 일은 칠입니다')
    for updates, problem_mode in (({'confidence': .71}, False), ({'kind': 'answer'}, True)):
        gap = analyze_visual_observation(observation(text='2x + 1 = 7', **updates), spoken, problem_mode=problem_mode)
        assert gap.action == GapAction.HOLD
        assert not gap.safe_to_speak and gap.source_text is None and not gap.public_description
