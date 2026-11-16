from app.core.demo import build_demo_package
from app.core.lecture_agent import LectureAgent, parse_subtitles
from app.models import (
    AnalysisPackageInput,
    AnalysisStatus,
    AssetInput,
    GlossaryItem,
    LectureCreate,
    LectureSnapshot,
    StudyGuide,
    TranscriptSegment,
    VisualObservation,
    VisualComponent,
)


def make_agent() -> tuple[LectureAgent, str]:
    agent = LectureAgent()
    session = agent.create_session(
        LectureCreate(
            title="접근성 데모",
            subject="통합",
            source_label="직접 제작 영상",
        )
    )
    return agent, session.session_id


def test_srt_and_vtt_timecodes_are_parsed() -> None:
    subtitles = """WEBVTT

00:00:01.000 --> 00:00:03.500
첫 번째 설명입니다.

2
00:04:05,250 --> 00:04:08,000
두 번째 설명입니다.
"""

    segments = parse_subtitles(subtitles)

    assert len(segments) == 2
    assert segments[0].start_ms == 1000
    assert segments[1].start_ms == 245_250


def test_video_is_registered_as_local_only_without_content() -> None:
    agent, session_id = make_agent()
    record = agent.register_asset(
        session_id,
        AssetInput(
            asset_id="video-1",
            name="lecture.mp4",
            kind="video",
            media_type="video/mp4",
            size_bytes=15_000_000,
            metadata={"client_local_playback": True},
        ),
    )

    assert record.processing_status == "local-only"
    assert "저장하지" in record.note
    assert not hasattr(record, "content_text")


def test_demo_runs_end_to_end_and_builds_accessible_review() -> None:
    agent, session_id = make_agent()
    snapshot = agent.analyze(session_id, build_demo_package())

    assert snapshot.active_mode == "mixed"
    assert snapshot.safe_description_count >= 3
    assert snapshot.held_count == 1
    assert snapshot.passage is not None
    assert snapshot.passage.highlighted_count == 1
    assert snapshot.review.visual_only_information
    assert snapshot.review.highlighted_sentences
    assert all(item.description != "18.7" for item in snapshot.review.visual_only_information)


def test_subtitle_asset_is_indexed_as_transcript() -> None:
    agent, session_id = make_agent()
    agent.register_asset(
        session_id,
        AssetInput(
            asset_id="subtitle-1",
            name="lecture.srt",
            kind="subtitle",
            media_type="text/plain",
            content_text="00:00:01,000 --> 00:00:02,000\n안녕하세요.",
        ),
    )

    snapshot = agent.snapshot(session_id)
    assert snapshot.transcript_segments[0].text == "안녕하세요."


def test_sensitive_identifiers_are_redacted_from_every_public_output() -> None:
    agent, session_id = make_agent()
    snapshot = agent.analyze(
        session_id,
        AnalysisPackageInput(
            transcript_segments=[
                TranscriptSegment(
                    segment_id="private-speech",
                    start_ms=0,
                    end_ms=1000,
                    text="연락처는 010-1234-5678이고 메일은 student@example.com입니다.",
                )
            ],
            visual_observations=[
                VisualObservation(
                    observation_id="private-screen",
                    timestamp_ms=2000,
                    screen_type="slide",
                    kind="concept",
                    text="student@example.com",
                    annotation="연락처 010 9876 5432",
                    confidence=0.95,
                    importance=0.9,
                )
            ],
            passage_text="학생 연락처는 01012345678이다.",
            study_guide=StudyGuide(
                overview="문의: student@example.com",
                glossary=[
                    GlossaryItem(term="연락처", definition="010-1111-2222")
                ],
            ),
        ),
    )

    serialized = snapshot.model_dump_json()
    assert "student@example.com" not in serialized
    assert "010-1234-5678" not in serialized
    assert "01012345678" not in serialized
    assert "[개인정보 비공개]" in serialized
import pytest
from pydantic import ValidationError



