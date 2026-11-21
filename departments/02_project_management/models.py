"""
Project Management domain models for Department 02: Project Management.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ProductionStage(str, Enum):
    PLANNING = "PLANNING"
    PRE_PRODUCTION = "PRE_PRODUCTION"
    ASSET_PREPARATION = "ASSET_PREPARATION"
    GENERATION = "GENERATION"
    EDITING = "EDITING"
    ANIMATION = "ANIMATION"
    VFX = "VFX"
    AUDIO = "AUDIO"
    COLOR = "COLOR"
    LOCALIZATION = "LOCALIZATION"
    QC = "QC"
    RENDERING = "RENDERING"
    DELIVERY = "DELIVERY"
    COMPLETED = "COMPLETED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ProjectTemplateType(str, Enum):
    BLANK = "BLANK"
    YOUTUBE_16_9 = "YOUTUBE_16_9"
    SOCIAL_VERTICAL_9_16 = "SOCIAL_VERTICAL_9_16"
    CINEMATIC_2_39 = "CINEMATIC_2_39"
    DOCUMENTARY = "DOCUMENTARY"
    COMMERCIAL = "COMMERCIAL"
    EXPLAINER = "EXPLAINER"
    ANIME_2D = "ANIME_2D"


class ProjectTemplate(BaseModel):
    template_id: ProjectTemplateType
    name: str
    description: str
    width: int
    height: int
    fps: float
    aspect_ratio: str
    color_space: str
    audio_sample_rate: int
    default_tracks: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    stage: ProductionStage
    name: str
    description: str = ""
    assigned_agent: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[UUID] = Field(default_factory=list)
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProjectVersionSnapshot(BaseModel):
    version_id: str
    project_id: UUID
    version_name: str
    notes: Optional[str] = None
    snapshot: Dict[str, Any]
    created_at: str

