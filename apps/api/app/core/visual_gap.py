from __future__ import annotations

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

from app.models import (GapAction, SafeHoldNotice, TranscriptSegment, VisualComponent,
                        VisualGap, VisualObservation)


HIGH_RISK_KINDS = {"formula", "number", "condition"}
CONFIRMED = {"confirmed", "corrected"}
UNCERTAIN = {"uncertain", "disagreed", "unverified", "unverified-hold", "rejected"}

_KOREAN_DIGITS = dict(zip("영공일이삼사오육칠팔구", (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9)))
_SPOKEN_VARIABLES = {"엑스": "x", "와이": "y", "제트": "z"}
_KOREAN_NUMBER = r"[영공일이삼사오육칠팔구십백천]+"
_MATH_NUMBER = rf"(?:\d+(?:\.\d+)?|{_KOREAN_NUMBER})"
_MATH_VARIABLE = r"(?:엑스|와이|제트|[xyzXYZ])"
_MATH_OPERAND = rf"[+\-]?\s*(?:{_MATH_NUMBER}\s*{_MATH_VARIABLE}|{_MATH_NUMBER}|{_MATH_VARIABLE})"
_SPOKEN_EXPRESSION = re.compile(
    rf"(?<![가-힣A-Za-z0-9])(?P<expression>{_MATH_OPERAND}"
    rf"(?:\s*(?:<=|>=|!=|[+\-*/=<>^%±]|은|는)\s*{_MATH_OPERAND})+)"
    r"(?:(?P<ending>\s*(?:입니다|이에요|예요|이다))(?![가-힣A-Za-z0-9])|(?=\s*(?:$|[.,!?;:])))"
)


def _korean_integer(text: str) -> str | None:
    """Read unambiguous Sino-Korean integers through 9999; reject guesses."""
    if len(text) == 1 and text in _KOREAN_DIGITS:
        return str(_KOREAN_DIGITS[text])
    if not re.fullmatch(r"(?:[일이삼사오육칠팔구]?천)?(?:[일이삼사오육칠팔구]?백)?"
                        r"(?:[일이삼사오육칠팔구]?십)?[일이삼사오육칠팔구]?", text):
        return None
    total = digit = 0
    for char in text:
        if char in _KOREAN_DIGITS:
            digit = _KOREAN_DIGITS[char]
        else:
            total += (digit or 1) * {"십": 10, "백": 100, "천": 1000}[char]
            digit = 0
    return str(total + digit)


def _normalize_spoken_math(text: str) -> str:
    def replace(match: re.Match) -> str:
        expression = match["expression"]
        # Never convert only the suffix of an unsupported spaced numeral, or
        # truncate an unsupported decimal at its punctuation.
        if re.search(rf"(?<![가-힣A-Za-z0-9])(?:{_KOREAN_NUMBER}|\d+)\s+$", text[:match.start()]):
            return match[0]
        if not match['ending'] and re.match(r"\s*[.,]\s*[0-9영공일이삼사오육칠팔구십백천]", text[match.end():]):
            return match[0]
        # A topic particle alone is not evidence of an equation in ordinary prose.
        if not re.search(r"엑스|와이|제트|[xyzXYZ+\-*/=<>^%±]", expression):
            return match[0]
        for spoken, variable in _SPOKEN_VARIABLES.items():
            expression = expression.replace(spoken, variable)
        numbers = re.findall(_KOREAN_NUMBER, expression)
        if any(_korean_integer(number) is None for number in numbers):
            return match[0]
        expression = re.sub(_KOREAN_NUMBER, lambda number: _korean_integer(number[0]), expression)
        expression = re.sub(r"은|는", "=", expression)
        return re.sub(r"\s+", "", expression)

    return _SPOKEN_EXPRESSION.sub(replace, text)