@pytest.mark.parametrize("held_mode", ["low_confidence", "disagreed", "answer"])
def test_candidate_never_leaks_through_any_snapshot_or_navigation_output(held_mode: str) -> None:
    agent = LectureAgent()
    session = agent.create_session(LectureCreate(title="안전 경계", problem_mode=held_mode == "answer"))
    secret = "PRIVATE_COMPONENT_18.7"
    components = []
    kind = "answer" if held_mode == "answer" else "number"
    confidence = .4 if held_mode == "low_confidence" else .99
    metadata = {}
    if held_mode == "disagreed":
        components = [VisualComponent(component_id="part", text=secret, kind="number", confidence=.99,
                                      verification="disagreed", visible_evidence=[secret], location="formula_right_number")]
        metadata = {"verification": "confirmed"}
    agent.register_asset(session.session_id, AssetInput(asset_id="original", name="문서.txt", kind="passage",
                         content_text=f"처음 등록한 {secret} 문장입니다."))
    snapshot = agent.analyze(session.session_id, AnalysisPackageInput(
        transcript_segments=[TranscriptSegment(segment_id="leak", start_ms=0, end_ms=1000, text=f"반복된 {secret} 내용입니다.")],
        visual_observations=[VisualObservation(observation_id="held", timestamp_ms=500, screen_type="board",
            kind=kind, text=secret, annotation=secret, confidence=confidence, metadata=metadata, components=components)],
        passage_text=f"복습으로 우회한 {secret} 문장입니다.", highlighted_texts=[secret],
        study_guide=StudyGuide(overview=secret, concept_map=[secret], recall_questions=[secret],
                              glossary=[GlossaryItem(term=secret, definition=secret)]),
    ))
    assert secret not in snapshot.model_dump_json()
    assert secret not in agent.navigate(session.session_id, "현재 문단", None).model_dump_json()
    assert snapshot.visual_gaps[0].source_text is None
    assert not snapshot.review.core_summary
    assert snapshot.study_guide == StudyGuide()
    agent.register_asset(session.session_id, AssetInput(asset_id="later", name=f"{secret}.srt", kind="subtitle",
                         content_text=f"00:00:01,000 --> 00:00:02,000\n다시 들어온 {secret}"))
    assert secret not in agent.snapshot(session.session_id).model_dump_json()


def test_partial_uncertainty_keeps_known_narration_but_clears_unproven_aggregate_guide() -> None:
    agent, session_id = make_agent()
    snapshot = agent.analyze(session_id, AnalysisPackageInput(
        visual_observations=[VisualObservation(
            observation_id="partial", timestamp_ms=1000, screen_type="board", kind="formula", text="x = 7; PRIVATE_18.7",
            metadata={"verification": "confirmed"}, components=[
                VisualComponent(component_id="known", kind="formula", text="x = 7", confidence=.99,
                                verification="confirmed", visible_evidence=["x = 7"]),
                VisualComponent(component_id="unclear", kind="number", text="PRIVATE_18.7", confidence=.4,
                                verification="uncertain", location="formula_right_number"),
            ])], study_guide=StudyGuide(overview="흐린 값에 대한 출처 없는 재해석입니다."),
    ))
    gap = snapshot.visual_gaps[0]
    assert gap.safe_to_speak and gap.source_text == "x = 7"
    assert "식 오른쪽의 숫자" in gap.public_description
    assert "PRIVATE" not in snapshot.model_dump_json()
    assert snapshot.study_guide == StudyGuide()
    assert snapshot.review.visual_only_information[0].description == gap.public_description


def test_loaded_snapshot_sanitizes_unsafe_gap_concepts_review_and_notice_text() -> None:
    agent, session_id = make_agent()
    raw = agent.snapshot(session_id).model_dump(mode="json")
    secret = "UNSAFE_LOADED_CANDIDATE_777"
    raw['visual_gaps'] = [dict(gap_id='held', observation_id='old', timestamp_ms=0, screen_type='board',
        kind='number', action='INTERRUPT', safe_to_speak=True, public_description=secret, reason=secret,
        confidence=.4, importance=.9, spoken_overlap=0, source_text=secret,
        hold_notices=[{'location':secret, 'text':secret}])]
    raw['concept_index'] = [dict(concept_id='old-concept', keyword=secret, timestamp_ms=0, end_ms=1000, ai_explanation=secret)]
    raw['transcript_segments'] = [dict(segment_id='old-speech', start_ms=0, end_ms=1000, text=secret)]
    item = dict(item_id='old-review', timestamp_ms=0, kind='number', title=secret, description=secret)
    raw['review'] = dict(core_summary=[secret], visual_only_information=[item], highlighted_sentences=[item], key_segments=[item])
    raw['study_guide'] = {'overview': secret}
    result = LectureSnapshot.model_validate(raw)
    assert secret not in result.model_dump_json()
    assert result.visual_gaps[0].source_text is None and result.visual_gaps[0].action.value == 'HOLD'
    assert result.visual_gaps[0].hold_notices[0].text.startswith('‘이 장면의 판서’')
    assert not result.concept_index and not result.transcript_segments and not result.review.key_segments


