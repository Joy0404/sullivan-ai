from app.core.demo import build_demo_package
from app.core.lecture_agent import LectureAgent, parse_subtitles
from app.models import (
    AnalysisPackageInput,
    AssetInput,
    GlossaryItem,
    LectureCreate,
    StudyGuide,
    TranscriptSegment,
    VisualObservation,
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
