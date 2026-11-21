"""
VFX Project & Shot Task Models
Manages shot task lifecycle, parameters, tracking metadata, and review approvals.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class VFXTaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class VFXType(str, Enum):
    SCREEN_REPLACEMENT = "SCREEN_REPLACEMENT"
    CHROMA_KEY = "CHROMA_KEY"
    OBJECT_REMOVAL = "OBJECT_REMOVAL"
    SKY_REPLACEMENT = "SKY_REPLACEMENT"
    TRACKED_GRAPHIC = "TRACKED_GRAPHIC"
    ATMOSPHERIC_EFFECT = "ATMOSPHERIC_EFFECT"
    MULTI_LAYER_COMPOSITE = "MULTI_LAYER_COMPOSITE"
    DEPTH_DISPLACEMENT = "DEPTH_DISPLACEMENT"
    THREE_D_INSERTION = "THREE_D_INSERTION"


@dataclass
class VFXShotTask:
    task_id: str
    project_id: str
    shot_id: str
    name: str
    vfx_type: VFXType
    description: str
    status: VFXTaskStatus = VFXTaskStatus.PENDING
    input_assets: List[str] = field(default_factory=list)
    output_asset_id: Optional[str] = None
    compositing_graph_id: Optional[str] = None
    tracking_data: Dict[str, Any] = field(default_factory=dict)
    qc_report: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "shot_id": self.shot_id,
            "name": self.name,
            "vfx_type": self.vfx_type.value,
            "description": self.description,
            "status": self.status.value,
            "input_assets": self.input_assets,
            "output_asset_id": self.output_asset_id,
            "compositing_graph_id": self.compositing_graph_id,
            "tracking_data": self.tracking_data,
            "qc_report": self.qc_report,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VFXShotTask":
        return cls(
            task_id=data["task_id"],
            project_id=data["project_id"],
            shot_id=data["shot_id"],
            name=data["name"],
            vfx_type=VFXType(data["vfx_type"]),
            description=data.get("description", ""),
            status=VFXTaskStatus(data.get("status", VFXTaskStatus.PENDING.value)),
            input_assets=data.get("input_assets", []),
            output_asset_id=data.get("output_asset_id"),
            compositing_graph_id=data.get("compositing_graph_id"),
            tracking_data=data.get("tracking_data", {}),
            qc_report=data.get("qc_report", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class VFXProject:
    vfx_project_id: str
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    tasks: List[VFXShotTask] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vfx_project_id": self.vfx_project_id,
            "project_id": self.project_id,
            "name": self.name,
            "resolution_w": self.resolution_w,
            "resolution_h": self.resolution_h,
            "fps": self.fps,
            "tasks": [t.to_dict() for t in self.tasks],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VFXProject":
        return cls(
            vfx_project_id=data["vfx_project_id"],
            project_id=data["project_id"],
            name=data["name"],
            resolution_w=data.get("resolution_w", 1920),
            resolution_h=data.get("resolution_h", 1080),
            fps=data.get("fps", 24.0),
            tasks=[VFXShotTask.from_dict(t) for t in data.get("tasks", [])],
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )
