"""Synthetic provider fixtures verify boundaries; these are not live token savings."""
import asyncio
import json

import httpx
import pytest

from app.adapters import gemini_agent, video_link
from app.adapters.usage_metrics import capture_usage
from app.core.lecture_agent import LectureAgent
from app.core.question_evidence import select_question_evidence
from app.core.token_optimization import current_route, experimental_route
from app.core.verification_plan import (blind_verification_prompt, merge_blind_readings,
                                        merge_intervals, plan_verification)
from app.models import AnalysisPackageInput, LectureCreate, TranscriptSegment, VisualObservation, VisualComponent


def draft(text="x < 7", *, kind="condition", timestamp=10000, spoken=False, broad=False):
    metadata = {"verification": "confirmed", "visible_evidence": [text], "recommended_action": "INTERRUPT"}
    if broad:
        metadata.update(scene_start_ms=5000, scene_end_ms=45000)
    return AnalysisPackageInput(
        transcript_segments=[TranscriptSegment(segment_id="s0", start_ms=9000, end_ms=11000, text=text, confidence=.99)] if spoken else [],
        visual_observations=[VisualObservation(observation_id="opaque-candidate", timestamp_ms=timestamp,
            kind=kind, screen_type="passage" if kind in {"passage", "highlight"} else "board",
            text=text, confidence=.99, importance=.99, metadata=metadata,
            components=[VisualComponent(component_id="original-part", text=text, kind=kind,
                confidence=.99, verification="confirmed", visible_evidence=[text])])])


def blind(package):
    return {"readings": [{"id": f"v{i}", "timestamp_ms": obs.timestamp_ms,
                          "observed_timestamp_ms": obs.timestamp_ms, "status": "confirmed",
                          "visible_evidence": obs.metadata["visible_evidence"],
                          "parts": [{**part.model_dump(mode="json"), "id": f"p{j}"}
                                    for j, part in enumerate(obs.components)], "corrections": []}
                         for i, obs in enumerate(package.visual_observations)],
            "material_status": {key: "confirmed" for key in
                                ("transcript_segments", "passage_text", "highlighted_texts", "study_guide")}}


def snapshot(package, *, problem=False):
    agent = LectureAgent()
    session = agent.create_session(LectureCreate(title="검사 강의", problem_mode=problem))
    return agent.analyze(session.session_id, package)


def mock_client(monkeypatch, module, provider):
    original = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(provider), **kwargs))


def response(value, total=100):
    text = value.model_dump_json() if isinstance(value, AnalysisPackageInput) else json.dumps(value, ensure_ascii=False)
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}],
                                    "usageMetadata": {"promptTokenCount": total - 20, "candidatesTokenCount": 20,
                                                      "totalTokenCount": total}})


def analyze():
    return asyncio.run(video_link._analyze_gemini_video_source("https://fixture.example/owned.mp4",
        mime_type="video/mp4", title="비교", subject="수학", problem_mode=False, api_key="test-key"))


def test_default_remains_baseline_and_route_is_task_local():
    assert current_route() == "baseline"
    with experimental_route():
        assert current_route() == "experimental"
    assert current_route() == "baseline"


def test_short_board_padding_merges_and_long_scene_expands():
    package = draft()
    package.visual_observations.append(package.visual_observations[0].model_copy(update={"observation_id": "b", "timestamp_ms": 18000}))
    assert plan_verification(package, problem_mode=False).intervals == ((5000, 23000),)
    long = draft("긴 지문", kind="passage", broad=True)
    assert plan_verification(long, problem_mode=False).intervals == ((5000, 45000),)
    assert merge_intervals([(10, 20), (0, 10), (30, 40)]) == ((0, 20), (30, 40))


@pytest.mark.parametrize("change", ["passage", "speech", "hold", "answer", "unbounded"])
def test_insufficient_or_protected_coverage_uses_full_critic(change):
    package = draft()
    problem = change == "answer"
    if change == "passage": package.passage_text = "범위 밖의 긴 지문"
    if change == "speech": package.transcript_segments = [TranscriptSegment(segment_id="later", start_ms=90000, end_ms=95000, text="후반 발화")]
    if change == "hold": package.visual_observations[0].confidence = .71
    if change == "answer": package.visual_observations[0].kind = "answer"
    if change == "unbounded": package.visual_observations[0].kind = "passage"
    assert plan_verification(package, problem_mode=problem).fallback_reason