def normalize_critical_text(text: str) -> str:
    """Normalize notation without erasing distinctions such as < versus <=."""
    text = text.translate(str.maketrans({"−": "-", "–": "-", "×": "*", "÷": "/", "≤": "<=", "≥": ">=", "≠": "!=", "²": "^2", "³": "^3"}))
    text = unicodedata.normalize("NFKC", text)
    for word, symbol in (("이상", ">="), ("이하", "<="), ("초과", ">"), ("미만", "<"),
                         ("더하기", "+"), ("마이너스", "-"), ("빼기", "-"), ("곱하기", "*"), ("나누기", "/")):
        text = text.replace(word, symbol)
    for word, unit in (("킬로미터", "km"), ("센티미터", "cm"), ("밀리미터", "mm"),
                       ("미터", "m"), ("킬로그램", "kg"), ("밀리그램", "mg"), ("그램", "g"),
                       ("켈빈", "K"), ("헤르츠", "Hz"), ("볼트", "V"), ("암페어", "A")):
        text = text.replace(word, unit)
    text = _normalize_spoken_math(text)
    text = re.sub(r"(?<=\d)\s*(?:는|은)\s*(?=[+\-]?\d)", "=", text)
    return re.sub(r"([A-Za-z][A-Za-z0-9]*)\s*(?:는|은)\s*(?=[+\-]?\d)", r"\1=", text)


def critical_signature(text: str) -> tuple[Counter, ...]:
    normalized = normalize_critical_text(text)
    numbers = Counter(re.findall(r"\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?", normalized))
    operators = Counter(re.findall(r"<=|>=|!=|[+\-*/=<>%^±]", normalized))
    units = Counter(re.findall(
        r"(?<![A-Za-z])(?:km/h|m/s(?:\^2)?|km|cm|mm|kg|mg|kHz|MHz|Hz|kPa|MPa|Pa|mL|mol|ms|min|°C|℃|Ω|%|[mgsKhNJVWAL])(?=$|[^A-Za-z])",
        normalized,
    ))
    bindings = Counter((variable.casefold(), operator, number) for variable, operator, number in re.findall(
        r"([A-Za-z][A-Za-z0-9]*)\s*(<=|>=|!=|=|<|>)\s*([+\-]?\d+(?:\.\d+)?)", normalized))
    operand = r'(?:[+\-]?\d+(?:\.\d+)?(?:[A-Za-z][A-Za-z0-9]*)?|[A-Za-z][A-Za-z0-9]*)'
    expressions = Counter(re.sub(r'\s+', '', value).casefold() for value in re.findall(
        rf'{operand}\s*(?:(?:<=|>=|!=|[+\-*/=<>%^])\s*{operand}\s*)+', normalized))
    return numbers, operators, units, bindings, expressions


def critical_signatures_differ(first: str, second: str) -> bool:
    """Different numeric/operator/unit readings are disagreement, not a vote."""
    return critical_signature(first) != critical_signature(second)


def critical_values_communicated(visual_text: str, speech_text: str) -> bool:
    visual = critical_signature(visual_text)
    spoken = critical_signature(speech_text)
    return all(not (required - supplied) for required, supplied in zip(visual, spoken))


def component_is_confirmed(component: VisualComponent, *, problem_mode: bool = False) -> bool:
    return (component.confidence >= .72 and component.verification in CONFIRMED
            and bool(component.text.strip()) and any(value.strip() for value in component.visible_evidence)
            and (component.kind!='highlight' or any(re.sub(r'\s+','',component.text) in re.sub(r'\s+','',value) for value in component.visible_evidence))
            and not (problem_mode and component.kind == "answer"))


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[0-9a-zA-Z가-힣]+|[+\-×÷=<>]", text.casefold()))


def spoken_overlap(visual_text: str, speech_text: str) -> float:
    visual = _tokens(normalize_critical_text(visual_text))
    speech = _tokens(normalize_critical_text(speech_text))
    if not visual:
        return 0.0
    return len(visual & speech) / len(visual)


def nearby_speech(
    segments: list[TranscriptSegment], timestamp_ms: int, window_ms: int = 6000
) -> str:
    return " ".join(
        segment.text
        for segment in segments
        if segment.confidence >= .72 and segment.start_ms - window_ms <= timestamp_ms <= segment.end_ms + window_ms
    )


def current_critical_speech(segments: list[TranscriptSegment], timestamp_ms: int,
                            window_ms: int = 6000) -> str:
    """Do not let an older matching equation conceal the current contradiction."""
    active = [segment for segment in segments if segment.start_ms <= timestamp_ms <= segment.end_ms]
    if active:
        selected = max(active, key=lambda segment: segment.start_ms)
        return selected.text if selected.confidence >= .72 else ""
    nearby = [segment for segment in segments if segment.confidence >= .72
              and segment.start_ms - window_ms <= timestamp_ms <= segment.end_ms + window_ms]
    if not nearby:
        return ""
    selected = min(nearby, key=lambda segment: (min(abs(timestamp_ms - segment.start_ms), abs(timestamp_ms - segment.end_ms)), -segment.start_ms))
    return selected.text


