"""
Character Identity & Model Sheet Data Models
Defines persistent character DNA, anatomical proportions, turnaround specifications,
expression matrices, and pose presets.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4


class IdentityStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"


class ExpressionType(str, Enum):
    NEUTRAL = "NEUTRAL"
    HAPPY = "HAPPY"
    SAD = "SAD"
    ANGRY = "ANGRY"
    SURPRISED = "SURPRISED"
    CONFUSED = "CONFUSED"
    FEARFUL = "FEARFUL"
    TALKING = "TALKING"
    SMILING = "SMILING"
    CUSTOM = "CUSTOM"


class PoseType(str, Enum):
    STANDING = "STANDING"
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    SITTING = "SITTING"
    JUMPING = "JUMPING"
    ACTION = "ACTION"
    FALLING = "FALLING"
    CUSTOM = "CUSTOM"


@dataclass
class CharacterIdentity:
    character_id: str
    project_id: str
    name: str
    visual_style: str = "ANIME_CEL"
    head_ratio: float = 7.0  # Anatomical ratio: total height / head height
    age_appearance: str = "Young Adult (18-20)"
    personality: str = ""
    color_palette: Dict[str, str] = field(default_factory=lambda: {
        "skin_base": "#f8d5c2",
        "skin_shadow": "#dca894",
        "hair_base": "#1a2238",
        "hair_highlight": "#3b558c",
        "eye_iris": "#2b7cd3",
        "costume_primary": "#1f2937",
        "costume_accent": "#f59e0b",
    })
    distinctive_features: List[str] = field(default_factory=list)
    costume_layers: Dict[str, Any] = field(default_factory=dict)
    approved_model_sheet_ids: List[str] = field(default_factory=list)
    version: int = 1
    status: IdentityStatus = IdentityStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "project_id": self.project_id,
            "name": self.name,
            "visual_style": self.visual_style,
            "head_ratio": self.head_ratio,
            "age_appearance": self.age_appearance,
            "personality": self.personality,
            "color_palette": self.color_palette,
            "distinctive_features": self.distinctive_features,
            "costume_layers": self.costume_layers,
            "approved_model_sheet_ids": self.approved_model_sheet_ids,
            "version": self.version,
            "status": self.status.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterIdentity":
        return cls(
            character_id=data["character_id"],
            project_id=data["project_id"],
            name=data["name"],
            visual_style=data.get("visual_style", "ANIME_CEL"),
            head_ratio=float(data.get("head_ratio", 7.0)),
            age_appearance=data.get("age_appearance", "Young Adult (18-20)"),
            personality=data.get("personality", ""),
            color_palette=data.get("color_palette", {}),
            distinctive_features=data.get("distinctive_features", []),
            costume_layers=data.get("costume_layers", {}),
            approved_model_sheet_ids=data.get("approved_model_sheet_ids", []),
            version=data.get("version", 1),
            status=IdentityStatus(data.get("status", IdentityStatus.DRAFT.value)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CharacterPose:
    pose_id: str
    character_id: str
    pose_type: PoseType
    name: str
    joint_angles: Dict[str, float] = field(default_factory=dict)  # Bone name -> angle in degrees
    root_position: Tuple[float, float] = (0.0, 0.0)
    duration_frames: int = 12

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pose_id": self.pose_id,
            "character_id": self.character_id,
            "pose_type": self.pose_type.value,
            "name": self.name,
            "joint_angles": self.joint_angles,
            "root_position": list(self.root_position),
            "duration_frames": self.duration_frames,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterPose":
        return cls(
            pose_id=data["pose_id"],
            character_id=data["character_id"],
            pose_type=PoseType(data["pose_type"]),
            name=data["name"],
            joint_angles=data.get("joint_angles", {}),
            root_position=tuple(data.get("root_position", [0.0, 0.0])),
            duration_frames=data.get("duration_frames", 12),
        )


@dataclass
class ModelSheet:
    model_sheet_id: str
    character_id: str
    name: str
    front_view: Dict[str, Any] = field(default_factory=dict)
    three_quarter_view: Dict[str, Any] = field(default_factory=dict)
    side_view: Dict[str, Any] = field(default_factory=dict)
    back_view: Dict[str, Any] = field(default_factory=dict)
    close_up: Dict[str, Any] = field(default_factory=dict)
    alignment_guides: Dict[str, float] = field(default_factory=lambda: {
        "top_of_head": 50.0,
        "eye_line": 95.0,
        "chin": 130.0,
        "shoulder": 160.0,
        "hip": 320.0,
        "knee": 460.0,
        "ankle": 580.0,
    })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_sheet_id": self.model_sheet_id,
            "character_id": self.character_id,
            "name": self.name,
            "front_view": self.front_view,
            "three_quarter_view": self.three_quarter_view,
            "side_view": self.side_view,
            "back_view": self.back_view,
            "close_up": self.close_up,
            "alignment_guides": self.alignment_guides,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelSheet":
        return cls(
            model_sheet_id=data["model_sheet_id"],
            character_id=data["character_id"],
            name=data["name"],
            front_view=data.get("front_view", {}),
            three_quarter_view=data.get("three_quarter_view", {}),
            side_view=data.get("side_view", {}),
            back_view=data.get("back_view", {}),
            close_up=data.get("close_up", {}),
            alignment_guides=data.get("alignment_guides", {}),
        )
