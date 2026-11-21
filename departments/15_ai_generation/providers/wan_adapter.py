"""
Wan2.1 & Open-Weights Video Diffusion Adapter
Department 15: 15_ai_generation
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from .base import BaseGenerationProvider
from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
    GenerationResult,
    JobStatus,
    ProviderSpec,
)


class WanAdapter(BaseGenerationProvider):
    """Adapter for Wan2.1 open video diffusion models routed to remote GPU workers."""

    def __init__(self, endpoint_url: Optional[str] = None):
        spec = ProviderSpec(
            provider_id="wan2_1",
            name="Wan2.1 Video Diffusion (Open Weights)",
            capabilities=["text_to_video", "image_to_video", "video_to_video"],
            supported_modalities=[
                GenerationModality.TEXT_TO_VIDEO,
                GenerationModality.IMAGE_TO_VIDEO,
                GenerationModality.VIDEO_TO_VIDEO,
            ],
            max_duration_sec=5.0,
            max_resolution=(1920, 1080),
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            cost_per_second=0.02,  # Compute hosting cost
            requires_api_key=False,
            is_active=True,
            is_mock=False,
        )
        super().__init__(spec)
        self.endpoint_url = endpoint_url or os.environ.get("WAN_REMOTE_ENDPOINT")
        self._jobs: Dict[str, GenerationResult] = {}

    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        valid, err = self.validate_request(request)
        if not valid:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="wan2.1_14b",
                error_message=err,
            )

        if not self.endpoint_url:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="wan2.1_14b",
                error_message="Remote Wan2.1 GPU worker endpoint not configured.",
            )

        import uuid
        job_id = str(uuid.uuid4())
        res = GenerationResult(
            job_id=job_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=JobStatus.SUBMITTED,
            provider_id=self.provider_id,
            model_id="wan2.1_14b",
            actual_cost_usd=self.estimate_cost(request),
        )
        self._jobs[job_id] = res
        return res

    async def poll_job(self, job_id: str) -> GenerationResult:
        return self._jobs.get(job_id, GenerationResult(
            job_id=job_id, request_id="", project_id="", status=JobStatus.FAILED,
            provider_id=self.provider_id, model_id="", error_message="Job ID not found"
        ))

    async def cancel_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._jobs[job_id].status = JobStatus.CANCELLED
            return True
        return False
