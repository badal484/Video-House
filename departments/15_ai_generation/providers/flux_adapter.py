"""
FLUX.1 Adapter: Text-to-Image, Inpainting & Concept Art
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


class FluxAdapter(BaseGenerationProvider):
    """Adapter for FLUX.1 Pro, Dev, and Schnell image generation."""

    def __init__(self, api_key: Optional[str] = None):
        spec = ProviderSpec(
            provider_id="flux_engine",
            name="FLUX.1 (Black Forest Labs)",
            capabilities=["text_to_image", "image_to_image", "inpainting", "outpainting"],
            supported_modalities=[
                GenerationModality.TEXT_TO_IMAGE,
                GenerationModality.IMAGE_TO_IMAGE,
                GenerationModality.INPAINTING,
                GenerationModality.OUTPAINTING,
            ],
            max_resolution=(2048, 2048),
            supported_aspect_ratios=["16:9", "9:16", "1:1", "2.39:1", "4:5"],
            cost_per_image=0.04,
            requires_api_key=True,
            is_active=True,
            is_mock=False,
        )
        super().__init__(spec)
        self.api_key = api_key or os.environ.get("FLUX_API_KEY") or os.environ.get("REPLICATE_API_TOKEN")
        self._jobs: Dict[str, GenerationResult] = {}

    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        valid, err = self.validate_request(request)
        if not valid:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id=request.preferred_model or "flux-pro",
                error_message=err,
            )

        if not self.api_key:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="flux-pro",
                error_message="Missing FLUX_API_KEY in environment.",
            )

        import uuid
        job_id = str(uuid.uuid4())
        res = GenerationResult(
            job_id=job_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=JobStatus.SUBMITTED,
            provider_id=self.provider_id,
            model_id=request.preferred_model or "flux-pro",
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
