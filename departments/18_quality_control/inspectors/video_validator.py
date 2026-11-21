"""
Video Validator for Department 18.
Inspects resolution, frame rate, black frames, frozen frames, flash frames, and variable frame rates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..core.models import QCCheckType, QCDefect, QCSeverity


class VideoValidator:
    """Validates video stream dimensions, frame rate, and pixel defects."""

    @classmethod
    def validate_stream_properties(
        cls,
        actual_width: int,
        actual_height: int,
        actual_fps: float,
        expected_width: int,
        expected_height: int,
        expected_fps: float,
        is_vfr: bool = False,
    ) -> List[QCDefect]:
        """Validates video resolution and frame rate conformance."""
        defects: List[QCDefect] = []

        if actual_width != expected_width or actual_height != expected_height:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.VIDEO,
                    severity=QCSeverity.CRITICAL,
                    rule_name="resolution_conformance",
                    description=f"Video resolution ({actual_width}x{actual_height}) does not match required ({expected_width}x{expected_height}).",
                    remediation_suggestion=f"Re-encode with scale filter: scale={expected_width}:{expected_height}.",
                )
            )

        fps_diff = abs(actual_fps - expected_fps)
        if fps_diff > 0.05:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.VIDEO,
                    severity=QCSeverity.ERROR,
                    rule_name="framerate_conformance",
                    description=f"Video frame rate ({actual_fps:.2f} fps) deviates from target ({expected_fps:.2f} fps).",
                    remediation_suggestion=f"Force constant frame rate: -r {expected_fps} -vsync cfr.",
                )
            )

        if is_vfr:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.VIDEO,
                    severity=QCSeverity.ERROR,
                    rule_name="cfr_conformance",
                    description="Variable frame rate (VFR) timestamps detected.",
                    remediation_suggestion="Transcode to Constant Frame Rate (CFR) to prevent playout sync drift.",
                )
            )

        return defects

    @classmethod
    def detect_black_frames(
        cls,
        black_intervals: List[tuple[float, float]],
        max_allowed_black_sec: float = 0.25,
    ) -> List[QCDefect]:
        """Detects unexpected black frames exceeding duration threshold."""
        defects: List[QCDefect] = []
        for start_t, end_t in black_intervals:
            dur = end_t - start_t
            if dur > max_allowed_black_sec:
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.VIDEO,
                        severity=QCSeverity.ERROR,
                        rule_name="black_frame_check",
                        description=f"Black frame sequence detected from {start_t:.2f}s to {end_t:.2f}s ({dur:.2f}s duration).",
                        timestamp_sec=start_t,
                        remediation_suggestion="Inspect timeline for missing clip or unintentional gap in video track.",
                    )
                )
        return defects

    @classmethod
    def detect_freeze_frames(
        cls,
        frozen_intervals: List[tuple[float, float]],
        max_allowed_frozen_sec: float = 1.0,
    ) -> List[QCDefect]:
        """Detects frozen frame sequences exceeding duration threshold."""
        defects: List[QCDefect] = []
        for start_t, end_t in frozen_intervals:
            dur = end_t - start_t
            if dur > max_allowed_frozen_sec:
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.VIDEO,
                        severity=QCSeverity.ERROR,
                        rule_name="freeze_frame_check",
                        description=f"Frozen frame sequence detected from {start_t:.2f}s to {end_t:.2f}s ({dur:.2f}s duration).",
                        timestamp_sec=start_t,
                        remediation_suggestion="Check rendering encoder logs for buffer freeze or dropped input frames.",
                    )
                )
        return defects
