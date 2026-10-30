from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.models import GapAction, TranscriptSegment, VisualGap, VisualObservation


HIGH_RISK_KINDS = {"formula", "number", "condition"}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[0-9a-zA-Z가-힣]+|[+\-×÷=<>]", text.casefold()))


def spoken_overlap(visual_text: str, speech_text: str) -> float:
    visual = _tokens(visual_text)
    speech = _tokens(speech_text)
    if not visual:
        return 0.0
    return len(visual & speech) / len(visual)


def nearby_speech(
    segments: list[TranscriptSegment], timestamp_ms: int, window_ms: int = 6000
) -> str:
    return " ".join(
        segment.text
        for segment in segments
        if segment.start_ms - window_ms <= timestamp_ms <= segment.end_ms + window_ms
    )


def _speak_math(text: str) -> str:
    replacements = {
        "=": " 는 ",
        "+": " 더하기 ",
        "-": " 마이너스 ",
        "×": " 곱하기 ",
        "*": " 곱하기 ",
        "/": " 나누기 ",
    }
    result = text
    for symbol, spoken in replacements.items():
        result = result.replace(symbol, spoken)
    return re.sub(r"\s+", " ", result).strip()


def _change_description(before: str, after: str) -> str | None:
    if not before or before == after:
        return None
    matcher = SequenceMatcher(a=before, b=after)
    changes: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            changes.append(f"'{before[i1:i2]}'이 '{after[j1:j2]}'으로 수정")
        elif tag == "insert":
            changes.append(f"'{after[j1:j2]}'이 추가")
        elif tag == "delete":
            changes.append(f"'{before[i1:i2]}'이 삭제")
    return ", ".join(changes[:2]) if changes else None


def analyze_visual_observation(
    observation: VisualObservation,
    transcript_segments: list[TranscriptSegment],
    previous_visual_text: str | None = None,
    *,
    problem_mode: bool = False,
) -> VisualGap:
    speech = nearby_speech(transcript_segments, observation.timestamp_ms)
    overlap = spoken_overlap(observation.text, speech)
    description = observation.annotation or observation.text
    reason = "화면 정보와 강사 발화를 비교했습니다."
    action = GapAction.INDEX_ONLY
    safe_to_speak = True
    model_verification = str(observation.metadata.get("verification", "")).lower()
    recommended_action = str(observation.metadata.get("recommended_action", "")).upper()
    model_reason = str(observation.metadata.get("decision_reason", "")).strip()
    model_action_is_verified = (
        model_verification in {"confirmed", "corrected"}
        and recommended_action in {item.value for item in GapAction}
    )

    if observation.confidence < 0.72:
        action = GapAction.HOLD
        safe_to_speak = False
        description = ""
        reason = "화면 인식 확신도가 낮아 내용을 전달하지 않습니다."
    elif problem_mode and observation.kind == "answer":
        action = GapAction.HOLD
        safe_to_speak = False
        description = ""
        reason = "문제 모드에서는 정답에 해당하는 화면 정보를 대신 제공하지 않습니다."
    elif observation.kind == "decoration" or observation.importance < 0.35:
        action = GapAction.SKIP
        safe_to_speak = False
        description = ""
        reason = "학습과 관계없는 장식 또는 낮은 중요도 정보입니다."
    elif model_action_is_verified and recommended_action in {"HOLD", "SKIP"}:
        action = GapAction(recommended_action)
        safe_to_speak = False
        description = ""
        reason = model_reason or "Gemini의 독립 장면 검증에서 자동 해설 대상이 아닌 것으로 판단했습니다."
    elif overlap >= 0.72:
        action = GapAction.INDEX_ONLY
        reason = "강사가 이미 같은 내용을 충분히 말해 자동 해설하지 않습니다."
    elif model_action_is_verified:
        action = GapAction(recommended_action)
        reason = model_reason or "Gemini가 화면 근거와 앞뒤 발화를 함께 보고 개입 시점을 선택했습니다."
    elif observation.kind in HIGH_RISK_KINDS and observation.importance >= 0.65:
        action = GapAction.INTERRUPT
        reason = "숫자·조건·수식이 음성으로 충분히 전달되지 않아 즉시 설명합니다."
    elif observation.kind == "highlight":
        action = GapAction.INTERRUPT if observation.importance >= 0.75 else GapAction.DESCRIBE_AT_BREAK
        reason = "강사의 시각적 강조가 음성으로 특정되지 않았습니다."
    elif observation.importance >= 0.78:
        action = GapAction.DESCRIBE_AT_BREAK
        reason = "중요한 시각정보를 다음 자연스러운 구간에서 설명합니다."
    else:
        action = GapAction.INDEX_ONLY
        reason = "복습 인덱스에는 남기되 재생을 방해하지 않습니다."

    change = _change_description(previous_visual_text or "", observation.text)
    if change and observation.kind in HIGH_RISK_KINDS and overlap < 0.72 and safe_to_speak:
        description = f"화면 내용이 바뀌었습니다. {change}되었습니다. 현재 내용은 {_speak_math(observation.text)}입니다."
        action = GapAction.INTERRUPT
        reason = "중요 판서의 숫자 또는 부호 변경을 감지했습니다."
    elif safe_to_speak and description:
        if observation.kind == "formula":
            description = f"새로운 식이 화면에 추가되었습니다. {_speak_math(description)}입니다."
        elif observation.kind == "highlight":
            description = f"강사가 다음 문장을 강조했습니다. {description}"
        elif observation.kind == "graph":
            description = f"화면에 그래프가 표시되었습니다. {description}"
        elif observation.kind == "condition":
            description = f"문제 조건이 화면에 제시되었습니다. {description}"

    return VisualGap(
        gap_id=f"gap-{observation.observation_id}",
        observation_id=observation.observation_id,
        timestamp_ms=observation.timestamp_ms,
        screen_type=observation.screen_type,
        kind=observation.kind,
        action=action,
        safe_to_speak=safe_to_speak,
        public_description=description if safe_to_speak else "",
        reason=reason,
        confidence=observation.confidence,
        importance=observation.importance,
        spoken_overlap=round(overlap, 3),
        source_text=observation.text if safe_to_speak else None,
    )
