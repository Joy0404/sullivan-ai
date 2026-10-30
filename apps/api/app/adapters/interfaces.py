"""Replaceable STT/OCR/multimodal boundary.

The competition build consumes a time-coded analysis package. A production
adapter may create the same package from a lawfully accessed lecture, but must
not download protected streams or retain raw media by default.
"""

from enum import Enum
from typing import Protocol

from app.models import AnalysisPackageInput


class AdapterErrorCode(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNSUPPORTED_MEDIA = "UNSUPPORTED_MEDIA"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    EMPTY_RESULT = "EMPTY_RESULT"
    NETWORK_ERROR = "NETWORK_ERROR"


class AdapterError(RuntimeError):
    def __init__(self, code: AdapterErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class LectureMediaAnalyzer(Protocol):
    async def analyze(
        self,
        *,
        video_reference: str | None,
        subtitle_text: str | None,
        supporting_text: str | None,
    ) -> AnalysisPackageInput: ...
