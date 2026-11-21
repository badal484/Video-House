"""
Department 18: Quality Control Service Implementation
Automated multi-stage inspection of media files, video streams, audio, color, and subtitles.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .core.models import QCDefect, QCPolicy, QCReport, QCSeverity
from .inspectors.audio_validator import AudioValidator
from .inspectors.color_validator import ColorValidator
from .inspectors.file_integrity import FileIntegrityInspector
from .inspectors.subtitle_validator import SubtitleValidator
from .inspectors.video_validator import VideoValidator
from .interface import IQualityControl, QualityControlRequest, QualityControlResponse
from .rules.qc_policy_engine import QCPolicyEngine


class QualityControlService(IQualityControl):
    """Production service implementing IQualityControl."""

    async def execute(self, request: QualityControlRequest) -> QualityControlResponse:
        params = request.parameters
        action = params.get("action", "audit_media_file")
        project_id = request.project_id

        try:
            if action == "audit_media_file":
                file_path = params.get("file_path", "")
                raw_aid = params.get("asset_id")
                asset_id = UUID(str(raw_aid)) if raw_aid else uuid4()
                policy_name = params.get("policy_name", "STREAMING_STANDARD")

                defects: List[QCDefect] = []

                # 1. File integrity
                integrity_defects = FileIntegrityInspector.inspect_file(
                    file_path=file_path,
                    expected_checksum=params.get("expected_checksum"),
                )
                defects.extend(integrity_defects)

                # 2. Video validation (if simulated parameters or probe data provided)
                if params.get("video"):
                    v_params = params["video"]
                    v_defects = VideoValidator.validate_stream_properties(
                        actual_width=v_params.get("width", 1920),
                        actual_height=v_params.get("height", 1080),
                        actual_fps=v_params.get("fps", 24.0),
                        expected_width=v_params.get("expected_width", 1920),
                        expected_height=v_params.get("expected_height", 1080),
                        expected_fps=v_params.get("expected_fps", 24.0),
                        is_vfr=v_params.get("is_vfr", False),
                    )
                    defects.extend(v_defects)

                    if "black_intervals" in v_params:
                        defects.extend(VideoValidator.detect_black_frames(v_params["black_intervals"]))
                    if "frozen_intervals" in v_params:
                        defects.extend(VideoValidator.detect_freeze_frames(v_params["frozen_intervals"]))

                # 3. Audio validation
                if params.get("audio"):
                    a_params = params["audio"]
                    a_stream_defects = AudioValidator.validate_audio_stream(
                        has_audio=a_params.get("has_audio", True),
                        actual_sample_rate=a_params.get("sample_rate", 48000),
                        expected_sample_rate=a_params.get("expected_sample_rate", 48000),
                        actual_channels=a_params.get("channels", 2),
                        expected_channels=a_params.get("expected_channels", 2),
                    )
                    defects.extend(a_stream_defects)

                    if "lufs" in a_params:
                        loud_defects = AudioValidator.validate_loudness_and_peaks(
                            measured_lufs=a_params["lufs"],
                            true_peak_db=a_params.get("true_peak_db", -1.5),
                            target_lufs=a_params.get("target_lufs", -23.0),
                        )
                        defects.extend(loud_defects)

                    if "video_duration_sec" in a_params and "audio_duration_sec" in a_params:
                        sync_defects = AudioValidator.validate_av_sync(
                            video_duration_sec=a_params["video_duration_sec"],
                            audio_duration_sec=a_params["audio_duration_sec"],
                        )
                        defects.extend(sync_defects)

                # 4. Compile final report
                report = QCPolicyEngine.compile_report(
                    project_id=project_id,
                    asset_id=asset_id,
                    defects=defects,
                    policy_name=policy_name,
                    render_job_id=UUID(str(params["render_job_id"])) if params.get("render_job_id") else None,
                )

                return QualityControlResponse(
                    success=True,
                    message="Media Quality Control audit completed.",
                    data={"qc_report": report.model_dump(mode="json")},
                )

            return QualityControlResponse(
                success=False,
                message=f"Unknown quality control action: '{action}'.",
            )
        except Exception as e:
            return QualityControlResponse(
                success=False,
                message=f"Quality Control audit error: {str(e)}",
            )

    def health_check(self) -> bool:
        return True
