"""
ElevenLabs Voice & SFX Generation Adapter
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


class ElevenLabsAdapter(BaseGenerationProvider):
    """Adapter for ElevenLabs Voiceover & Sound Effect Generation."""

    def __init__(self, api_key: Optional[str] = None):
        spec = ProviderSpec(
            provider_id="elevenlabs",
            name="ElevenLabs Voice & Sound FX",
            capabilities=["text_to_speech", "text_to_sound", "voice_cloning"],
            supported_modalities=[
                GenerationModality.TEXT_TO_SPEECH,
                GenerationModality.TEXT_TO_SOUND,
            ],
            cost_per_second=0.01,
            cost_per_image=0.0,
            requires_api_key=True,
            is_active=True,
            is_mock=False,
        )
        super().__init__(spec)
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self._jobs: Dict[str, GenerationResult] = {}

    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        valid, err = self.validate_request(request)
        if not valid:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="eleven_multilingual_v2",
                error_message=err,
            )

        if not self.api_key:
            return GenerationResult(
                request_id=request.request_id,
                project_id=request.project_id,
                status=JobStatus.FAILED,
                provider_id=self.provider_id,
                model_id="eleven_multilingual_v2",
                error_message="Missing ELEVENLABS_API_KEY in environment.",
            )

        import uuid
        job_id = str(uuid.uuid4())
        res = GenerationResult(
            job_id=job_id,
            request_id=request.request_id,
            project_id=request.project_id,
            status=JobStatus.SUBMITTED,
            provider_id=self.provider_id,
            model_id="eleven_multilingual_v2",
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
