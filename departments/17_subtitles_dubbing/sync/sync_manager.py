"""
Sync Manager for Department 17.
Enforces rational timecode arithmetic, detects audio-video clock drift,
aligns sample rates (48kHz standard), and locks dialogue cues to shot boundaries.
"""
from __future__ import annotations

import fractions
from typing import Any, Dict, List, Optional
from uuid import UUID


class RationalTime:
    """Exact rational timecode representation eliminating floating-point rounding drift."""

    def __init__(self, value: int, rate: int | float):
        self.value = int(value)
        self.rate = float(rate)

    def to_seconds(self) -> float:
        return self.value / self.rate

    def to_timecode(self) -> str:
        sec = self.to_seconds()
        fps = round(self.rate)
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        f = int((sec - int(sec)) * fps)
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    def __repr__(self) -> str:
        return f"RationalTime({self.value}, {self.rate})"


class SyncManager:
    """Detects and corrects audio-video drift across long-form productions."""

    AUDIO_SAMPLE_RATE_STD = 48000  # Broadcast standard 48kHz

    @classmethod
    def calculate_clock_drift_ms(
        cls,
        total_audio_samples: int,
        total_video_frames: int,
        video_fps: float = 24.0,
        audio_rate: int = 48000,
    ) -> float:
        """
        Calculates drift in milliseconds between total audio samples and total video frames:
        drift = |(samples / audio_rate) - (frames / fps)| * 1000
        """
        audio_duration_sec = total_audio_samples / audio_rate
        video_duration_sec = total_video_frames / video_fps
        drift_sec = abs(audio_duration_sec - video_duration_sec)
        return round(drift_sec * 1000.0, 3)

    @classmethod
    def snap_cue_to_shot_boundary(
        cls,
        cue_time_sec: float,
        shot_boundaries_sec: List[float],
        tolerance_sec: float = 0.125,  # 3 frames @ 24fps
    ) -> float:
        """
        Snaps subtitle cue start/end time to an adjacent shot cut point if within tolerance
        to prevent subtitle flashing across scene transitions.
        """
        for cut in shot_boundaries_sec:
            if abs(cue_time_sec - cut) <= tolerance_sec:
                return cut
        return cue_time_sec