def _speak_math(text: str) -> str:
    replacements = {
        "!=": " 와 같지 않다 ",
        "≠": " 와 같지 않다 ",
        "±": " 플러스 마이너스 ",
        "<=": " 작거나 같다 ",
        ">=": " 크거나 같다 ",
        "≤": " 작거나 같다 ",
        "≥": " 크거나 같다 ",
        "<": " 보다 작다 ",
        ">": " 보다 크다 ",
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
    source = observation.text
    description = observation.annotation or source
    if description != source and (any(critical_signature(source)) or any(critical_signature(description))) and critical_signatures_differ(source, description):
        description = source
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
    notices: list[SafeHoldNotice] = []
    held_components: list[VisualComponent] = []
    if observation.components:
        confirmed = [component for component in observation.components
                     if component_is_confirmed(component, problem_mode=problem_mode)]
        held_components = [component for component in observation.components if component not in confirmed]
        source = " ".join(component.text for component in confirmed)
        # Parent annotations may still repeat an uncertain component. Only the
        # individually verified component readings are public in this path.
        description = source
        if model_verification in CONFIRMED:
            notices = list({component.location: SafeHoldNotice(location='underlined_sentence' if component.kind=='highlight' and component.location=='unknown' else component.location)
                            for component in held_components
                            if not (problem_mode and component.kind == "answer")}.values())
    overlap = spoken_overlap(source, speech)
    critical_gap = not critical_values_communicated(source, current_critical_speech(transcript_segments, observation.timestamp_ms))

    if observation.confidence < 0.72:
        action = GapAction.HOLD
        safe_to_speak = False
        description = ""
        reason = "화면 인식 확신도가 낮아 내용을 전달하지 않습니다."
        notices = [SafeHoldNotice(location=observation.location)]
    elif problem_mode and observation.kind == "answer":
        action = GapAction.HOLD
        safe_to_speak = False
        description = ""
        reason = "문제 모드에서는 정답에 해당하는 화면 정보를 대신 제공하지 않습니다."
        notices = []
    elif model_verification in UNCERTAIN or (observation.components and (not source or model_verification not in CONFIRMED)):
        action = GapAction.HOLD
        safe_to_speak = False
        description = ""
        reason = "화면의 내용을 확인하지 못했거나 판독이 서로 달라 설명을 보류합니다."
        if not notices and not (problem_mode and observation.components and all(c.kind == "answer" for c in observation.components)):
            notices = [SafeHoldNotice(location=observation.location)]
    elif observation.kind == "decoration" or observation.importance < 0.35:
        action = GapAction.SKIP
        safe_to_speak = False
        description = ""
        reason = "학습과 관계없는 장식 또는 낮은 중요도 정보입니다."
        notices = []
    elif model_action_is_verified and recommended_action in {"HOLD", "SKIP"}:
        action = GapAction(recommended_action)
        safe_to_speak = False
        description = ""
        reason = "장면 확인 결과에 따라 화면 내용의 공개를 보류합니다."
        notices = [SafeHoldNotice(location=observation.location)] if action == GapAction.HOLD else []
    elif critical_gap and observation.importance >= .65:
        action = GapAction.INTERRUPT
        reason = "숫자·부호·부등호·단위가 강사 발화와 달라 누락된 화면 정보를 설명합니다."
    elif notices:
        action = GapAction.DESCRIBE_AT_BREAK
        reason = "확인한 부분만 설명하고 불확실한 부분의 보류 안내를 같은 해설에 포함합니다."
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

    change = _change_description(previous_visual_text or "", source)
    if change and (observation.kind in HIGH_RISK_KINDS or any(critical_signature(source))) and critical_gap and safe_to_speak:
        description = f"화면 내용이 바뀌었습니다. {change}되었습니다. 현재 내용은 {_speak_math(source)}입니다."
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
    if safe_to_speak and notices:
        description = " ".join([description, *(notice.text for notice in notices)])
    if problem_mode and (observation.kind == "answer" or observation.components and all(c.kind == "answer" for c in observation.components)):
        notices = []
    if observation.kind=='decoration' or observation.importance<.35:notices=[]

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
        source_text=source if safe_to_speak else None,
        hold_notices=notices,
    )
