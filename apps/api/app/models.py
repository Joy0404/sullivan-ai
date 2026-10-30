from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr


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
    kind: Literal[
        "formula",
        "number",
        "condition",
        "highlight",
        "passage",
        "graph",
        "concept",
        "decoration",
        "answer",
    ] = "concept"
    text: str = Field(default="", max_length=12_000)
    confidence: float = Field(default=0.9, ge=0, le=1)
    importance: float = Field(default=0.7, ge=0, le=1)
    annotation: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GlossaryItem(BaseModel):
    term: str = Field(min_length=1, max_length=120)
    definition: str = Field(min_length=1, max_length=1200)


class StudyGuide(BaseModel):
    overview: str = Field(default="", max_length=6000)
    concept_map: list[str] = Field(default_factory=list, max_length=20)
    glossary: list[GlossaryItem] = Field(default_factory=list, max_length=40)
    recall_questions: list[str] = Field(default_factory=list, max_length=20)


class AnalysisPackageInput(BaseModel):
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


class LectureSnapshot(BaseModel):
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
