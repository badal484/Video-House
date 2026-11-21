"""
Department 17: Subtitles & Dubbing Package
"""
from .interface import (
    ISubtitlesDubbing,
    SubtitlesDubbingRequest,
    SubtitlesDubbingResponse,
)
from .service import SubtitlesDubbingService

__all__ = [
    "ISubtitlesDubbing",
    "SubtitlesDubbingRequest",
    "SubtitlesDubbingResponse",
    "SubtitlesDubbingService",
]
