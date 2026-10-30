from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from app.core.passage import navigate_passage, structure_passage
from app.core.visual_gap import analyze_visual_observation
from app.models import (
    AnalysisPackageInput,
    AssetInput,
    AssetRecord,
    GapAction,
    LectureCreate,
    LectureSession,
    LectureSnapshot,
    LectureStatus,
    LessonReview,
    NavigationResponse,
    PassageDocument,
    ReviewItem,
    StudyGuide,
    TranscriptSegment,
    VisualGap,
    VisualObservation,
)


SENSITIVE_TEXT_PATTERNS = (
    re.compile(
        r"(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![A-Z])",
        re.IGNORECASE,
    ),
    re.compile(r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)"),
    re.compile(r"(?<!\d)\d{6}[ -]?[1-4]\d{6}(?!\d)"),
)


def redact_sensitive_text(value: str | None) -> str | None:
    """Remove common personal identifiers before they enter public outputs."""
    if value is None:
        return None
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS:
        redacted = pattern.sub("[개인정보 비공개]", redacted)
    return redacted


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LectureNotFoundError(KeyError):
    pass


class InvalidAnalysisError(ValueError):
    pass


def _timecode_to_ms(value: str) -> int:
    normalized = value.strip().replace(",", ".")
    parts = normalized.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes, seconds = "0", parts[0], parts[1]
        else:
            return 0
        return int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000)
    except ValueError:
        return 0


def parse_subtitles(content: str) -> list[TranscriptSegment]:
    cleaned = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", cleaned)
    segments: list[TranscriptSegment] = []
    time_pattern = re.compile(
        r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})\s*-->\s*"
        r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3})"
    )
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        time_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue
        match = time_pattern.search(lines[time_index])
        if not match:
            continue
        text = " ".join(lines[time_index + 1 :]).strip()
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                segment_id=f"subtitle-{len(segments) + 1}",
                start_ms=_timecode_to_ms(match.group("start")),
                end_ms=_timecode_to_ms(match.group("end")),
                text=re.sub(r"<[^>]+>", "", text),
                confidence=1.0,
            )
        )
    return segments


