"""
Canonical Timeline and Non-Linear Editing Data Models.
Defines application-owned representation for projects, multi-track timelines,
clips, transitions, effects, keyframes, markers, and render tickets.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from core.timeline.time_model import RationalTime, TimeRange


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------------------
# Categorical Enums
# -------------------------------------------------------------------------

class TrackType(str, Enum):
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    SUBTITLE = "SUBTITLE"


class EditMode(str, Enum):
    OVERWRITE = "OVERWRITE"
    INSERT = "INSERT"
    RIPPLE = "RIPPLE"


class TransitionType(str, Enum):
    HARD_CUT = "HARD_CUT"
    CROSS_DISSOLVE = "CROSS_DISSOLVE"
    FADE_IN = "FADE_IN"
    FADE_OUT = "FADE_OUT"
    DIP_TO_BLACK = "DIP_TO_BLACK"
    DIP_TO_WHITE = "DIP_TO_WHITE"
    WIPE_LEFT = "WIPE_LEFT"
    WIPE_RIGHT = "WIPE_RIGHT"
    SLIDE_LEFT = "SLIDE_LEFT"
    SLIDE_RIGHT = "SLIDE_RIGHT"
    PUSH_UP = "PUSH_UP"
    PUSH_DOWN = "PUSH_DOWN"


class EffectType(str, Enum):
    SCALE = "SCALE"
    CROP = "CROP"
    POSITION = "POSITION"
    ROTATION = "ROTATION"
    OPACITY = "OPACITY"
    BLUR = "BLUR"
    BRIGHTNESS = "BRIGHTNESS"
    CONTRAST = "CONTRAST"
    SATURATION = "SATURATION"
    VOLUME = "VOLUME"
    PAN = "PAN"
    AUDIO_FADE = "AUDIO_FADE"
    EQ = "EQ"


class InterpolationMode(str, Enum):
    LINEAR = "LINEAR"
    EASE_IN = "EASE_IN"
    EASE_OUT = "EASE_OUT"
    EASE_IN_OUT = "EASE_IN_OUT"
    HOLD = "HOLD"


class RenderStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# -------------------------------------------------------------------------
# Canonical Entities
# -------------------------------------------------------------------------

@dataclass
class Keyframe:
    property_name: str
    time: RationalTime
    value: float
    interpolation: InterpolationMode = InterpolationMode.LINEAR
    easing_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_name": self.property_name,
            "time": self.time.to_dict(),
            "value": self.value,
            "interpolation": self.interpolation.value,
            "easing_params": self.easing_params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Keyframe":
        return cls(
            property_name=data["property_name"],
            time=RationalTime.from_dict(data["time"]),
            value=float(data["value"]),
            interpolation=InterpolationMode(data.get("interpolation", "LINEAR")),
            easing_params=data.get("easing_params", {})
        )


@dataclass
class Effect:
    effect_id: UUID
    effect_type: EffectType
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    start_time: Optional[RationalTime] = None
    duration: Optional[RationalTime] = None
    keyframes: List[Keyframe] = field(default_factory=list)
    processing_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_id": str(self.effect_id),
            "effect_type": self.effect_type.value,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "start_time": self.start_time.to_dict() if self.start_time else None,
            "duration": self.duration.to_dict() if self.duration else None,
            "keyframes": [k.to_dict() for k in self.keyframes],
            "processing_order": self.processing_order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Effect":
        return cls(
            effect_id=UUID(data["effect_id"]),
            effect_type=EffectType(data["effect_type"]),
            parameters=data.get("parameters", {}),
            enabled=data.get("enabled", True),
            start_time=RationalTime.from_dict(data["start_time"]) if data.get("start_time") else None,
            duration=RationalTime.from_dict(data["duration"]) if data.get("duration") else None,
            keyframes=[Keyframe.from_dict(k) for k in data.get("keyframes", [])],
            processing_order=data.get("processing_order", 0)
        )


@dataclass
class Transition:
    transition_id: UUID
    transition_type: TransitionType
    start_time: RationalTime
    duration: RationalTime
    from_clip_id: Optional[UUID] = None
    to_clip_id: Optional[UUID] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    easing: str = "LINEAR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": str(self.transition_id),
            "transition_type": self.transition_type.value,
            "start_time": self.start_time.to_dict(),
            "duration": self.duration.to_dict(),
            "from_clip_id": str(self.from_clip_id) if self.from_clip_id else None,
            "to_clip_id": str(self.to_clip_id) if self.to_clip_id else None,
            "parameters": self.parameters,
            "easing": self.easing
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transition":
        return cls(
            transition_id=UUID(data["transition_id"]),
            transition_type=TransitionType(data["transition_type"]),
            start_time=RationalTime.from_dict(data["start_time"]),
            duration=RationalTime.from_dict(data["duration"]),
            from_clip_id=UUID(data["from_clip_id"]) if data.get("from_clip_id") else None,
            to_clip_id=UUID(data["to_clip_id"]) if data.get("to_clip_id") else None,
            parameters=data.get("parameters", {}),
            easing=data.get("easing", "LINEAR")
        )


@dataclass
class Clip:
    clip_id: UUID
    asset_id: UUID
    track_id: UUID
    timeline_start: RationalTime
    timeline_duration: RationalTime
    source_in: RationalTime
    source_out: RationalTime
    speed: float = 1.0
    transform: Dict[str, Any] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "scale_x": 1.0, "scale_y": 1.0, "rotation": 0.0})
    opacity: float = 1.0
    volume: float = 1.0
    pan: float = 0.0
    enabled: bool = True
    effects: List[Effect] = field(default_factory=list)
    keyframes: List[Keyframe] = field(default_factory=list)
    linked_clip_id: Optional[UUID] = None
    name: str = "Clip"

    @property
    def timeline_end(self) -> RationalTime:
        return self.timeline_start + self.timeline_duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clip_id": str(self.clip_id),
            "asset_id": str(self.asset_id),
            "track_id": str(self.track_id),
            "timeline_start": self.timeline_start.to_dict(),
            "timeline_duration": self.timeline_duration.to_dict(),
            "timeline_end": self.timeline_end.to_dict(),
            "source_in": self.source_in.to_dict(),
            "source_out": self.source_out.to_dict(),
            "speed": self.speed,
            "transform": self.transform,
            "opacity": self.opacity,
            "volume": self.volume,
            "pan": self.pan,
            "enabled": self.enabled,
            "effects": [e.to_dict() for e in self.effects],
            "keyframes": [k.to_dict() for k in self.keyframes],
            "linked_clip_id": str(self.linked_clip_id) if self.linked_clip_id else None,
            "name": self.name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clip":
        return cls(
            clip_id=UUID(data["clip_id"]),
            asset_id=UUID(data["asset_id"]),
            track_id=UUID(data["track_id"]),
            timeline_start=RationalTime.from_dict(data["timeline_start"]),
            timeline_duration=RationalTime.from_dict(data["timeline_duration"]),
            source_in=RationalTime.from_dict(data["source_in"]),
            source_out=RationalTime.from_dict(data["source_out"]),
            speed=float(data.get("speed", 1.0)),
            transform=data.get("transform", {"x": 0.0, "y": 0.0, "scale_x": 1.0, "scale_y": 1.0, "rotation": 0.0}),
            opacity=float(data.get("opacity", 1.0)),
            volume=float(data.get("volume", 1.0)),
            pan=float(data.get("pan", 0.0)),
            enabled=data.get("enabled", True),
            effects=[Effect.from_dict(e) for e in data.get("effects", [])],
            keyframes=[Keyframe.from_dict(k) for k in data.get("keyframes", [])],
            linked_clip_id=UUID(data["linked_clip_id"]) if data.get("linked_clip_id") else None,
            name=data.get("name", "Clip")
        )


@dataclass
class Track:
    track_id: UUID
    timeline_id: UUID
    track_type: TrackType
    name: str
    order_index: int = 0
    is_muted: bool = False
    is_visible: bool = True
    is_locked: bool = False
    is_solo: bool = False
    gain: float = 1.0
    opacity: float = 1.0
    clips: List[Clip] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": str(self.track_id),
            "timeline_id": str(self.timeline_id),
            "track_type": self.track_type.value,
            "name": self.name,
            "order_index": self.order_index,
            "is_muted": self.is_muted,
            "is_visible": self.is_visible,
            "is_locked": self.is_locked,
            "is_solo": self.is_solo,
            "gain": self.gain,
            "opacity": self.opacity,
            "clips": [c.to_dict() for c in sorted(self.clips, key=lambda x: x.timeline_start.to_seconds())],
            "transitions": [t.to_dict() for t in self.transitions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Track":
        return cls(
            track_id=UUID(data["track_id"]),
            timeline_id=UUID(data["timeline_id"]),
            track_type=TrackType(data["track_type"]),
            name=data["name"],
            order_index=data.get("order_index", 0),
            is_muted=data.get("is_muted", False),
            is_visible=data.get("is_visible", True),
            is_locked=data.get("is_locked", False),
            is_solo=data.get("is_solo", False),
            gain=float(data.get("gain", 1.0)),
            opacity=float(data.get("opacity", 1.0)),
            clips=[Clip.from_dict(c) for c in data.get("clips", [])],
            transitions=[Transition.from_dict(t) for t in data.get("transitions", [])]
        )


@dataclass
class Marker:
    marker_id: UUID
    timeline_id: UUID
    time: RationalTime
    name: str = "Marker"
    color: str = "#00FF00"
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "marker_id": str(self.marker_id),
            "timeline_id": str(self.timeline_id),
            "time": self.time.to_dict(),
            "name": self.name,
            "color": self.color,
            "comment": self.comment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Marker":
        return cls(
            marker_id=UUID(data["marker_id"]),
            timeline_id=UUID(data["timeline_id"]),
            time=RationalTime.from_dict(data["time"]),
            name=data.get("name", "Marker"),
            color=data.get("color", "#00FF00"),
            comment=data.get("comment", "")
        )


@dataclass
class Timeline:
    timeline_id: UUID
    project_id: UUID
    name: str
    time_base: float = 24.0
    duration: RationalTime = field(default_factory=lambda: RationalTime(0, 24.0))
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: float = 24.0
    sample_rate: int = 48000
    tracks: List[Track] = field(default_factory=list)
    markers: List[Marker] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def calculate_total_duration(self) -> RationalTime:
        max_sec = 0.0
        for track in self.tracks:
            for clip in track.clips:
                end_sec = clip.timeline_end.to_seconds()
                if end_sec > max_sec:
                    max_sec = end_sec
        return RationalTime.from_seconds(max_sec, self.fps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline_id": str(self.timeline_id),
            "project_id": str(self.project_id),
            "name": self.name,
            "time_base": self.time_base,
            "duration": self.duration.to_dict(),
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "fps": self.fps,
            "sample_rate": self.sample_rate,
            "tracks": [t.to_dict() for t in self.tracks],
            "markers": [m.to_dict() for m in self.markers],
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timeline":
        return cls(
            timeline_id=UUID(data["timeline_id"]),
            project_id=UUID(data["project_id"]),
            name=data["name"],
            time_base=float(data.get("time_base", 24.0)),
            duration=RationalTime.from_dict(data["duration"]) if data.get("duration") else RationalTime(0, 24.0),
            resolution_width=int(data.get("resolution_width", 1920)),
            resolution_height=int(data.get("resolution_height", 1080)),
            fps=float(data.get("fps", 24.0)),
            sample_rate=int(data.get("sample_rate", 48000)),
            tracks=[Track.from_dict(t) for t in data.get("tracks", [])],
            markers=[Marker.from_dict(m) for m in data.get("markers", [])],
            version=int(data.get("version", 1)),
            created_at=data.get("created_at", utc_now_iso()),
            updated_at=data.get("updated_at", utc_now_iso())
        )


@dataclass
class EditingProject:
    project_id: UUID
    name: str
    active_timeline_id: Optional[UUID] = None
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "color_space": "Rec.709",
        "drop_frame": False,
        "proxy_mode": True
    })
    timelines: List[Timeline] = field(default_factory=list)
    revision: int = 1
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class RenderJob:
    render_id: UUID
    project_id: UUID
    timeline_id: UUID
    output_path: str
    is_preview: bool = False
    format_preset: str = "H264_1080P"
    status: RenderStatus = RenderStatus.QUEUED
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None
