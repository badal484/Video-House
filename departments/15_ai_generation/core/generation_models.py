"""
Canonical Generation Models and Data Structures
Department 15: 15_ai_generation
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class GenerationModality(str, Enum):
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"
    IMAGE_TO_VIDEO = "IMAGE_TO_VIDEO"
    VIDEO_TO_VIDEO = "VIDEO_TO_VIDEO"
    REFERENCE_TO_VIDEO = "REFERENCE_TO_VIDEO"
    FIRST_LAST_FRAME_VIDEO = "FIRST_LAST_FRAME_VIDEO"
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"
    IMAGE_TO_IMAGE = "IMAGE_TO_IMAGE"
    INPAINTING = "INPAINTING"
    OUTPAINTING = "OUTPAINTING"
    TEXT_TO_SPEECH = "TEXT_TO_SPEECH"
    TEXT_TO_MUSIC = "TEXT_TO_MUSIC"
    TEXT_TO_SOUND = "TEXT_TO_SOUND"
    TEXT_TO_3D = "TEXT_TO_3D"
    IMAGE_TO_3D = "IMAGE_TO_3D"


class JobStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    QUEUED = "QUEUED"
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"


class ValidationStatus(str, Enum):
    UNCHECKED = "UNCHECKED"
    VALIDATING = "VALIDATING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReferenceCategory(str, Enum):
    CHARACTER_IDENTITY = "CHARACTER_IDENTITY"
    CLOTHING = "CLOTHING"
    ENVIRONMENT = "ENVIRONMENT"
    VISUAL_STYLE = "VISUAL_STYLE"
    COMPOSITION = "COMPOSITION"
    CAMERA = "CAMERA"
    MOTION = "MOTION"
    LIGHTING = "LIGHTING"
    COLOR = "COLOR"


class ReferenceAssetBinding(BaseModel):
    asset_id: str
    category: ReferenceCategory = ReferenceCategory.CHARACTER_IDENTITY
    weight: float = 1.0  # 0.0 to 2.0
    file_path: Optional[str] = None
    notes: Optional[str] = None


class GenerationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    scene_id: Optional[str] = None
    shot_id: Optional[str] = None
    modality: GenerationModality = GenerationModality.TEXT_TO_IMAGE
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    raw_prompt: str
    compiled_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    reference_assets: List[ReferenceAssetBinding] = Field(default_factory=list)
    character_id: Optional[str] = None
    resolution: Tuple[int, int] = (1920, 1080)
    aspect_ratio: str = "16:9"
    duration_sec: float = 5.0
    fps: float = 24.0
    seed: Optional[int] = None
    camera_motion: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    estimated_cost_usd: float = 0.0
    idempotency_key: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_idempotency_key(self) -> str:
        """Calculates a deterministic hash representing the exact generation parameters."""
        hasher = hashlib.sha256()
        hasher.update(f"{self.project_id}_{self.shot_id}_{self.modality}_{self.raw_prompt}_{self.seed}".encode("utf-8"))
        for ref in self.reference_assets:
            hasher.update(f"{ref.asset_id}_{ref.category}".encode("utf-8"))
        key = hasher.hexdigest()
        self.idempotency_key = key
        return key

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GenerationRequest:
        return cls(**data)


class GenerationResult(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    project_id: str
    status: JobStatus = JobStatus.SUBMITTED
    provider_id: str
    model_id: str
    output_asset_ids: List[str] = Field(default_factory=list)
    output_file_paths: List[str] = Field(default_factory=list)
    actual_cost_usd: float = 0.0
    validation_status: ValidationStatus = ValidationStatus.UNCHECKED
    validation_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GenerationResult:
        return cls(**data)


class ProviderSpec(BaseModel):
    provider_id: str
    name: str
    capabilities: List[str] = Field(default_factory=list)
    supported_modalities: List[GenerationModality] = Field(default_factory=list)
    max_duration_sec: float = 10.0
    max_resolution: Tuple[int, int] = (1920, 1080)
    supported_aspect_ratios: List[str] = Field(default_factory=lambda: ["16:9", "9:16", "1:1"])
    cost_per_second: float = 0.05
    cost_per_image: float = 0.04
    requires_api_key: bool = True
    is_active: bool = True
    is_mock: bool = False


class ModelSpec(BaseModel):
    model_id: str
    provider_id: str
    name: str
    version: str
    modality: GenerationModality
    is_commercial_cleared: bool = True
    parameters_count: Optional[str] = None
    pricing_per_call: float = 0.0
