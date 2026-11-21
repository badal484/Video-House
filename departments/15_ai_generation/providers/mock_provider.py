"""
Mock Local Provider for Deterministic Testing & Offline Prototyping
Department 15: 15_ai_generation
"""
from __future__ import annotations

import os
import uuid
import numpy as np
from datetime import datetime, timezone
import scipy.io.wavfile

from .base import BaseGenerationProvider
from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
    GenerationResult,
    JobStatus,
    ProviderSpec,
    ValidationStatus,
)


class MockLocalProvider(BaseGenerationProvider):
    """
    Deterministic local generation provider.
    Synthesizes valid image, video, and audio media files locally without network access or cloud costs.
    """

    def __init__(self, output_dir: str = "temp/generation_scratch"):
        spec = ProviderSpec(
            provider_id="mock_local_engine",
            name="Mock Local Generation Engine",
            capabilities=[
                "text_to_video",
                "image_to_video",
                "video_to_video",
                "reference_to_video",
                "text_to_image",
                "image_to_image",
                "inpainting",
                "outpainting",
                "text_to_speech",
                "text_to_music",
                "text_to_sound",
                "text_to_3d",
            ],
            supported_modalities=list(GenerationModality),
            max_duration_sec=30.0,
            max_resolution=(3840, 2160),
            supported_aspect_ratios=["16:9", "9:16", "1:1", "2.39:1", "4:5"],
            cost_per_second=0.0,
            cost_per_image=0.0,
            requires_api_key=False,
            is_active=True,
            is_mock=True,
        )
        super().__init__(spec)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._jobs = {}

    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        valid, err = self.validate_request(request)
        if not valid:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="mock_v1",
                error_message=err,
            )

        job_id = str(uuid.uuid4())
        out_paths = []
        out_asset_ids = []

        # Generate synthetic compliant media based on modality
        if request.modality in (
            GenerationModality.TEXT_TO_VIDEO,
            GenerationModality.IMAGE_TO_VIDEO,
            GenerationModality.VIDEO_TO_VIDEO,
            GenerationModality.FIRST_LAST_FRAME_VIDEO,
        ):
            # Synthetic 1.0s video file
            out_file = os.path.join(self.output_dir, f"{job_id}_video.mp4")
            # Synthesize 24 frames of 640x360 video via OpenCV or numpy
            try:
                import cv2
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                vw = cv2.VideoWriter(out_file, fourcc, 24.0, (640, 360))
                for f_idx in range(24):
                    frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    # Colored background + frame number
                    frame[:, :, 0] = int((f_idx * 10) % 255)
                    frame[:, :, 1] = 120
                    frame[:, :, 2] = 200
                    cv2.putText(frame, f"Mock Shot {request.shot_id or '1'} F:{f_idx}", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                    vw.write(frame)
                vw.release()
            except Exception:
                with open(out_file, "wb") as f:
                    f.write(b"MOCK_MP4_CONTAINER_BYTES")
            out_paths.append(out_file)
            out_asset_ids.append(str(uuid.uuid4()))

        elif request.modality in (
            GenerationModality.TEXT_TO_IMAGE,
            GenerationModality.IMAGE_TO_IMAGE,
            GenerationModality.INPAINTING,
            GenerationModality.OUTPAINTING,
        ):
            # Synthetic PNG image
            out_file = os.path.join(self.output_dir, f"{job_id}_image.png")
            try:
                import cv2
                img = np.zeros((512, 512, 3), dtype=np.uint8)
                img[:] = (40, 40, 60)
                cv2.circle(img, (256, 256), 120, (100, 200, 250), -1)
                cv2.putText(img, "MOCK GENERATION", (80, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                cv2.imwrite(out_file, img)
            except Exception:
                with open(out_file, "wb") as f:
                    f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00")
            out_paths.append(out_file)
            out_asset_ids.append(str(uuid.uuid4()))

        elif request.modality in (
            GenerationModality.TEXT_TO_SPEECH,
            GenerationModality.TEXT_TO_MUSIC,
            GenerationModality.TEXT_TO_SOUND,
        ):
            # Synthetic WAV audio
            out_file = os.path.join(self.output_dir, f"{job_id}_audio.wav")
            sr = 48000
            t = np.linspace(0.0, 1.0, sr, endpoint=False)
            sine = (0.2 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
            scipy.io.wavfile.write(out_file, sr, sine)
            out_paths.append(out_file)
            out_asset_ids.append(str(uuid.uuid4()))

        else:
            # 3D Placeholder
            out_file = os.path.join(self.output_dir, f"{job_id}_mesh.obj")
            with open(out_file, "w") as f:
                f.write("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            out_paths.append(out_file)
            out_asset_ids.append(str(uuid.uuid4()))

        res = GenerationResult(
            job_id=job_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=JobStatus.SUCCEEDED,
            provider_id=self.provider_id,
            model_id="mock_generator_v1",
            output_asset_ids=out_asset_ids,
            output_file_paths=out_paths,
            actual_cost_usd=0.0,
            validation_status=ValidationStatus.PASSED,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._jobs[job_id] = res
        return res

    async def poll_job(self, job_id: str) -> GenerationResult:
        if job_id in self._jobs:
            return self._jobs[job_id]
        return GenerationResult(
            job_id=job_id,
            request_id="unknown",
            project_id="unknown",
            status=JobStatus.FAILED,
            provider_id=self.provider_id,
            model_id="mock",
            error_message="Job not found",
        )

    async def cancel_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._jobs[job_id].status = JobStatus.CANCELLED
            return True
        return False
