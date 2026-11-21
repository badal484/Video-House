"""
Audio Validator for Department 18.
Inspects audio presence, sample rate, EBU R128 loudness, true-peak, clipping, and A/V sync drift.
"""
from __future__ import annotations

from typing import List, Optional
from ..core.models import QCCheckType, QCDefect, QCSeverity


class AudioValidator:
    """Validates audio loudness, channel counts, clipping, and sync."""

    @classmethod
    def validate_audio_stream(
        cls,
        has_audio: bool,
        actual_sample_rate: int = 48000,
        expected_sample_rate: int = 48000,
        actual_channels: int = 2,
        expected_channels: int = 2,
    ) -> List[QCDefect]:
        """Validates fundamental audio stream headers."""
        defects: List[QCDefect] = []

        if not has_audio:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=QCSeverity.CRITICAL,
                    rule_name="audio_stream_present",
                    description="No audio stream detected in container.",
                    remediation_suggestion="Verify audio multiplexing parameters during render encoding.",
                )
            )
            return defects

        if actual_sample_rate != expected_sample_rate:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=QCSeverity.ERROR,
                    rule_name="sample_rate_conformance",
                    description=f"Audio sample rate ({actual_sample_rate} Hz) does not match required ({expected_sample_rate} Hz).",
                    remediation_suggestion=f"Resample audio with: -ar {expected_sample_rate}.",
                )
            )

        if actual_channels != expected_channels:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=QCSeverity.ERROR,
                    rule_name="channel_layout_conformance",
                    description=f"Audio channel count ({actual_channels}) deviates from expected ({expected_channels}).",
                    remediation_suggestion=f"Configure channel layout with: -ac {expected_channels}.",
                )
            )

        return defects

    @classmethod
    def validate_loudness_and_peaks(
        cls,
        measured_lufs: float,
        true_peak_db: float,
        target_lufs: float = -23.0,
        lufs_tolerance: float = 0.5,
        max_true_peak_db: float = -1.0,
    ) -> List[QCDefect]:
        """Validates EBU R128 / ITU-R BS.1770 loudness and true peak limits."""
        defects: List[QCDefect] = []
        lufs_diff = abs(measured_lufs - target_lufs)

        if lufs_diff > lufs_tolerance:
            severity = QCSeverity.ERROR if lufs_diff > 1.5 else QCSeverity.WARNING
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=severity,
                    rule_name="loudness_conformance",
                    description=f"Integrated loudness ({measured_lufs:.1f} LUFS) deviates from target {target_lufs} LUFS by {lufs_diff:.1f} LUFS.",
                    remediation_suggestion=f"Apply EBU R128 normalization filter targeting {target_lufs} LUFS.",
                )
            )

        if true_peak_db > max_true_peak_db:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=QCSeverity.ERROR,
                    rule_name="true_peak_limit",
                    description=f"True peak ({true_peak_db:.1f} dBTP) exceeds maximum safe ceiling ({max_true_peak_db} dBTP).",
                    remediation_suggestion="Apply true-peak brickwall limiter at -1.0 dBTP.",
                )
            )

        return defects

    @classmethod
    def validate_av_sync(
        cls,
        video_duration_sec: float,
        audio_duration_sec: float,
        max_drift_sec: float = 0.040,  # ~1 frame @ 24fps
    ) -> List[QCDefect]:
        """Validates that video and audio stream durations align without drift."""
        defects: List[QCDefect] = []
        drift = abs(video_duration_sec - audio_duration_sec)

        if drift > max_drift_sec:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.AUDIO,
                    severity=QCSeverity.ERROR,
                    rule_name="av_sync_drift",
                    description=f"A/V duration mismatch ({drift * 1000:.1f}ms drift): video={video_duration_sec:.3f}s, audio={audio_duration_sec:.3f}s.",
                    remediation_suggestion="Pad or trim audio track to match exact video frame boundary.",
                )
            )

        return defects

