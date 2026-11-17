"""Whole-lecture retrieval of complete, public evidence with source times.

No generated embeddings or summarizer are used. Selection never starts with a
prefix slice of the lecture and never truncates an original evidence item.
"""
import re
from dataclasses import dataclass
from typing import Any

from app.models import GapAction, LectureSnapshot, sanitize_snapshot_content


def safe_question_snapshot(snapshot: LectureSnapshot) -> LectureSnapshot:
    return sanitize_snapshot_content(snapshot.model_copy(deep=True))


def blocked_texts(snapshot: LectureSnapshot) -> list[str]:
    return [value for gap in snapshot.visual_gaps
            if (gap.action in {GapAction.HOLD, GapAction.SKIP} or not gap.safe_to_speak
                or gap.confidence < .72 or snapshot.session.problem_mode and gap.kind == "answer")
            for value in (gap.source_text, gap.public_description, gap.reason) if value]


@dataclass(frozen=True)
class EvidenceSelection:
    context: dict[str, Any]
    evidence: tuple[dict[str, Any], ...]
    scope: str

    @property
    def sufficient(self) -> bool:
        return bool(self.evidence)


def select_question_evidence(snapshot: LectureSnapshot, message: str, current_time_ms: int,
                             *, force_global: bool = False) -> EvidenceSelection:
    snapshot = safe_question_snapshot(snapshot)
    docs = []

    def add(kind, text, timestamp=None, **fields):
        if text.strip():
            docs.append({"id": f"e{len(docs)}", "type": kind, "text": text,
                         "timestamp_ms": timestamp, **fields})

    for item in snapshot.transcript_segments:
        if item.confidence >= .72:
            add("speech", item.text, item.start_ms, end_ms=item.end_ms, source_id=item.segment_id)
    for item in snapshot.visual_gaps:
        if (item.safe_to_speak and item.confidence >= .72 and item.action not in {GapAction.HOLD, GapAction.SKIP}
                and not (snapshot.session.problem_mode and item.kind == "answer")):
            add("screen", item.public_description, item.timestamp_ms, source_id=item.gap_id)
    for paragraph in snapshot.passage.paragraphs if snapshot.passage else []:
        text = " ".join(sentence.text for sentence in paragraph.sentences)
        add("passage", text, next((s.timestamp_ms for s in paragraph.sentences if s.timestamp_ms is not None), None),
            paragraph_index=paragraph.paragraph_index,
            sentences=[{"sentence_id": s.sentence_id, "text": s.text, "timestamp_ms": s.timestamp_ms}
                       for s in paragraph.sentences])
    for item in snapshot.review.key_segments:
        add("review", item.description, item.timestamp_ms)
    for text in snapshot.review.core_summary:
        add("summary", text)
    add("guide", snapshot.study_guide.overview)
    for text in snapshot.study_guide.concept_map:
        add("guide", text)
    for item in snapshot.study_guide.glossary:
        add("guide", f"{item.term}: {item.definition}")

    query = message.casefold()
    tokens = [t for t in re.findall(r"[\w]+", query) if len(t) >= 2 and t not in {
        "지금", "현재", "화면", "판서", "여기", "설명", "설명해", "설명해줘", "알려줘", "무엇", "어떤", "강의", "내용", "질문",
        "후반", "후반부", "마지막", "처음", "이전", "비교", "차이", "전체", "각각", "여러", "다시"}]
    # Match Korean topic particles without rewriting the original evidence.
    tokens = [re.sub(r"(?:에서는|에서|은|는|을|를|의|이|가|에|와|과)$", "", t) for t in tokens]
    tokens = [t for t in tokens if len(t) >= 2]
    anchors = [int(m[0]) * 60000 + int(m[1]) * 1000 for m in re.findall(r"(\d{1,3}):(\d{2})", query)]
    anchors += [int(m[0]) * 60000 + int(m[1] or 0) * 1000 for m in re.findall(r"(\d+)\s*분(?:\s*(\d+)\s*초)?", query)]
    global_intent = bool(anchors or re.search(r"후반|마지막|처음|이전|앞에서|비교|차이|전체|각각|여러", query))
    current_intent = bool(re.search(r"지금|현재|이 화면|이 판서|여기", query)) and not global_intent

    def score(doc):
        text = doc["text"].casefold()
        return sum(1 for token in tokens if token in text)

    scores = {doc["id"]: score(doc) for doc in docs}
    selected, scope = [], "insufficient"
    if not global_intent and not force_global:
        for window in (30000, 120000):
            nearby = [doc for doc in docs if doc["timestamp_ms"] is not None
                      and abs(doc["timestamp_ms"] - current_time_ms) <= window
                      and doc["type"] in {"screen", "speech", "passage"}]
            relevant = [doc for doc in nearby if scores[doc["id"]] > 0]
            if relevant or current_intent and nearby:
                # Include both modalities around relevant/current screens.
                selected, scope = nearby, f"nearby-{window}"
                break
    if not selected:
        ranked = sorted([doc for doc in docs if scores[doc["id"]] > 0],
                        key=lambda doc: (-scores[doc["id"]], doc["timestamp_ms"] or 0))
        selected, scope = ranked, "lecture-search"
        if anchors:
            temporal = [doc for doc in docs if doc["timestamp_ms"] is not None
                        and any(abs(doc["timestamp_ms"] - anchor) <= 30000 for anchor in anchors)]
            # Each requested time must have actual, public source evidence.
            if not all(any(abs(doc["timestamp_ms"] - a) <= 30000 for doc in temporal) for a in anchors):
                selected = []
            else:
                selected = temporal + [doc for doc in ranked if doc not in temporal]
        elif not tokens and re.search(r"전체|요약|흐름", query):
            selected = [doc for doc in docs if doc["type"] in {"summary", "guide"}]
        elif force_global and not tokens:
            selected = docs
    # A multi-range request must not lose a requested range to a size cap.
    # Refuse oversized selections instead of slicing text or hiding omissions.
    if len(selected) > 32 or sum(len(doc["text"]) for doc in selected) > 24000:
        if global_intent or current_intent:
            selected, scope = [], "evidence-budget-insufficient"
        else:
            selected = sorted(selected, key=lambda d: (-scores[d["id"]], abs((d["timestamp_ms"] or 0) - current_time_ms)))[:16]
            if sum(len(d["text"]) for d in selected) > 24000:
                selected, scope = [], "evidence-budget-insufficient"
    context = {"lecture": {"title": snapshot.session.title, "subject": snapshot.session.subject,
                           "problem_mode": snapshot.session.problem_mode}, "scope": scope, "evidence": selected}
    return EvidenceSelection(context, tuple(selected), scope)