def test_actual_wire_clips_and_does_not_send_first_reading(monkeypatch):
    package = draft("FIRST_READING_PRIVATE")
    wire = []
    def provider(request):
        wire.append(json.loads(request.content))
        return response(package if len(wire) == 1 else blind(package))
    mock_client(monkeypatch, video_link, provider)
    with capture_usage() as records, experimental_route():
        result = analyze()
    assert len(wire) == 2
    first = wire[0]["contents"][0]["parts"]
    second = wire[1]["contents"][0]["parts"]
    assert "videoMetadata" not in first[0]
    assert second[0]["videoMetadata"] == {"startOffset": "5s", "endOffset": "15s"}
    assert "FIRST_READING_PRIVATE" not in second[-1]["text"]
    assert result.visual_observations[0].timestamp_ms == 10000
    assert [r["stage"] for r in records] == ["analysis", "verification"]
    assert all(r["route"] == "experimental" for r in records)


@pytest.mark.parametrize("failure", ["unsupported", "material-omitted"])
def test_clip_failure_retries_full_video_and_records_all_tokens(monkeypatch, failure):
    package = draft()
    if failure == "material-omitted":
        package.study_guide.overview = "검증할 요약"
    calls = []
    def provider(request):
        body = json.loads(request.content); calls.append(body)
        if len(calls) == 2:
            return httpx.Response(400, json={"error": {"message": "unsupported"}}) if failure == "unsupported" else response(blind(package))
        if len(calls) == 3 and failure == "material-omitted":
            return response({"confidence": .99})
        return response(package)
    mock_client(monkeypatch, video_link, provider)
    with capture_usage() as records, experimental_route(): analyze()
    assert len(calls) == (3 if failure == "unsupported" else 4)
    assert "videoMetadata" not in calls[-1]["contents"][0]["parts"][0]
    failed = records[1 if failure == "unsupported" else 2]
    assert failed["success"] is False
    assert records[-1]["retry"] and records[-1]["attempt"] == (2 if failure == "unsupported" else 3)
    if failure == "material-omitted":
        assert records[2]["attempt"] == 2 and not records[2]["retry"]
    assert failed["measurement"] == ("미측정" if failure == "unsupported" else "measured")


def test_long_passage_blind_read_is_independent_then_text_audit_preserves_every_sentence(monkeypatch):
    passage = " ".join(f"직접 확인한 지문의 {i}번째 문장입니다." for i in range(1, 201))
    package = draft(passage, kind="passage", broad=True)
    package.passage_text = passage
    highlight = draft("직접 확인한 지문의 199번째 문장입니다.", kind="highlight", broad=True).visual_observations[0]
    highlight.observation_id = "underline"
    package.visual_observations.append(highlight)
    package.highlighted_texts = [highlight.text]
    package.study_guide.overview = "검증된 지문의 문장과 강조 부분을 되짚습니다."
    wire = []
    def provider(request):
        wire.append(json.loads(request.content))
        return response(package if len(wire) == 1 else blind(package) if len(wire) == 2
                        else {"confidence": .99, "material_status": blind(package)["material_status"]})
    mock_client(monkeypatch, video_link, provider)
    with capture_usage() as records, experimental_route():
        verified = analyze()
    assert len(wire) == 3
    assert passage not in wire[1]["contents"][0]["parts"][-1]["text"]
    assert "199번째" not in wire[1]["contents"][0]["parts"][-1]["text"]
    assert len(wire[2]["contents"][0]["parts"]) == 1
    assert "file_data" not in wire[2]["contents"][0]["parts"][0]
    assert passage in wire[2]["contents"][0]["parts"][0]["text"]
    assert verified.passage_text == passage and verified.highlighted_texts == [highlight.text]
    assert verified.study_guide.overview == package.study_guide.overview
    assert [r["stage"] for r in records] == ["analysis", "verification", "verification"]
    assert [r["attempt"] for r in records] == [1, 1, 2]
    assert not any(r["retry"] for r in records)
    assert len({r["operation_id"] for r in records}) == 1
    assert sum(r["total_tokens"] for r in records) == 300  # synthetic counters only


