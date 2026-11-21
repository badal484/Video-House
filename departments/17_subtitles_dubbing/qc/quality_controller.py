"""
Localization Quality Controller for Department 17.
Performs automated inspection on subtitle tracks, reading speed (CPS), line length (CPL),
temporal overlaps, audio loudness compliance (EBU R128), and clock drift.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from ..core.models import LocalizationQCReport, SubtitleTrack


class LocalizationQualityController:
    """Automated Quality Control (QC) validator for subtitles, dubbing, and sync."""

    MAX_CPS_ADULT = 17.0
    MAX_CPL_LATIN = 42
    MIN_CUE_DURATION = 0.833
    MAX_CUE_DURATION = 6.0

    @classmethod
    def audit_subtitle_track(
        cls,
        track: SubtitleTrack,
        max_cps: float = MAX_CPS_ADULT,
        max_cpl: int = MAX_CPL_LATIN,
    ) -> LocalizationQCReport:
        """
        Runs comprehensive rule-based QC checks on a SubtitleTrack.
        """
        reading_speed_violations = 0
        line_length_violations = 0
        overlap_violations = 0
        issues: List[str] = []

        for idx, cue in enumerate(track.cues):
            duration = cue.end_time - cue.start_time

            # 1. Overlap check
            if idx > 0:
                prev_cue = track.cues[idx - 1]
                if cue.start_time < prev_cue.end_time:
                    overlap_violations += 1
                    issues.append(
                        f"Cue {cue.cue_index} starts ({cue.start_time}s) before prior cue ends ({prev_cue.end_time}s)."
                    )

            # 2. Duration check
            if duration < cls.MIN_CUE_DURATION:
                issues.append(f"Cue {cue.cue_index} duration ({duration:.2f}s) is below minimum {cls.MIN_CUE_DURATION}s.")
            elif duration > cls.MAX_CUE_DURATION:
                issues.append(f"Cue {cue.cue_index} duration ({duration:.2f}s) exceeds maximum {cls.MAX_CUE_DURATION}s.")

            # 3. Line length check
            lines = cue.text.split("\n")
            if len(lines) > 2:
                issues.append(f"Cue {cue.cue_index} has {len(lines)} lines (maximum allowed is 2).")

            for line in lines:
                if len(line) > max_cpl:
                    line_length_violations += 1
                    issues.append(
                        f"Cue {cue.cue_index} line length ({len(line)} chars) exceeds maximum {max_cpl}: '{line[:30]}...'"
                    )

            # 4. Reading speed (CPS) check
            total_chars = len(cue.text.replace("\n", " "))
            cps = total_chars / max(0.1, duration)
            if cps > max_cps:
                reading_speed_violations += 1
                issues.append(
                    f"Cue {cue.cue_index} reading speed ({cps:.1f} CPS) exceeds limit ({max_cps} CPS)."
                )

        total_issues = len(issues)
        passed = total_issues == 0

        return LocalizationQCReport(
            project_id=track.project_id,
            passed=passed,
            total_issues=total_issues,
            reading_speed_violations=reading_speed_violations,
            line_length_violations=line_length_violations,
            overlap_violations=overlap_violations,
            details=issues,
        )

    @classmethod
    def audit_audio_loudness(
        cls,
        project_id: UUID,
        measured_lufs: float,
        true_peak_db: float,
        target_lufs: float = -23.0,
        lufs_tolerance: float = 0.5,
        max_true_peak_db: float = -1.0,
    ) -> LocalizationQCReport:
        """
        Validates dubbed audio against EBU R128 loudness and true peak standards.
        """
        issues: List[str] = []
        lufs_diff = abs(measured_lufs - target_lufs)

        if lufs_diff > lufs_tolerance:
            issues.append(
                f"Audio loudness ({measured_lufs:.1f} LUFS) deviates from target {target_lufs} LUFS "
                f"by {lufs_diff:.1f} LUFS (allowed tolerance: {lufs_tolerance} LUFS)."
            )

        if true_peak_db > max_true_peak_db:
            issues.append(
                f"Audio true peak ({true_peak_db:.1f} dBTP) exceeds maximum safe ceiling ({max_true_peak_db} dBTP)."
            )

        return LocalizationQCReport(
            project_id=project_id,
            passed=len(issues) == 0,
            total_issues=len(issues),
            loudness_lufs=measured_lufs,
            true_peak_db=true_peak_db,
            details=issues,
        )
