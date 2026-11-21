"""
Canonical 2D Animation Project Data Models
Defines application-owned, engine-agnostic structures for 2D animation projects,
scenes, shots, tracks, drawing exposures, keyframes, and cameras.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4


class AnimationType(str, Enum):
    FRAME_BY_FRAME = "FRAME_BY_FRAME"
    SKELETAL_RIG = "SKELETAL_RIG"
    CUT_OUT = "CUT_OUT"
    PROCEDURAL_VECTOR = "PROCEDURAL_VECTOR"
    ANIME_CEL = "ANIME_CEL"
    HYBRID = "HYBRID"


class ExposureRate(str, Enum):
    ON_1S = "ON_1S"  # 1 drawing per frame (24 fps) - action/impact
    ON_2S = "ON_2S"  # 1 drawing per 2 frames (12 fps) - standard anime
    ON_3S = "ON_3S"  # 1 drawing per 3 frames (8 fps) - slow dialogue


class TrackType(str, Enum):
    DRAWING = "DRAWING"
    RIG_BONE = "RIG_BONE"
    PUPPET_LAYER = "PUPPET_LAYER"
    CAMERA = "CAMERA"
    BACKGROUND = "BACKGROUND"
    AUDIO = "AUDIO"


@dataclass
class DrawingExposure:
    drawing_id: str
    duration_frames: int = 2
    hold_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drawing_id": self.drawing_id,
            "duration_frames": self.duration_frames,
            "hold_count": self.hold_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DrawingExposure":
        return cls(
            drawing_id=data["drawing_id"],
            duration_frames=data.get("duration_frames", 2),
            hold_count=data.get("hold_count", 1),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AnimationKeyframe:
    frame_index: int
    property_name: str
    value: Any
    easing_curve: str = "LINEAR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "property_name": self.property_name,
            "value": self.value,
            "easing_curve": self.easing_curve,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationKeyframe":
        return cls(
            frame_index=data["frame_index"],
            property_name=data["property_name"],
            value=data["value"],
            easing_curve=data.get("easing_curve", "LINEAR"),
        )


@dataclass
class AnimationTrack:
    track_id: str
    name: str
    track_type: TrackType
    exposures: List[DrawingExposure] = field(default_factory=list)
    keyframes: List[AnimationKeyframe] = field(default_factory=list)
    visible: bool = True
    locked: bool = False
    z_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "name": self.name,
            "track_type": self.track_type.value,
            "exposures": [e.to_dict() for e in self.exposures],
            "keyframes": [k.to_dict() for k in self.keyframes],
            "visible": self.visible,
            "locked": self.locked,
            "z_index": self.z_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationTrack":
        return cls(
            track_id=data["track_id"],
            name=data["name"],
            track_type=TrackType(data["track_type"]),
            exposures=[DrawingExposure.from_dict(e) for e in data.get("exposures", [])],
            keyframes=[AnimationKeyframe.from_dict(k) for k in data.get("keyframes", [])],
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            z_index=data.get("z_index", 0),
        )


@dataclass
class Camera2D:
    camera_id: str = "default_camera"
    position_x: float = 0.0
    position_y: float = 0.0
    depth_z: float = 1.0
    zoom: float = 1.0
    rotation: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "depth_z": self.depth_z,
            "zoom": self.zoom,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Camera2D":
        return cls(
            camera_id=data.get("camera_id", "default_camera"),
            position_x=float(data.get("position_x", 0.0)),
            position_y=float(data.get("position_y", 0.0)),
            depth_z=float(data.get("depth_z", 1.0)),
            zoom=float(data.get("zoom", 1.0)),
            rotation=float(data.get("rotation", 0.0)),
        )


@dataclass
class AnimationShot:
    shot_id: str
    name: str
    duration_frames: int = 48
    fps: float = 24.0
    camera: Camera2D = field(default_factory=Camera2D)
    tracks: List[AnimationTrack] = field(default_factory=list)
    layout_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shot_id": self.shot_id,
            "name": self.name,
            "duration_frames": self.duration_frames,
            "fps": self.fps,
            "camera": self.camera.to_dict(),
            "tracks": [t.to_dict() for t in self.tracks],
            "layout_notes": self.layout_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationShot":
        return cls(
            shot_id=data["shot_id"],
            name=data["name"],
            duration_frames=data.get("duration_frames", 48),
            fps=data.get("fps", 24.0),
            camera=Camera2D.from_dict(data.get("camera", {})),
            tracks=[AnimationTrack.from_dict(t) for t in data.get("tracks", [])],
            layout_notes=data.get("layout_notes", ""),
        )


@dataclass
class CharacterInstance:
    instance_id: str
    character_id: str
    name: str
    position: Tuple[float, float] = (0.0, 0.0)
    scale: float = 1.0
    facing_direction: str = "RIGHT"  # "RIGHT" or "LEFT"
    active_pose: Optional[str] = None
    active_expression: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "character_id": self.character_id,
            "name": self.name,
            "position": list(self.position),
            "scale": self.scale,
            "facing_direction": self.facing_direction,
            "active_pose": self.active_pose,
            "active_expression": self.active_expression,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterInstance":
        return cls(
            instance_id=data["instance_id"],
            character_id=data["character_id"],
            name=data["name"],
            position=tuple(data.get("position", [0.0, 0.0])),
            scale=data.get("scale", 1.0),
            facing_direction=data.get("facing_direction", "RIGHT"),
            active_pose=data.get("active_pose"),
            active_expression=data.get("active_expression"),
        )


@dataclass
class AnimationScene:
    scene_id: str
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    background_id: Optional[str] = None
    shots: List[AnimationShot] = field(default_factory=list)
    characters: List[CharacterInstance] = field(default_factory=list)
    audio_guide_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "project_id": self.project_id,
            "name": self.name,
            "resolution_w": self.resolution_w,
            "resolution_h": self.resolution_h,
            "fps": self.fps,
            "background_id": self.background_id,
            "shots": [s.to_dict() for s in self.shots],
            "characters": [c.to_dict() for c in self.characters],
            "audio_guide_id": self.audio_guide_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationScene":
        return cls(
            scene_id=data["scene_id"],
            project_id=data["project_id"],
            name=data["name"],
            resolution_w=data.get("resolution_w", 1920),
            resolution_h=data.get("resolution_h", 1080),
            fps=data.get("fps", 24.0),
            background_id=data.get("background_id"),
            shots=[AnimationShot.from_dict(s) for s in data.get("shots", [])],
            characters=[CharacterInstance.from_dict(c) for c in data.get("characters", [])],
            audio_guide_id=data.get("audio_guide_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AnimationProject:
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    scenes: List[AnimationScene] = field(default_factory=list)
    character_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "resolution_w": self.resolution_w,
            "resolution_h": self.resolution_h,
            "fps": self.fps,
            "scenes": [s.to_dict() for s in self.scenes],
            "character_ids": self.character_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationProject":
        return cls(
            project_id=data["project_id"],
            name=data["name"],
            resolution_w=data.get("resolution_w", 1920),
            resolution_h=data.get("resolution_h", 1080),
            fps=data.get("fps", 24.0),
            scenes=[AnimationScene.from_dict(s) for s in data.get("scenes", [])],
            character_ids=data.get("character_ids", []),
            metadata=data.get("metadata", {}),
        )

