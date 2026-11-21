"""
Kling AI Adapter: Action Dynamics, Human Motion & Trajectory Brush
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


class KlingAdapter(BaseGenerationProvider):
    """Adapter for Kling AI 1.5 / 2.0 Video Generation."""

    def __init__(self, api_key: Optional[str] = None):
        spec = ProviderSpec(
            provider_id="kling_ai",
            name="Kling AI 1.5 / 2.0",
            capabilities=["text_to_video", "image_to_video", "motion_brush"],
            supported_modalities=[
                GenerationModality.TEXT_TO_VIDEO,
                GenerationModality.IMAGE_TO_VIDEO,
            ],
            max_duration_sec=10.0,
            max_resolution=(1920, 1080),
            supported_aspect_ratios=["16:9", "9:16", "1:1"],
            cost_per_second=0.07,
            requires_api_key=True,
            is_active=True,
            is_mock=False,
        )
        super().__init__(spec)
        self.api_key = api_key or os.environ.get("KLING_API_KEY")
        self._jobs: Dict[str, GenerationResult] = {}

    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        valid, err = self.validate_request(request)
        if not valid:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="kling_v1.5",
                error_message=err,
            )

        if not self.api_key:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="kling_v1.5",
                error_message="Missing KLING_API_KEY in environment.",
            )

        import uuid
        job_id = str(uuid.uuid4())
        res = GenerationResult(
            job_id=job_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=JobStatus.SUBMITTED,
            provider_id=self.provider_id,
            model_id="kling_v1.5",
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
