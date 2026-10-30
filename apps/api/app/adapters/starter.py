from app.adapters.interfaces import AdapterError, AdapterErrorCode
from app.core.demo import build_demo_package
from app.models import AnalysisPackageInput


class DeterministicDemoAnalyzer:
    """Reproducible competition scenario, never presented as live AI."""

    async def analyze(
        self,
        *,
        video_reference: str | None = None,
        subtitle_text: str | None = None,
        supporting_text: str | None = None,
    ) -> AnalysisPackageInput:
        package = build_demo_package()
        if supporting_text:
            package = package.model_copy(update={"passage_text": supporting_text})
        return package


class LiveLectureAnalyzer:
    """Fail-closed seam for a licensed STT/OCR or multimodal provider."""

    async def analyze(
        self,
        *,
        video_reference: str | None,
        subtitle_text: str | None,
        supporting_text: str | None,
    ) -> AnalysisPackageInput:
        raise AdapterError(
            AdapterErrorCode.NOT_CONFIGURED,
            "실제 영상 분석 공급자가 설정되지 않았습니다. 분석 JSON 또는 데모 모드를 사용하세요.",
        )
