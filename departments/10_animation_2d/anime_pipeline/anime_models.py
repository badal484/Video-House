"""
Anime Pipeline Data Models
Defines cel shading layers, timing charts (Tsume), layout framing (Reiauto),
and multiplane depth specifications.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CelLayerType(str, Enum):
    LINE_ART = "LINE_ART"
    FLAT_BASE = "FLAT_BASE"
    CORE_SHADOW = "CORE_SHADOW"
    SPECULAR_HIGHLIGHT = "SPECULAR_HIGHLIGHT"


class FramingType(str, Enum):
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"
    CLOSE_UP = "CLOSE_UP"
    MEDIUM_SHOT = "MEDIUM_SHOT"
    FULL_SHOT = "FULL_SHOT"
    LONG_SHOT = "LONG_SHOT"


@dataclass
class AnimeCelLayer:
    layer_id: str
    name: str
    layer_type: CelLayerType
    opacity: float = 1.0
    color_override: Optional[str] = None
    visible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "layer_type": self.layer_type.value,
            "opacity": self.opacity,
            "color_override": self.color_override,
            "visible": self.visible,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimeCelLayer":
        return cls(
            layer_id=data["layer_id"],
            name=data["name"],
            layer_type=CelLayerType(data["layer_type"]),
            opacity=float(data.get("opacity", 1.0)),
            color_override=data.get("color_override"),
            visible=data.get("visible", True),
        )


@dataclass
class TimingChart:
    """
    Japanese anime timing chart (Tsume) annotating key poses (Genga) and in-betweens (Doga).
    """
    key_frame_indices: List[int] = field(default_factory=lambda: [0, 8, 16, 24])
    hold_frames: int = 2  # Animating on 2s by default
    easing: str = "EASE_IN_OUT"

    def get_drawing_index_for_frame(self, frame_index: int) -> int:
        """
        Maps a 24 FPS continuous timeline frame index to its stepped exposure drawing index.
        """
        stepped = (frame_index // self.hold_frames) * self.hold_frames
        return stepped


@dataclass
class AnimeLayout:
    layout_id: str
    framing: FramingType = FramingType.MEDIUM_SHOT
    focal_length_mm: float = 35.0
    horizon_y_ratio: float = 0.55  # Horizon line placement (0.0 top, 1.0 bottom)
    light_direction_deg: float = 45.0  # Sun/key light angle in degrees
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "framing": self.framing.value,
            "focal_length_mm": self.focal_length_mm,
            "horizon_y_ratio": self.horizon_y_ratio,
            "light_direction_deg": self.light_direction_deg,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimeLayout":
        return cls(
            layout_id=data["layout_id"],
            framing=FramingType(data.get("framing", FramingType.MEDIUM_SHOT.value)),
            focal_length_mm=float(data.get("focal_length_mm", 35.0)),
            horizon_y_ratio=float(data.get("horizon_y_ratio", 0.55)),
            light_direction_deg=float(data.get("light_direction_deg", 45.0)),
            notes=data.get("notes", ""),
        )
