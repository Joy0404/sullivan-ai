import httpx
import pytest

from app.adapters.video_link import (
    _gemini_failure_message,
    UnsafeVideoLinkError,
    _analysis_prompt,
    _enforce_model_visual_verification,
    _parse_analysis_json,
    _verification_prompt,
    normalize_video_link,
)
from app.models import AnalysisPackageInput, VideoLinkInput, VisualObservation


def test_youtube_watch_url_becomes_privacy_enhanced_embed() -> None:
    link = normalize_video_link("https://www.youtube.com/watch?v=9hE5-98ZeCg")

    assert link.playback_kind == "youtube"
    assert link.playback_url.startswith("https://www.youtube-nocookie.com/embed/9hE5-98ZeCg")
    assert "disablekb=1" in link.playback_url


def test_localhost_video_link_is_rejected() -> None:
    with pytest.raises(UnsafeVideoLinkError):
        normalize_video_link("http://localhost:9000/lecture.mp4")


def test_gemini_json_is_validated_as_analysis_contract() -> None:
    package = _parse_analysis_json(
        """```json
        {
          "transcript_segments": [
            {"segment_id":"s1","start_ms":0,"end_ms":1000,"text":"설명","confidence":0.9}
          ],
          "visual_observations": [],
          "passage_text": null,
          "highlighted_texts": []
        }
        ```"""
    )

    assert package.transcript_segments[0].text == "설명"


def test_ephemeral_gemini_key_is_never_serialized() -> None:
    payload = VideoLinkInput(
        url="https://www.youtube.com/watch?v=9hE5-98ZeCg",
        rights_confirmed=True,
        gemini_api_key="temporary-secret",
    )

    assert payload.gemini_api_key.get_secret_value() == "temporary-secret"
    assert "gemini_api_key" not in payload.model_dump()


def test_unverified_visual_candidate_is_forced_below_tts_threshold() -> None:
    package = AnalysisPackageInput(
        visual_observations=[
            VisualObservation(
                observation_id="invented-graph",
                timestamp_ms=235_000,
                screen_type="graph",
                kind="graph",
                text="화면에 없는 그래프",
                confidence=0.98,
                importance=0.9,
            )
        ]
    )

    guarded = _enforce_model_visual_verification(package)

    assert guarded.visual_observations[0].confidence == 0.69
    assert guarded.visual_observations[0].metadata["verification"] == "unverified-hold"


def test_confirmed_visual_with_direct_evidence_keeps_confidence() -> None:
    package = AnalysisPackageInput(
        visual_observations=[
            VisualObservation(
                observation_id="real-board",
                timestamp_ms=235_000,
                screen_type="board",
                kind="concept",
                text="성운에서 주계열성으로",
                confidence=0.96,
                importance=0.9,
                metadata={
                    "verification": "corrected",
                    "visible_evidence": ["성운 → 중력 수축 → 원시별 → 주계열성"],
                },
            )
        ]
    )

    guarded = _enforce_model_visual_verification(package)

    assert guarded.visual_observations[0].confidence == 0.96


def test_gemini_prompts_require_adaptive_scan_and_independent_visual_critic() -> None:
    prompt = _analysis_prompt(title="별의 진화", subject="과학", problem_mode=False)
    draft = AnalysisPackageInput()
    critic = _verification_prompt(draft)

    assert "스스로 살펴 분석 지점을 선택" in prompt
    assert "그래프가 없으면" in prompt
    assert "독립적인 시각 근거 검증" in critic
    assert "H-R도" in critic


def test_gemini_auth_failure_has_actionable_message() -> None:
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com")
    response = httpx.Response(403, request=request, text='{"error":{"message":"API key not valid"}}')
    message = _gemini_failure_message(httpx.HTTPStatusError("forbidden", request=request, response=response))

    assert "API 키" in message
    assert "유효하지 않거나" in message
