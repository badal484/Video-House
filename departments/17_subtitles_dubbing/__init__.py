"""
Department 17: Subtitles, Dubbing & Localization Package
"""
from .interface import (
    ISubtitlesDubbing,
    SubtitlesDubbingRequest,
    SubtitlesDubbingResponse,
)
from .service import SubtitlesDubbingService
from .core.models import (
    WordTimestamp,
    TranscriptSegment,
    SpeakerRecord,
    Transcript,
    GlossaryTerm,
    TranslationRecord,
    SubtitleCue,
    SubtitleTrack,
    DubbingJob,
    LipSyncJob,
    BiometricConsentRecord,
    LocalizationQCReport,
    SubtitleFormat,
    SubtitleStylePreset,
)

__all__ = [
    "ISubtitlesDubbing",
    "SubtitlesDubbingRequest",
    "SubtitlesDubbingResponse",
    "SubtitlesDubbingService",
    "WordTimestamp",
    "TranscriptSegment",
    "SpeakerRecord",
    "Transcript",
    "GlossaryTerm",
    "TranslationRecord",
    "SubtitleCue",
    "SubtitleTrack",
    "DubbingJob",
    "LipSyncJob",
    "BiometricConsentRecord",
    "LocalizationQCReport",
    "SubtitleFormat",
    "SubtitleStylePreset",
]
