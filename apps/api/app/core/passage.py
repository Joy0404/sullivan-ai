from __future__ import annotations

import re
from collections.abc import Iterable

from app.models import (
    NavigationResponse,
    PassageDocument,
    PassageParagraph,
    PassageSentence,
)


def _normalize(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", text).casefold()


def _split_sentences(paragraph: str) -> list[str]:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    candidates: list[str] = []
    for line in lines or [paragraph.strip()]:
        parts = re.split(r"(?<=[.!?。！？])\s+", line)
        candidates.extend(part.strip() for part in parts if part.strip())
    return candidates


def _flow_role(text: str, index: int, total: int) -> str:
    normalized = text.replace(" ", "")
    if any(word in normalized for word in ("그러나", "하지만", "반면", "반대로")):
        return "반론·대조"
    if any(word in normalized for word in ("따라서", "결론", "그러므로", "요컨대")):
        return "필자의 결론"
    if index == 1:
        return "문제 제기"
    if index == total:
        return "정리"
    return "주장 전개"


def _is_highlighted(text: str, highlighted_texts: Iterable[str]) -> bool:
    target = _normalize(text)
    if not target:
        return False
    for highlight in highlighted_texts:
        candidate = _normalize(highlight)
        if candidate and (candidate in target or target in candidate):
            return True
    return False


def _timestamp_for(text: str, timestamp_hints: Iterable[tuple[str, int]]) -> int | None:
    target = _normalize(text)
    best: tuple[float, int] | None = None
    target_tokens = set(re.findall(r"[0-9a-zA-Z가-힣]+", text.casefold()))
    for hint_text, timestamp_ms in timestamp_hints:
        hint = _normalize(hint_text)
        if hint and (hint in target or target in hint):
            return timestamp_ms
        hint_tokens = set(re.findall(r"[0-9a-zA-Z가-힣]+", hint_text.casefold()))
        union = target_tokens | hint_tokens
        score = len(target_tokens & hint_tokens) / len(union) if union else 0.0
        if best is None or score > best[0]:
            best = (score, timestamp_ms)
    return best[1] if best and best[0] >= 0.35 else None


def structure_passage(
    text: str,
    highlighted_texts: Iterable[str] = (),
    timestamp_hints: Iterable[tuple[str, int]] = (),
    *,
    title: str = "업로드 지문",
) -> PassageDocument:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return PassageDocument(title=title)

    raw_paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", cleaned) if part.strip()]
    if len(raw_paragraphs) == 1 and cleaned.count("\n") >= 2:
        raw_paragraphs = [line.strip() for line in cleaned.splitlines() if line.strip()]

    paragraphs: list[PassageParagraph] = []
    sentence_count = 0
    highlighted_count = 0
    total = len(raw_paragraphs)
    hints = list(timestamp_hints)
    highlights = list(highlighted_texts)

    for paragraph_index, raw in enumerate(raw_paragraphs, start=1):
        sentences: list[PassageSentence] = []
        for sentence_index, sentence_text in enumerate(_split_sentences(raw), start=1):
            highlighted = _is_highlighted(sentence_text, highlights)
            if highlighted:
                highlighted_count += 1
            sentence_count += 1
            sentences.append(
                PassageSentence(
                    sentence_id=f"p{paragraph_index}-s{sentence_index}",
                    paragraph_index=paragraph_index,
                    sentence_index=sentence_index,
                    text=sentence_text,
                    timestamp_ms=_timestamp_for(sentence_text, hints),
                    highlighted=highlighted,
                )
            )
        paragraphs.append(
            PassageParagraph(
                paragraph_id=f"p{paragraph_index}",
                paragraph_index=paragraph_index,
                flow_role=_flow_role(raw, paragraph_index, total),
                sentences=sentences,
            )
        )

    return PassageDocument(
        title=title,
        paragraphs=paragraphs,
        sentence_count=sentence_count,
        highlighted_count=highlighted_count,
    )


def navigate_passage(
    document: PassageDocument | None,
    command: str,
    current_sentence_id: str | None = None,
) -> NavigationResponse:
    if document is None or not document.paragraphs:
        return NavigationResponse(
            message="탐색할 지문이 아직 없습니다. 지문 자료를 먼저 분석해 주세요.",
            safe_to_speak=True,
        )

    sentences = [sentence for paragraph in document.paragraphs for sentence in paragraph.sentences]
    by_id = {sentence.sentence_id: sentence for sentence in sentences}
    current_index = next(
        (index for index, item in enumerate(sentences) if item.sentence_id == current_sentence_id),
        0,
    )
    normalized = command.strip().casefold()

    def response(items: list[PassageSentence], prefix: str) -> NavigationResponse:
        if not items:
            return NavigationResponse(message="해당하는 문장을 찾지 못했습니다.")
        first = items[0]
        location = f"{first.paragraph_index}문단 {first.sentence_index}번째 문장"
        combined = " ".join(item.text for item in items)
        return NavigationResponse(
            message=f"{prefix} {location}. {combined}",
            sentence_ids=[item.sentence_id for item in items],
            timestamp_ms=first.timestamp_ms,
            current_sentence_id=first.sentence_id,
        )

    if "밑줄" in normalized or "강조" in normalized:
        highlighted = [item for item in sentences if item.highlighted]
        if "만" in normalized:
            return response(highlighted, "강사가 강조한 문장입니다.")
        nearest = next((item for item in highlighted if sentences.index(item) >= current_index), None)
        return response([nearest] if nearest else highlighted[:1], "강사가 강조한 문장입니다.")

    if "앞뒤" in normalized or "두 문장 같이" in normalized:
        start = max(0, current_index - 1)
        end = min(len(sentences), current_index + 2)
        return response(sentences[start:end], "현재 위치의 앞뒤 문장입니다.")

    if "앞 문장" in normalized or "이전 문장" in normalized:
        target = sentences[max(0, current_index - 1)]
        return response([target], "앞 문장입니다.")

    if "다음 문장" in normalized:
        target = sentences[min(len(sentences) - 1, current_index + 1)]
        return response([target], "다음 문장입니다.")

    paragraph_match = re.search(r"(\d+)\s*문단", normalized)
    if paragraph_match:
        paragraph_index = int(paragraph_match.group(1))
        paragraph = next(
            (item for item in document.paragraphs if item.paragraph_index == paragraph_index),
            None,
        )
        return response(paragraph.sentences if paragraph else [], f"{paragraph_index}문단입니다.")

    for paragraph in document.paragraphs:
        if paragraph.flow_role in normalized or (
            "반론" in normalized and "반론" in paragraph.flow_role
        ) or ("결론" in normalized and "결론" in paragraph.flow_role):
            return response(paragraph.sentences, f"{paragraph.flow_role} 부분입니다.")

    if "현재 문단" in normalized or "이 문단" in normalized:
        current = by_id.get(current_sentence_id or "", sentences[current_index])
        paragraph = document.paragraphs[current.paragraph_index - 1]
        return response(paragraph.sentences, "현재 문단입니다.")

    search_match = re.search(r"[‘'\"]?(.+?)[’'\"]?\s*(?:이라는|라는|이|가)?\s*단어", normalized)
    if search_match:
        keyword = search_match.group(1).strip(" ‘’'\"")
        matches = [item for item in sentences if keyword and keyword in item.text.casefold()]
        return response(matches[:3], f"'{keyword}'이 들어간 문장입니다.")

    return response([sentences[current_index]], "현재 문장입니다.")

