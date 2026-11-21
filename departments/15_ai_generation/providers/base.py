"""
Base Generation Provider Abstract Interface
Department 15: 15_ai_generation
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ..core.generation_models import (
    GenerationModality,
    GenerationRequest,
    GenerationResult,
    ProviderSpec,
)


class BaseGenerationProvider(ABC):
    """Abstract base class for all AI media generation adapters."""

    def __init__(self, spec: ProviderSpec):
        self.spec = spec

    @property
    def provider_id(self) -> str:
        return self.spec.provider_id

    @property
    def name(self) -> str:
        return self.spec.name

    def supports_modality(self, modality: GenerationModality) -> bool:
        return modality in self.spec.supported_modalities

    def validate_request(self, request: GenerationRequest) -> Tuple[bool, Optional[str]]:
        """Verifies request parameters conform to this provider's capabilities."""
        if not self.supports_modality(request.modality):
            return False, f"Provider '{self.name}' does not support modality '{request.modality.value}'."
        
        if request.duration_sec > self.spec.max_duration_sec:
            return False, f"Requested duration {request.duration_sec}s exceeds provider limit of {self.spec.max_duration_sec}s."

        if request.aspect_ratio not in self.spec.supported_aspect_ratios:
            return False, f"Aspect ratio '{request.aspect_ratio}' not in supported ratios {self.spec.supported_aspect_ratios}."

        return True, None

    def estimate_cost(self, request: GenerationRequest) -> float:
        """Calculates upfront cost in USD for this generation request."""
        if request.modality in (
            GenerationModality.TEXT_TO_VIDEO,
            GenerationModality.IMAGE_TO_VIDEO,
            GenerationModality.VIDEO_TO_VIDEO,
            GenerationModality.FIRST_LAST_FRAME_VIDEO,
        ):
            return round(request.duration_sec * self.spec.cost_per_second, 4)
        else:
            return round(self.spec.cost_per_image, 4)

    @abstractmethod
    async def submit_job(self, request: GenerationRequest) -> GenerationResult:
        """Asynchronously dispatches generation job to provider."""
        pass

    @abstractmethod
    async def poll_job(self, job_id: str) -> GenerationResult:
        """Checks progress or retrieves outputs of a previously submitted job."""
        pass

    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Attempts to cancel an active queued or running job."""
        pass
