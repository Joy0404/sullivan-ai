from __future__ import annotations

from enum import Enum
import re
from typing import Any, Literal
import unicodedata

from pydantic import BaseModel, Field, SecretStr, computed_field, field_validator, model_validator


class LectureStatus(str, Enum):
    READY = "ready"
    ANALYZING = "analyzing"
    ACTIVE = "active"
    ENDED = "ended"


class GapAction(str, Enum):
    INTERRUPT = "INTERRUPT"
    DESCRIBE_AT_BREAK = "DESCRIBE_AT_BREAK"
    INDEX_ONLY = "INDEX_ONLY"
    HOLD = "HOLD"
    SKIP = "SKIP"


class VisualLocation(str, Enum):
    UNKNOWN = "unknown"
    VERTICAL_AXIS_UNIT = "vertical_axis_unit"
    HORIZONTAL_AXIS_UNIT = "horizontal_axis_unit"
    FORMULA_RIGHT_NUMBER = "formula_right_number"
    FORMULA_NUMBER = "formula_number"
    FORMULA_SIGN = "formula_sign"
    FORMULA_INEQUALITY = "formula_inequality"
    UNDERLINED_SENTENCE = "underlined_sentence"
    EMPHASIZED_TEXT = "emphasized_text"
    UNIT = "unit"
    WHOLE_BOARD = "whole_board"
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


VISUAL_LOCATION_LABELS = {
    VisualLocation.UNKNOWN: "이 장면의 판서",
    VisualLocation.VERTICAL_AXIS_UNIT: "세로축의 단위",
    VisualLocation.HORIZONTAL_AXIS_UNIT: "가로축의 단위",
    VisualLocation.FORMULA_RIGHT_NUMBER: "식 오른쪽의 숫자",
    VisualLocation.FORMULA_NUMBER: "식의 숫자",
    VisualLocation.FORMULA_SIGN: "식의 부호",
    VisualLocation.FORMULA_INEQUALITY: "식의 부등호",
    VisualLocation.UNDERLINED_SENTENCE: "밑줄 친 문장",
    VisualLocation.EMPHASIZED_TEXT: "강조된 글자",
    VisualLocation.UNIT: "단위",
    VisualLocation.WHOLE_BOARD: "이 장면의 판서",
    VisualLocation.TOP_LEFT: "화면 왼쪽 위",
    VisualLocation.TOP_CENTER: "화면 위쪽 가운데",
    VisualLocation.TOP_RIGHT: "화면 오른쪽 위",
    VisualLocation.CENTER_LEFT: "화면 왼쪽 가운데",
    VisualLocation.CENTER: "화면 가운데",
    VisualLocation.CENTER_RIGHT: "화면 오른쪽 가운데",
    VisualLocation.BOTTOM_LEFT: "화면 왼쪽 아래",
    VisualLocation.BOTTOM_CENTER: "화면 아래쪽 가운데",
    VisualLocation.BOTTOM_RIGHT: "화면 오른쪽 아래",
}


def safe_visual_location(value: Any) -> VisualLocation:
    try:
        return VisualLocation(value)
    except (ValueError, TypeError):
        return VisualLocation.UNKNOWN


class SafeHoldNotice(BaseModel):
    """The public message is constructed from an allowlist, never model text."""

    code: Literal["visual_uncertain"] = "visual_uncertain"
    location: VisualLocation = VisualLocation.UNKNOWN

    _safe_location = field_validator("location", mode="before")(safe_visual_location)

    @computed_field
    @property
    def text(self) -> str:
        return f"‘{VISUAL_LOCATION_LABELS[self.location]}’ 부분은 확실치 않아서 설명을 보류하겠습니다."


VisualKind = Literal[
    "formula", "number", "condition", "highlight", "passage", "graph",
    "concept", "decoration", "answer",
]