@pytest.mark.parametrize("case,first,second,kind,spoken,confidence", [
    ("small-inequality", "x < 7", "x ≤ 7", "condition", False, .99),
    ("axis-unit", "7 m", "7 cm", "number", False, .99),
    ("long-passage-underline", "이 문장은 원인입니다.", "이 문장은 원인입니다.", "highlight", False, .99),
    ("already-spoken", "질량은 7 kg입니다.", "질량은 7 kg입니다.", "number", True, .99),
    ("blur", "BLURRED_SECRET", "BLURRED_SECRET", "concept", False, .71),
    ("answer", "ANSWER_SECRET", "ANSWER_SECRET", "answer", False, .99),
])
def test_fixture_quality_parity_and_zero_held_answer_leaks(case, first, second, kind, spoken, confidence):
    original = draft(first, kind=kind, spoken=spoken, broad=True)
    reread = draft(second, kind=kind, spoken=spoken, broad=True)
    reread.visual_observations[0].components[0].confidence = confidence
    expected = video_link._enforce_model_visual_verification(reread, original)
    plan = plan_verification(original, problem_mode=False)
    actual = video_link._enforce_model_visual_verification(merge_blind_readings(original, plan, blind(reread)), original)
    a, b = snapshot(expected, problem=kind == "answer"), snapshot(actual, problem=kind == "answer")
    assert [gap.action for gap in a.visual_gaps] == [gap.action for gap in b.visual_gaps]
    assert [gap.timestamp_ms for gap in a.visual_gaps] == [gap.timestamp_ms for gap in b.visual_gaps]
    assert a.safe_description_count == b.safe_description_count
    if first != second or confidence < .72 or kind == "answer":
        assert first not in b.model_dump_json() and second not in b.model_dump_json()
    else:
        assert second in b.model_dump_json()
    if spoken: assert b.visual_gaps[0].action.value == "INDEX_ONLY"


@pytest.mark.parametrize("defect", ["missing", "time", "status", "component", "component-evidence"])
def test_incomplete_rereading_holds_and_removes_dependent_material(defect):
    package = draft("PRIVATE_CANDIDATE")
    package.study_guide.overview = "PRIVATE_CANDIDATE 해설"
    raw = blind(package)
    if defect == "missing": raw["readings"] = []
    if defect == "time": raw["readings"][0]["observed_timestamp_ms"] = 0
    if defect == "status": raw["readings"][0]["status"] = "uncertain"
    if defect == "component": raw["readings"][0]["parts"] = []
    if defect == "component-evidence": raw["readings"][0]["parts"][0]["visible_evidence"] = []
    package.passage_text = "후보 해설에서 도출한 별도 표현의 지문"
    package.highlighted_texts = ["지문에서 강조한 부분"]
    merged = merge_blind_readings(package, plan_verification(package, problem_mode=False), raw)
    assert merged.passage_text is None and not merged.study_guide.overview and not merged.highlighted_texts
    safe = snapshot(video_link._enforce_model_visual_verification(merged, package))
    assert "PRIVATE_CANDIDATE" not in safe.model_dump_json()
    assert safe.visual_gaps[0].safe_to_speak is False


def lecture_with_late_evidence():
    package = draft("지금 화면의 세로축은 시간입니다.", timestamp=10000)
    package.transcript_segments = [TranscriptSegment(segment_id=f"s{i}", start_ms=i*10000, end_ms=i*10000+5000,
        text="앞부분의 별도 설명입니다.", confidence=.99) for i in range(200)]
    package.transcript_segments.append(TranscriptSegment(segment_id="late", start_ms=3600000, end_ms=3605000,
        text="엔트로피는 후반부에 정의합니다.", confidence=.99))
    return snapshot(package)


def test_late_question_searches_whole_lecture_preserving_original_time():
    selected = select_question_evidence(lecture_with_late_evidence(), "후반부 엔트로피 설명해줘", 10000)
    assert selected.sufficient and selected.scope == "lecture-search"
    assert any(e["text"] == "엔트로피는 후반부에 정의합니다." and e["timestamp_ms"] == 3600000 for e in selected.evidence)
    assert not any(e["text"] == "앞부분의 별도 설명입니다." for e in selected.evidence)


