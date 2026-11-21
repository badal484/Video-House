"""
Domain models for Department 19: Rendering & Delivery.
Strongly-typed Pydantic v2 schemas for render profiles, compilation DAGs, jobs, and delivery manifests.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class RenderJobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    BLOCKED = "BLOCKED"
    QUEUED = "QUEUED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    RENDERED = "RENDERED"
    QC_PENDING = "QC_PENDING"
    QC_FAILED = "QC_FAILED"
    APPROVED = "APPROVED"
    DELIVERED = "DELIVERED"


class ProfileCategory(str, enum.Enum):
    MASTER = "MASTER"
    SOCIAL = "SOCIAL"
    BROADCAST = "BROADCAST"
    ARCHIVAL = "ARCHIVAL"
    PREVIEW = "PREVIEW"


class RenderProfile(BaseModel):
    profile_id: str
    name: str
    category: ProfileCategory
    container: str = "mp4"
    video_codec: str = "h264"
    width: int = 1920
    height: int = 1080
    frame_rate: float = 24.0
    pixel_format: str = "yuv420p"
    bitrate_kbps: Optional[int] = 12000
    color_space: str = "bt709"
    transfer_characteristic: str = "bt709"
    matrix_coefficients: str = "bt709"
    audio_codec: str = "aac"
    audio_sample_rate: int = 48000
    audio_channels: int = 2
    target_loudness_lufs: float = -14.0
    max_true_peak_db: float = -1.0
    faststart: bool = True
    qc_policy_id: str = "STREAMING_STANDARD"


class RenderPlanStage(BaseModel):
    stage_id: str
    name: str
    stage_type: str  # DCC, TIMELINE, AUDIO, ENCODE, QC, PACKAGE
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration_sec: float = 1.0
    estimated_cost_usd: float = 0.0
    status: str = "PENDING"
    output_artifacts: List[str] = Field(default_factory=list)


class RenderPlan(BaseModel):
    plan_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    timeline_id: Optional[UUID] = None
    render_profile_id: str
    stages: List[RenderPlanStage] = Field(default_factory=list)
    estimated_duration_sec: float = 0.0
    estimated_cost_usd: float = 0.0
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RenderJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    sequence_id: Optional[UUID] = None
    render_profile_id: str
    status: RenderJobStatus = RenderJobStatus.DRAFT
    priority: int = Field(default=5, ge=1, le=10)
    worker_id: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    output_path: Optional[str] = None
    error_details: Optional[str] = None
    qc_report_id: Optional[UUID] = None
    estimated_duration_sec: float = 0.0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class DeliveryFile(BaseModel):
    file_id: UUID = Field(default_factory=uuid4)
    file_type: str  # MASTER_VIDEO, AUDIO_STEM, SUBTITLE, THUMBNAIL, MANIFEST
    file_path: str
    file_size_bytes: int
    sha256_checksum: str


class DeliveryPackage(BaseModel):
    package_id: UUID = Field(default_factory=uuid4)
    delivery_id: str
    project_id: UUID
    render_job_id: UUID
    master_file_path: str
    sidecar_files: List[DeliveryFile] = Field(default_factory=list)
    manifest_path: str
    total_size_bytes: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeliveryManifest(BaseModel):
    delivery_id: str
    project_id: UUID
    project_version: int = 1
    render_profile: str
    files: List[Dict[str, Any]] = Field(default_factory=list)
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    qc_summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