class VisualComponent(BaseModel):
    component_id: str = Field(min_length=1, max_length=120)
    text: str = Field(default="", max_length=12_000)
    kind: VisualKind = "concept"
    confidence: float = Field(default=0, ge=0, le=1)
    location: VisualLocation = VisualLocation.UNKNOWN
    verification: Literal["confirmed", "corrected", "uncertain", "disagreed", "unverified"] = "unverified"
    visible_evidence: list[str] = Field(default_factory=list, max_length=20)

    _safe_location = field_validator("location", mode="before")(safe_visual_location)


AnalysisState = Literal["unknown", "not_run", "analyzing", "completed", "failed", "sample"]
AnalysisProvider = Literal["gemini", "adapter"]


class AnalysisStatus(BaseModel):
    state: AnalysisState = "unknown"
    provider: AnalysisProvider | None = None
    run_id: str | None = None
    recorded_at: str | None = None

    @computed_field
    @property
    def label(self) -> str:
        if self.state == "completed":
            return {"gemini": "Gemini 분석 완료", "adapter": "외부 어댑터 분석 완료"}.get(self.provider, "분석 상태 확인 불가")
        if self.state == "analyzing":
            return "Gemini 분석 중" if self.provider == "gemini" else "영상 분석 중"
        if self.state == "failed":
            return "Gemini 분석 실패" if self.provider == "gemini" else "영상 분석 실패"
        return {"unknown": "분석 상태 확인 불가", "not_run": "영상 분석 미실행", "sample": "사전 준비 샘플"}[self.state]


class LectureCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    subject: str = Field(default="일반", min_length=1, max_length=80)
    source_label: str = Field(default="사용자 보유 강의", max_length=120)
    preferred_mode: Literal["auto", "board", "passage", "slides"] = "auto"
    problem_mode: bool = False


class LectureSession(LectureCreate):
    session_id: str
    created_at: str
    status: LectureStatus = LectureStatus.READY
    policy_version: str = "internet-lecture-access-v1"