def test_current_screen_prioritizes_nearby_verified_visual_and_speech():
    selected = select_question_evidence(lecture_with_late_evidence(), "지금 화면 설명해줘", 10000)
    assert selected.scope == "nearby-30000"
    assert {e["type"] for e in selected.evidence} >= {"screen", "speech"}
    assert all(e["timestamp_ms"] <= 40000 for e in selected.evidence)


def test_multi_time_questions_keep_both_original_ranges():
    selected = select_question_evidence(lecture_with_late_evidence(), "00:10과 60:00 비교", 0)
    assert selected.sufficient
    assert {10000, 3600000} <= {e["timestamp_ms"] for e in selected.evidence}
    assert not select_question_evidence(lecture_with_late_evidence(), "99:00 비교", 0).sufficient


def test_question_input_output_block_held_text_even_in_mutated_snapshot(monkeypatch):
    value = lecture_with_late_evidence()
    gap = value.visual_gaps[0]
    gap.action = "HOLD"; gap.safe_to_speak = True; gap.source_text = "PRIVATE_HELD_VALUE"; gap.public_description = "PRIVATE_HELD_VALUE"
    value.study_guide.overview = "PRIVATE_HELD_VALUE"
    assert "PRIVATE_HELD_VALUE" not in json.dumps(gemini_agent.build_grounded_context(value), ensure_ascii=False)
    assert "PRIVATE_HELD_VALUE" not in json.dumps(select_question_evidence(value, "지금 화면", 10000).context, ensure_ascii=False)
    raw = {"action": "answer", "title": "응답", "response_text": "PRIVATE_HELD_VALUE", "decision_reason": "근거", "grounding": ["PRIVATE_HELD_VALUE"], "confidence": .99}
    safe = gemini_agent.sanitize_agent_result(raw, snapshot=value, message="설명")
    assert not safe.safe_to_speak and "PRIVATE_HELD_VALUE" not in safe.model_dump_json()
    def no_call(*args, **kwargs): raise AssertionError("must not call provider")
    monkeypatch.setattr(gemini_agent, "metered_post", no_call)
    assert not asyncio.run(gemini_agent.run_agent_turn(value, message="PRIVATE_HELD_VALUE 설명", current_time_ms=0, api_key_override="test")).safe_to_speak


def test_question_widens_on_model_insufficiency_with_measured_retry(monkeypatch):
    value = lecture_with_late_evidence()
    calls = []
    def provider(request):
        prompt = json.loads(request.content)["contents"][0]["parts"][0]["text"]
        calls.append(prompt)
        if len(calls) == 1:
            return response({"action": "pause", "title": "부족", "response_text": "근거 부족", "decision_reason": "부족", "grounding": [], "confidence": .1})
        context = json.loads(prompt.split("강의 근거:\n", 1)[1].split("\nevidence_ids", 1)[0])
        source = next(e for e in context["evidence"] if "엔트로피" in e["text"])
        return response({"action": "answer", "title": "후반부", "response_text": source["text"], "decision_reason": "원문 확인",
                         "grounding": [source["text"]], "evidence_ids": [source["id"]], "confidence": .99})
    mock_client(monkeypatch, gemini_agent, provider)
    with experimental_route(), capture_usage() as records:
        result = asyncio.run(gemini_agent.run_agent_turn(value, message="지금 엔트로피 설명해줘", current_time_ms=10000, api_key_override="test"))
    assert len(calls) == 2 and "엔트로피는 후반부" not in calls[0] and "엔트로피는 후반부" in calls[1]
    assert result.safe_to_speak and "후반부" in result.response_text
    assert records[1]["retry"] and records[1]["operation_id"] == records[0]["operation_id"]


def test_unrelated_question_and_problem_answer_never_call_provider(monkeypatch):
    def no_call(*args, **kwargs): raise AssertionError("must not call provider")
    monkeypatch.setattr(gemini_agent, "metered_post", no_call)
    with experimental_route():
        held = asyncio.run(gemini_agent.run_agent_turn(lecture_with_late_evidence(), message="외계행성의 대기 조성", current_time_ms=0, api_key_override="test"))
        protected = asyncio.run(gemini_agent.run_agent_turn(snapshot(draft("ANSWER_SECRET", kind="answer"), problem=True), message="정답만 알려줘", current_time_ms=0, api_key_override="test"))
    assert not held.safe_to_speak
    assert "ANSWER_SECRET" not in protected.model_dump_json()


