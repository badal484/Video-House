"""
Temporal Engine Package for Department 04: Media Intelligence.
Provides multi-pass high-resolution sampling, media normalization, and temporal evidence models.
"""
from .normalization import MediaNormalizationService
from .sampling_engine import (
    HighResolutionTemporalSamplingEngine,
    MultiResolutionTimeline,
    TemporalSample
)

__all__ = [
    "MediaNormalizationService",
    "HighResolutionTemporalSamplingEngine",
    "MultiResolutionTimeline",
    "TemporalSample"
]