class AssetInput(BaseModel):
    asset_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=240)
    kind: Literal["video", "video_link", "subtitle", "passage", "slides", "analysis"]
    media_type: str = Field(default="application/octet-stream", max_length=120)
    size_bytes: int = Field(default=0, ge=0, le=2_000_000_000)
    content_text: str | None = Field(default=None, max_length=300_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetRecord(BaseModel):
    asset_id: str
    name: str
    kind: str
    media_type: str
    size_bytes: int
    processing_status: Literal["local-only", "remote-only", "indexed", "needs-adapter"]
    note: str


class VideoLinkInput(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    rights_confirmed: bool = False
    request_analysis: bool = True
    analysis_consent: bool = False
    access_code: SecretStr | None = Field(default=None, exclude=True)
    # Ignored by the public server: Gemini keys come only from server variables.
    gemini_api_key: SecretStr | None = Field(default=None, exclude=True)


class VideoLinkResult(BaseModel):
    asset: AssetRecord
    normalized_url: str
    playback_kind: Literal["direct", "youtube", "external"]
    playback_url: str
    analysis_status: Literal["completed", "needs-adapter", "registered-only"]
    message: str
    snapshot: "LectureSnapshot | None" = None


class TranscriptSegment(BaseModel):
    segment_id: str = Field(min_length=1, max_length=120)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=6000)
    confidence: float = Field(default=0.9, ge=0, le=1)


class VisualObservation(BaseModel):
    observation_id: str = Field(min_length=1, max_length=120)
    timestamp_ms: int = Field(ge=0)
    screen_type: Literal["board", "passage", "slide", "graph", "image"]
    kind: VisualKind = "concept"
    text: str = Field(default="", max_length=12_000)
    confidence: float = Field(default=0.9, ge=0, le=1)
    importance: float = Field(default=0.7, ge=0, le=1)
    annotation: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    location: VisualLocation = VisualLocation.UNKNOWN
    components: list[VisualComponent] = Field(default_factory=list, max_length=100)

    _safe_location = field_validator("location", mode="before")(safe_visual_location)


class GlossaryItem(BaseModel):
    term: str = Field(min_length=1, max_length=120)
    definition: str = Field(min_length=1, max_length=1200)


class StudyGuide(BaseModel):
    overview: str = Field(default="", max_length=6000)
    concept_map: list[str] = Field(default_factory=list, max_length=20)
    glossary: list[GlossaryItem] = Field(default_factory=list, max_length=40)
    recall_questions: list[str] = Field(default_factory=list, max_length=20)


class AnalysisPackageInput(BaseModel):
    # Provenance is server state, not an assertion supplied by imported JSON.
    model_config = {"extra": "ignore"}
    @model_validator(mode='before')
    @classmethod
    def server_owned_provenance(cls,value):
        if isinstance(value,dict) and 'analysis_status' in value:raise ValueError('분석 상태는 서버 처리 기록으로만 설정합니다.')
        return value
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    visual_observations: list[VisualObservation] = Field(default_factory=list)
    passage_text: str | None = Field(default=None, max_length=300_000)
    highlighted_texts: list[str] = Field(default_factory=list, max_length=100)
    study_guide: StudyGuide = Field(default_factory=StudyGuide)


class PassageSentence(BaseModel):
    sentence_id: str
    paragraph_index: int = Field(ge=1)
    sentence_index: int = Field(ge=1)
    text: str
    timestamp_ms: int | None = Field(default=None, ge=0)
    highlighted: bool = False


class PassageParagraph(BaseModel):
    paragraph_id: str
    paragraph_index: int = Field(ge=1)
    flow_role: str
    sentences: list[PassageSentence]


class PassageDocument(BaseModel):
    title: str = "업로드 지문"
    paragraphs: list[PassageParagraph] = Field(default_factory=list)
    sentence_count: int = 0
    highlighted_count: int = 0


class VisualGap(BaseModel):
    gap_id: str
    observation_id: str
    timestamp_ms: int
    screen_type: str
    kind: str
    action: GapAction
    safe_to_speak: bool
    public_description: str
    reason: str
    confidence: float
    importance: float
    spoken_overlap: float
    source_text: str | None = None
    hold_notices: list[SafeHoldNotice] = Field(default_factory=list)


class ReviewItem(BaseModel):
    item_id: str
    timestamp_ms: int
    kind: str
    title: str
    description: str


class LessonReview(BaseModel):
    core_summary: list[str] = Field(default_factory=list)
    visual_only_information: list[ReviewItem] = Field(default_factory=list)
    highlighted_sentences: list[ReviewItem] = Field(default_factory=list)
    key_segments: list[ReviewItem] = Field(default_factory=list)


class ConceptEntry(BaseModel):
    concept_id: str = Field(max_length=120)
    keyword: str = Field(max_length=240)
    aliases: list[str] = Field(default_factory=list, max_length=40)
    category: str = Field(default="핵심 개념", max_length=240)
    timestamp_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    lecturer_point: str = Field(default="", max_length=6000)
    ai_explanation: str = Field(default="", max_length=6000)
    flow: str = Field(default="", max_length=4000)
    related_keywords: list[str] = Field(default_factory=list, max_length=40)
    importance: float = Field(default=.8, ge=0, le=1)


class LectureSnapshot(BaseModel):
    analysis_status: AnalysisStatus = Field(default_factory=AnalysisStatus)
    concept_index: list[ConceptEntry] = Field(default_factory=list, max_length=200)
    session: LectureSession
    assets: list[AssetRecord] = Field(default_factory=list)
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    visual_gaps: list[VisualGap] = Field(default_factory=list)
    passage: PassageDocument | None = None
    review: LessonReview
    study_guide: StudyGuide = Field(default_factory=StudyGuide)
    active_mode: Literal["board", "passage", "slides", "mixed", "waiting"] = "waiting"
    safe_description_count: int = 0
    held_count: int = 0

    @model_validator(mode="after")
    def enforce_public_safety(self) -> "LectureSnapshot":
        return sanitize_snapshot_content(self)


def public_text_matches_blocked(value: str | None, forbidden: list[str]) -> bool:
    if not value:
        return False
    def normalized(text: str) -> str:
        text = unicodedata.normalize("NFKC", text).casefold()
        return re.sub(r"\s+", "", text).translate(str.maketrans({"−": "-", "≤": "<", "≥": ">"}))
    target = normalized(value)
    for candidate in forbidden:
        blocked = normalized(candidate)
        if not blocked:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", blocked):
            if re.search(r"(?<![\d.])" + re.escape(blocked) + r"(?![\d.])", target):
                return True
        elif blocked in target:
            return True
    return False


def sanitize_snapshot_content(snapshot: LectureSnapshot, forbidden_texts: list[str] | None = None,
                              confirmed_gap_ids: set[str] | None = None) -> LectureSnapshot:
    """Close loaded snapshots as well as newly built snapshots at one boundary.

    Candidate observations themselves are never part of this model. The agent
    supplies withheld component readings while they are still available inside
    its private analysis state; old snapshots can also carry unsafe gap fields.
    """
    blocked = list(forbidden_texts or [])
    protected_answer = snapshot.session.problem_mode and any(gap.kind == "answer" for gap in snapshot.visual_gaps)
    for gap in snapshot.visual_gaps:
        if (gap.confidence < .72 or not gap.safe_to_speak or gap.action in {GapAction.HOLD, GapAction.SKIP}
                or snapshot.session.problem_mode and gap.kind == "answer"):
            blocked.extend(value for value in (gap.source_text, gap.public_description, gap.reason) if value)
            gap.public_description = ""
            gap.source_text = None
            gap.safe_to_speak = False
            if gap.action != GapAction.SKIP or gap.confidence < .72 or snapshot.session.problem_mode and gap.kind == "answer":
                gap.action = GapAction.HOLD
            safe_reasons = {
                "화면 인식 확신도가 낮아 내용을 전달하지 않습니다.",
                "문제 모드에서는 정답에 해당하는 화면 정보를 대신 제공하지 않습니다.",
                "화면의 내용을 확인하지 못했거나 판독이 서로 달라 설명을 보류합니다.",
                "학습과 관계없는 장식 또는 낮은 중요도 정보입니다.",
                "장면 확인 결과에 따라 화면 내용의 공개를 보류합니다.",
            }
            if gap.reason not in safe_reasons:
                gap.reason = "문제 보호 정책에 따라 정답 화면 정보를 제공하지 않습니다." if snapshot.session.problem_mode and gap.kind == "answer" else "확인되지 않은 화면 내용은 공개하지 않습니다."
        if snapshot.session.problem_mode and gap.kind == "answer":
            gap.hold_notices = []
        elif gap.action==GapAction.HOLD and not gap.hold_notices and gap.kind not in {'answer','decoration'} and gap.importance>=.35:
            gap.hold_notices=[SafeHoldNotice(location='underlined_sentence' if gap.kind=='highlight' else 'whole_board')]
    blocked = list(dict.fromkeys(blocked))
    session_updates = {field: "확인되지 않은 내용 비공개" for field in ("title", "subject", "source_label")
                       if public_text_matches_blocked(getattr(snapshot.session, field), blocked)}
    if session_updates:
        snapshot.session = snapshot.session.model_copy(update=session_updates)
    for asset in snapshot.assets:
        for field in ("name", "note"):
            if public_text_matches_blocked(getattr(asset, field), blocked):
                setattr(asset, field, "확인되지 않은 내용 비공개")
    confirmed = confirmed_gap_ids or set()
    for gap in snapshot.visual_gaps:
        if gap.safe_to_speak and gap.gap_id not in confirmed and any(public_text_matches_blocked(value, blocked) for value in (gap.public_description, gap.source_text, gap.reason)):
            gap.action = GapAction.HOLD
            gap.safe_to_speak = False
            gap.public_description = ""
            gap.source_text = None
            gap.reason = "확인되지 않은 화면 내용이 포함되어 설명을 보류합니다."
    snapshot.transcript_segments = [segment for segment in snapshot.transcript_segments if not public_text_matches_blocked(segment.text, blocked)]
    snapshot.concept_index = [entry for entry in snapshot.concept_index if not public_text_matches_blocked(entry.model_dump_json(), blocked)]
    review = snapshot.review
    review.core_summary = [value for value in review.core_summary if not public_text_matches_blocked(value, blocked)]
    for field in ("visual_only_information", "highlighted_sentences", "key_segments"):
        setattr(review, field, [entry for entry in getattr(review, field)
                               if any(gap.gap_id == entry.item_id and gap.gap_id in confirmed and gap.safe_to_speak
                                      and gap.public_description == entry.description for gap in snapshot.visual_gaps)
                               or not public_text_matches_blocked(entry.model_dump_json(), blocked)])
    if protected_answer or public_text_matches_blocked(snapshot.study_guide.model_dump_json(), blocked):
        snapshot.study_guide = StudyGuide()
    if protected_answer:
        snapshot.passage = None
        snapshot.concept_index = []
    elif snapshot.passage:
        passage = snapshot.passage
        for paragraph in passage.paragraphs:
            paragraph.sentences = [sentence for sentence in paragraph.sentences if not public_text_matches_blocked(sentence.text, blocked)]
        passage.paragraphs = [paragraph for paragraph in passage.paragraphs if paragraph.sentences]
        passage.sentence_count = sum(len(paragraph.sentences) for paragraph in passage.paragraphs)
        passage.highlighted_count = sum(sentence.highlighted for paragraph in passage.paragraphs for sentence in paragraph.sentences)
        if not passage.paragraphs:
            snapshot.passage = None
    snapshot.safe_description_count = sum(gap.safe_to_speak and gap.action in {GapAction.INTERRUPT, GapAction.DESCRIBE_AT_BREAK} for gap in snapshot.visual_gaps)
    snapshot.held_count = sum(gap.action == GapAction.HOLD for gap in snapshot.visual_gaps)
    return snapshot


class VideoFileAnalysisResult(LectureSnapshot):
    """Snapshot plus the outcome of deleting the uploaded video copies."""

    cleanup_status: Literal["deleted", "delete-failed"] = "deleted"
    cleanup_message: str = ""
    remaining_trials: int | None = None


class NavigationRequest(BaseModel):
    command: str = Field(min_length=1, max_length=300)
    current_sentence_id: str | None = Field(default=None, max_length=120)


class NavigationResponse(BaseModel):
    message: str
    sentence_ids: list[str] = Field(default_factory=list)
    timestamp_ms: int | None = None
    current_sentence_id: str | None = None
    safe_to_speak: bool = True


AgentAction = Literal[
    "answer",
    "read_summary",
    "seek",
    "describe_current",
    "replay_paragraph",
    "pause",
]


class AgentTurnInput(BaseModel):
    """One grounded agent turn.

    ``snapshot`` lets the two prebuilt samples use the same agent loop without
    pretending that the server analysed those videos during this run. Raw
    frames or video bytes are never part of this request.
    """

    message: str = Field(min_length=1, max_length=2000)
    current_time_ms: int = Field(default=0, ge=0)
    snapshot: LectureSnapshot | None = None
    analysis_consent: bool = False
    access_code: SecretStr | None = Field(default=None, exclude=True)
    # Ignored by the public server: Gemini keys come only from server variables.
    gemini_api_key: SecretStr | None = Field(default=None, exclude=True)


class AgentTurnResponse(BaseModel):
    provider: Literal["gemini-agent"] = "gemini-agent"
    action: AgentAction
    title: str = Field(min_length=1, max_length=160)
    response_text: str = Field(min_length=1, max_length=12_000)
    decision_reason: str = Field(min_length=1, max_length=1000)
    target_timestamp_ms: int | None = Field(default=None, ge=0)
    paragraph_indices: list[int] = Field(default_factory=list, max_length=20)
    grounding: list[str] = Field(default_factory=list, max_length=12)
    confidence: float = Field(default=0.8, ge=0, le=1)
    safe_to_speak: bool = True