@pytest.mark.parametrize("defect", ["unknown-id", "invented-quote", "wrong-time", "wrong-paragraph"])
def test_question_cannot_execute_unselected_or_invented_grounding(monkeypatch, defect):
    value = lecture_with_late_evidence()
    source = next(e for e in select_question_evidence(value, "후반부 엔트로피 설명해줘", 0).evidence if e["type"] == "speech")
    raw = {"action": "answer", "title": "응답", "response_text": "확인한 근거", "decision_reason": "원문",
           "grounding": [source["text"]], "evidence_ids": [source["id"]], "confidence": .99}
    if defect == "unknown-id": raw["evidence_ids"] = ["not-selected"]
    if defect == "invented-quote": raw["grounding"] = ["강의에 없는 추측"]
    if defect == "wrong-time": raw["target_timestamp_ms"] = 12345
    if defect == "wrong-paragraph": raw["paragraph_indices"] = [99]
    mock_client(monkeypatch, gemini_agent, lambda request: response(raw))
    with experimental_route():
        result = asyncio.run(gemini_agent.run_agent_turn(value, message="후반부 엔트로피 설명해줘", current_time_ms=0, api_key_override="test"))
    assert not result.safe_to_speak and result.grounding == []


@pytest.mark.parametrize("defect", [None, "missing", "time", "uncertain", "duplicate"])
def test_material_audit_requires_fresh_speech_and_falls_back_on_missing_coverage(monkeypatch, defect):
    package = draft("PRIVATE_FIRST_TRANSCRIPT", spoken=True)
    package.study_guide.overview = "발화에 근거한 설명"
    raw = blind(package)
    speech = {"id": "s0", "start_ms": 9000, "end_ms": 11000,
              "text": "INDEPENDENT_AUDIO_READING", "confidence": .99}
    raw["source_speech"] = [speech]
    if defect == "missing": raw.pop("source_speech")
    if defect == "time": speech["start_ms"] = 0
    if defect == "uncertain": speech["confidence"] = .71
    if defect == "duplicate": raw["source_speech"].append(speech.copy())
    calls = []
    def provider(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1: return response(package)
        if len(calls) == 2: return response(raw)
        if defect: return response(package)
        return response({"confidence": .99, "material_status": raw["material_status"]})
    mock_client(monkeypatch, video_link, provider)
    with capture_usage() as records, experimental_route():
        analyze()
    blind_prompt = calls[1]["contents"][0]["parts"][-1]["text"]
    assert "PRIVATE_FIRST_TRANSCRIPT" not in blind_prompt
    assert '"start_ms":9000' in blind_prompt
    last = calls[-1]["contents"][0]["parts"]
    if defect:
        assert "file_data" in last[0] and "videoMetadata" not in last[0]
        assert not records[1]["success"] and records[2]["retry"]
    else:
        assert len(last) == 1 and "INDEPENDENT_AUDIO_READING" in last[0]["text"]
        assert "PRIVATE_FIRST_TRANSCRIPT" in last[0]["text"]
        assert not any(r["retry"] for r in records)


def test_unsafe_legacy_reason_cannot_enter_question_or_model_response(monkeypatch):
    value = lecture_with_late_evidence()
    gap = value.visual_gaps[0]
    gap.action = "HOLD"
    gap.reason = "PRIVATE_REASON_ONLY"
    raw = {"action": "answer", "title": "응답", "response_text": "PRIVATE_REASON_ONLY",
           "decision_reason": "확인", "grounding": [], "confidence": .99}
    assert not gemini_agent.sanitize_agent_result(raw, snapshot=value, message="설명").safe_to_speak
    def no_call(*args, **kwargs): raise AssertionError("must not call provider")
    monkeypatch.setattr(gemini_agent, "metered_post", no_call)
    held = asyncio.run(gemini_agent.run_agent_turn(value, message="PRIVATE_REASON_ONLY 설명", current_time_ms=0, api_key_override="test"))
    assert not held.safe_to_speak and "PRIVATE_REASON_ONLY" not in held.model_dump_json()