class LectureAgent:
    """In-memory MVP for accessible internet-lecture analysis.

    Raw video never enters this stateful class. The browser keeps the playback
    copy local; an explicitly consented adapter may process a temporary copy
    and submits only time-coded text observations to this class.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, LectureSession] = {}
        self._assets: dict[str, list[AssetRecord]] = {}
        self._transcripts: dict[str, list[TranscriptSegment]] = {}
        self._visuals: dict[str, list[VisualObservation]] = {}
        self._gaps: dict[str, list[VisualGap]] = {}
        self._passages: dict[str, PassageDocument | None] = {}
        self._reviews: dict[str, LessonReview] = {}
        self._study_guides: dict[str, StudyGuide] = {}

    def create_session(self, payload: LectureCreate) -> LectureSession:
        session = LectureSession(
            **payload.model_dump(),
            session_id=f"lecture-{uuid4().hex[:10]}",
            created_at=_now(),
        )
        self._sessions[session.session_id] = session
        self._assets[session.session_id] = []
        self._transcripts[session.session_id] = []
        self._visuals[session.session_id] = []
        self._gaps[session.session_id] = []
        self._passages[session.session_id] = None
        self._reviews[session.session_id] = LessonReview()
        self._study_guides[session.session_id] = StudyGuide()
        return session

    def register_asset(self, session_id: str, payload: AssetInput) -> AssetRecord:
        self._get_session(session_id)
        if payload.kind == "video":
            status = "local-only"
            note = "원본 영상은 브라우저에서만 재생하며 서버에 저장하지 않습니다."
        elif payload.kind == "video_link":
            status = "needs-adapter"
            note = "링크는 등록되었으며 AI 영상 분석 어댑터의 결과를 기다립니다."
        elif payload.content_text:
            status = "indexed"
            note = "텍스트 내용만 메모리에서 색인했으며 원본 파일은 저장하지 않습니다."
        else:
            status = "needs-adapter"
            note = "이 형식은 OCR·STT 어댑터 연결이 필요합니다."

        record = AssetRecord(
            asset_id=payload.asset_id,
            name=payload.name,
            kind=payload.kind,
            media_type=payload.media_type,
            size_bytes=payload.size_bytes,
            processing_status=status,
            note=note,
        )
        records = self._assets[session_id]
        records[:] = [item for item in records if item.asset_id != payload.asset_id]
        records.append(record)

        safe_content = redact_sensitive_text(payload.content_text)
        if payload.kind == "subtitle" and safe_content:
            parsed = parse_subtitles(safe_content)
            self._transcripts[session_id] = self._merge_by_id(
                self._transcripts[session_id], parsed, "segment_id"
            )
        elif payload.kind in {"passage", "slides"} and safe_content:
            self._passages[session_id] = structure_passage(
                safe_content,
                title=payload.name,
            )

        self._set_status(session_id, LectureStatus.ACTIVE)
        self._reviews[session_id] = self._build_review(session_id)
        return record

    def mark_asset_indexed(
        self, session_id: str, asset_id: str, note: str | None = None
    ) -> AssetRecord:
        self._get_session(session_id)
        records = self._assets[session_id]
        for index, record in enumerate(records):
            if record.asset_id == asset_id:
                updated = record.model_copy(
                    update={
                        "processing_status": "indexed",
                        "note": note
                        or "AI 분석 어댑터 결과를 검증해 세션에 반영했습니다. 원본 영상은 저장하지 않습니다.",
                    }
                )
                records[index] = updated
                return updated
        raise KeyError(asset_id)

    def analyze(
        self, session_id: str, payload: AnalysisPackageInput
    ) -> LectureSnapshot:
        session = self._get_session(session_id)
        self._set_status(session_id, LectureStatus.ANALYZING)

        safe_transcripts = [
            item.model_copy(update={"text": redact_sensitive_text(item.text) or ""})
            for item in payload.transcript_segments
        ]
        safe_visuals = [
            item.model_copy(
                update={
                    "text": redact_sensitive_text(item.text) or "",
                    "annotation": redact_sensitive_text(item.annotation),
                }
            )
            for item in payload.visual_observations
        ]
        safe_guide = payload.study_guide.model_copy(
            update={
                "overview": redact_sensitive_text(payload.study_guide.overview) or "",
                "concept_map": [
                    redact_sensitive_text(item) or "" for item in payload.study_guide.concept_map
                ],
                "glossary": [
                    item.model_copy(
                        update={
                            "term": redact_sensitive_text(item.term) or "비공개 용어",
                            "definition": redact_sensitive_text(item.definition) or "비공개",
                        }
                    )
                    for item in payload.study_guide.glossary
                ],
                "recall_questions": [
                    redact_sensitive_text(item) or "" for item in payload.study_guide.recall_questions
                ],
            }
        )

        if safe_transcripts:
            self._transcripts[session_id] = self._merge_by_id(
                self._transcripts[session_id], safe_transcripts, "segment_id"
            )
        if safe_visuals:
            self._visuals[session_id] = self._merge_by_id(
                self._visuals[session_id], safe_visuals, "observation_id"
            )
        if safe_guide.model_dump(exclude_defaults=True):
            self._study_guides[session_id] = safe_guide

        visual_hints = [
            (item.text, item.timestamp_ms)
            for item in self._visuals[session_id]
            if item.text
        ]
        highlighted = [
            *[redact_sensitive_text(item) or "" for item in payload.highlighted_texts],
            *[
                item.text
                for item in self._visuals[session_id]
                if item.kind == "highlight" and item.text
            ],
        ]
        safe_passage_text = redact_sensitive_text(payload.passage_text)
        if safe_passage_text:
            self._passages[session_id] = structure_passage(
                safe_passage_text,
                highlighted,
                visual_hints,
                title=f"{session.title} 지문",
            )
        elif self._passages[session_id] and highlighted:
            existing_text = "\n\n".join(
                " ".join(sentence.text for sentence in paragraph.sentences)
                for paragraph in self._passages[session_id].paragraphs
            )
            self._passages[session_id] = structure_passage(
                existing_text,
                highlighted,
                visual_hints,
                title=self._passages[session_id].title,
            )

        previous_by_screen: dict[str, str] = {}
        gaps: list[VisualGap] = []
        for observation in sorted(
            self._visuals[session_id], key=lambda item: item.timestamp_ms
        ):
            previous = previous_by_screen.get(observation.screen_type)
            gap = analyze_visual_observation(
                observation,
                self._transcripts[session_id],
                previous,
                problem_mode=session.problem_mode,
            )
            gaps.append(gap)
            if observation.text:
                previous_by_screen[observation.screen_type] = observation.text

        self._gaps[session_id] = gaps
        self._reviews[session_id] = self._build_review(session_id)
        self._set_status(session_id, LectureStatus.ACTIVE)
        return self.snapshot(session_id)

    def snapshot(self, session_id: str) -> LectureSnapshot:
        session = self._get_session(session_id)
        gaps = self._gaps[session_id]
        return LectureSnapshot(
            session=session,
            assets=list(self._assets[session_id]),
            transcript_segments=list(self._transcripts[session_id]),
            visual_gaps=list(gaps),
            passage=self._passages[session_id],
            review=self._reviews[session_id],
            study_guide=self._study_guides[session_id],
            active_mode=self._active_mode(session_id),
            safe_description_count=sum(
                gap.safe_to_speak and gap.action in {GapAction.INTERRUPT, GapAction.DESCRIBE_AT_BREAK}
                for gap in gaps
            ),
            held_count=sum(gap.action == GapAction.HOLD for gap in gaps),
        )

    def navigate(
        self, session_id: str, command: str, current_sentence_id: str | None
    ) -> NavigationResponse:
        self._get_session(session_id)
        return navigate_passage(
            self._passages[session_id], command, current_sentence_id
        )

    def end(self, session_id: str) -> LectureSession:
        self._get_session(session_id)
        self._reviews[session_id] = self._build_review(session_id)
        return self._set_status(session_id, LectureStatus.ENDED)

    def _build_review(self, session_id: str) -> LessonReview:
        core_summary: list[str] = []
        for segment in self._transcripts[session_id]:
            cleaned = segment.text.strip()
            if cleaned and cleaned not in core_summary:
                core_summary.append(cleaned)
            if len(core_summary) == 3:
                break

        visual_items = [
            ReviewItem(
                item_id=gap.gap_id,
                timestamp_ms=gap.timestamp_ms,
                kind=gap.kind,
                title="화면으로만 전달된 정보",
                description=gap.public_description,
            )
            for gap in self._gaps[session_id]
            if gap.safe_to_speak
            and gap.public_description
            and gap.action in {GapAction.INTERRUPT, GapAction.DESCRIBE_AT_BREAK}
        ]

        highlighted_items: list[ReviewItem] = []
        passage = self._passages[session_id]
        if passage:
            for paragraph in passage.paragraphs:
                for sentence in paragraph.sentences:
                    if sentence.highlighted:
                        highlighted_items.append(
                            ReviewItem(
                                item_id=f"review-{sentence.sentence_id}",
                                timestamp_ms=sentence.timestamp_ms or 0,
                                kind="highlight",
                                title=f"{sentence.paragraph_index}문단 {sentence.sentence_index}번째 문장",
                                description=sentence.text,
                            )
                        )

        key_segments = sorted(
            [*visual_items, *highlighted_items],
            key=lambda item: item.timestamp_ms,
        )[:8]
        return LessonReview(
            core_summary=core_summary,
            visual_only_information=visual_items,
            highlighted_sentences=highlighted_items,
            key_segments=key_segments,
        )

    def _active_mode(self, session_id: str) -> str:
        has_passage = self._passages[session_id] is not None
        screen_types = {item.screen_type for item in self._visuals[session_id]}
        has_board = "board" in screen_types or "graph" in screen_types
        if has_passage and has_board:
            return "mixed"
        if has_passage:
            return "passage"
        if has_board:
            return "board"
        if screen_types:
            return "slides"
        return "waiting"

    def _get_session(self, session_id: str) -> LectureSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise LectureNotFoundError(session_id)
        return session

    def _set_status(self, session_id: str, status: LectureStatus) -> LectureSession:
        session = self._get_session(session_id).model_copy(update={"status": status})
        self._sessions[session_id] = session
        return session

    @staticmethod
    def _merge_by_id(existing: list, incoming: list, field: str) -> list:
        merged = {getattr(item, field): item for item in existing}
        for item in incoming:
            merged[getattr(item, field)] = item
        return sorted(
            merged.values(),
            key=lambda item: getattr(item, "start_ms", getattr(item, "timestamp_ms", 0)),
        )