def test_analysis_provenance_is_server_only_and_unknown_for_old_snapshots() -> None:
    agent, session_id = make_agent()
    old = agent.snapshot(session_id).model_dump(mode="json")
    old.pop('analysis_status')
    restored = LectureSnapshot.model_validate(old)
    assert restored.analysis_status.state == 'unknown'
    assert restored.analysis_status.label == '분석 상태 확인 불가'
    with pytest.raises(ValidationError):
        AnalysisPackageInput.model_validate({'analysis_status': {'state': 'completed', 'provider': 'gemini'}})
    running = agent.set_analysis_status(session_id, 'analyzing', 'gemini')
    completed = agent.set_analysis_status(session_id, 'completed', 'gemini')
    assert running.run_id and running.run_id == completed.run_id
    assert agent.snapshot(session_id).analysis_status.label == 'Gemini 분석 완료'
    assert completed.recorded_at and completed.provider == 'gemini'
    assert AnalysisStatus(state='completed').label == '분석 상태 확인 불가'
    assert AnalysisStatus(state='not_run').label == '영상 분석 미실행'
    assert agent.analyze_demo(session_id).analysis_status.label == '사전 준비 샘플'


def test_confirmed_component_survives_same_numeral_in_an_uncertain_component() -> None:
    agent, session_id = make_agent()
    snapshot = agent.analyze(session_id, AnalysisPackageInput(visual_observations=[VisualObservation(
        observation_id='scoped-parts',timestamp_ms=1000,screen_type='board',kind='formula',text='x = 7; PRIVATE_UNIT_7',
        confidence=.99,metadata={'verification':'confirmed'},components=[
            VisualComponent(component_id='known',kind='formula',text='x = 7',confidence=.99,
                verification='confirmed',visible_evidence=['x = 7']),
            VisualComponent(component_id='unknown',kind='number',text='PRIVATE_UNIT_7',confidence=.4,
                verification='uncertain',location='vertical_axis_unit')
        ])],passage_text='출처 없이 옮긴 PRIVATE_UNIT_7입니다.'))
    gap=snapshot.visual_gaps[0]
    assert gap.safe_to_speak and gap.source_text=='x = 7'
    assert '세로축의 단위' in gap.public_description
    assert snapshot.review.visual_only_information[0].description==gap.public_description
    assert 'PRIVATE_UNIT' not in snapshot.model_dump_json()
    assert snapshot.passage is None
    assert agent.snapshot(session_id).visual_gaps[0].safe_to_speak


@pytest.mark.parametrize('spoken,action', [
    ('이 엑스 더하기 일은 칠입니다', 'INDEX_ONLY'),
    ('이 엑스 더하기 일은 팔입니다', 'INTERRUPT'),
])
def test_analysis_pipeline_compares_spoken_korean_formula(spoken: str, action: str) -> None:
    agent, session_id = make_agent()
    snapshot = agent.analyze(session_id, AnalysisPackageInput(
        transcript_segments=[TranscriptSegment(segment_id='korean-speech',start_ms=0,end_ms=2000,text=spoken,confidence=.98)],
        visual_observations=[VisualObservation(observation_id='korean-board',timestamp_ms=1000,
            screen_type='board',kind='formula',text='2x + 1 = 7',confidence=.98,importance=.95)],
    ))
    gap=snapshot.visual_gaps[0]
    assert gap.action.value==action
    assert gap.safe_to_speak and gap.source_text=='2x + 1 = 7'
