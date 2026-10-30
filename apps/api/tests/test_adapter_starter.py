import asyncio

import pytest

from app.adapters.interfaces import AdapterError, AdapterErrorCode
from app.adapters.starter import DeterministicDemoAnalyzer, LiveLectureAnalyzer


def test_demo_adapter_returns_reproducible_analysis_package() -> None:
    analyzer = DeterministicDemoAnalyzer()
    first = asyncio.run(
        analyzer.analyze(
            video_reference=None,
            subtitle_text=None,
            supporting_text=None,
        )
    )
    second = asyncio.run(
        analyzer.analyze(
            video_reference=None,
            subtitle_text=None,
            supporting_text=None,
        )
    )

    assert first == second
    assert first.transcript_segments
    assert first.visual_observations


def test_demo_adapter_can_replace_supporting_passage() -> None:
    result = asyncio.run(
        DeterministicDemoAnalyzer().analyze(
            video_reference=None,
            subtitle_text=None,
            supporting_text="직접 업로드한 지문입니다.",
        )
    )

    assert result.passage_text == "직접 업로드한 지문입니다."


def test_unconfigured_live_adapter_fails_closed() -> None:
    with pytest.raises(AdapterError) as captured:
        asyncio.run(
            LiveLectureAnalyzer().analyze(
                video_reference=None,
                subtitle_text=None,
                supporting_text=None,
            )
        )

    assert captured.value.code == AdapterErrorCode.NOT_CONFIGURED
