"""
Canonical Motion Graphics Composition Data Models.
Defines application-owned, engine-agnostic schemas for 2D motion design.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import json

from core.timeline.time_model import RationalTime, TimeRange


class LayerType(str, Enum):
    TEXT = "TEXT"
    SHAPE = "SHAPE"
    CHART = "CHART"
    HUD = "HUD"
    BRAND = "BRAND"
    CINEMATIC_OVERLAY = "CINEMATIC_OVERLAY"
    CONTAINER = "CONTAINER"


class EasingType(str, Enum):
    LINEAR = "LINEAR"
    EASE_IN = "EASE_IN"
    EASE_OUT = "EASE_OUT"
    EASE_IN_OUT = "EASE_IN_OUT"
    SPRING = "SPRING"
    BOUNCE = "BOUNCE"
    HOLD = "HOLD"


class TextRevealMode(str, Enum):
    NONE = "NONE"
    WORD_BY_WORD = "WORD_BY_WORD"
    CHAR_BY_CHAR = "CHAR_BY_CHAR"
    LINE_BY_LINE = "LINE_BY_LINE"
    TYPEWRITER = "TYPEWRITER"
    MASKED_REVEAL = "MASKED_REVEAL"


class ChartType(str, Enum):
    BAR = "BAR"
    LINE = "LINE"
    PIE = "PIE"
    DONUT = "DONUT"
    PROGRESS_RING = "PROGRESS_RING"
    COUNTER = "COUNTER"


class HUDType(str, Enum):
    RETICLE = "RETICLE"
    SCAN_LINE = "SCAN_LINE"
    TECH_GRID = "TECH_GRID"
    TELEMETRY = "TELEMETRY"
    RADAR = "RADAR"


class BackgroundType(str, Enum):
    TRANSPARENT = "TRANSPARENT"
    SOLID = "SOLID"
    GRADIENT = "GRADIENT"


@dataclass
class BackgroundConfig:
    type: BackgroundType = BackgroundType.TRANSPARENT
    color: str = "#00000000"
    gradient_colors: List[str] = field(default_factory=list)
    gradient_angle_deg: float = 0.0


@dataclass
class Transform2D:
    x: float = 0.0          # Normalized (-1.0 to 1.0) or absolute px
    y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation_deg: float = 0.0
    opacity: float = 1.0
    anchor_x: float = 0.5   # 0.0=left, 0.5=center, 1.0=right
    anchor_y: float = 0.5   # 0.0=top, 0.5=center, 1.0=bottom


@dataclass
class KeyframePoint:
    offset_time: RationalTime
    value: Union[float, str, List[float]]
    easing: EasingType = EasingType.LINEAR


@dataclass
class KeyframeAnimation:
    target_property: str   # 'x', 'y', 'scale_x', 'scale_y', 'opacity', 'rotation_deg', 'progress', etc.
    keyframes: List[KeyframePoint] = field(default_factory=list)


@dataclass
class TextElement:
    text: str
    font_family: str = "Inter"
    font_size: float = 48.0
    font_weight: str = "bold"
    fill_color: str = "#FFFFFF"
    stroke_color: Optional[str] = None
    stroke_width: float = 0.0
    text_align: str = "center"  # 'left', 'center', 'right'
    line_height: float = 1.2
    letter_spacing: float = 0.0
    reveal_mode: TextRevealMode = TextRevealMode.NONE
    stagger_delay_sec: float = 0.05
    show_cursor: bool = False
    cursor_color: str = "#00F0FF"


@dataclass
class ShapeElement:
    shape_type: str = "RECTANGLE"  # RECTANGLE, CIRCLE, LINE, POLYGON
    width: float = 200.0
    height: float = 100.0
    radius: float = 50.0
    points: List[Tuple[float, float]] = field(default_factory=list)
    fill_color: str = "#00F0FF"
    stroke_color: str = "#FFFFFF"
    stroke_width: float = 2.0
    corner_radius: float = 8.0


@dataclass
class ChartDataPoint:
    label: str
    value: float
    color: str = "#00F0FF"


@dataclass
class ChartElement:
    chart_type: ChartType = ChartType.BAR
    data: List[ChartDataPoint] = field(default_factory=list)
    max_value: Optional[float] = None
    animation_progress: float = 1.0  # 0.0 to 1.0
    show_labels: bool = True
    show_values: bool = True
    unit_suffix: str = ""
    bar_width: float = 40.0
    gap: float = 20.0


@dataclass
class HUDElement:
    hud_type: HUDType = HUDType.RETICLE
    primary_color: str = "#00F0FF"
    secondary_color: str = "#39FF14"
    line_width: float = 2.0
    rotation_speed: float = 30.0  # deg/sec
    scan_progress: float = 0.0
    telemetry_data: Dict[str, str] = field(default_factory=dict)
    coordinates: Tuple[float, float] = (0.0, 0.0)


@dataclass
class BrandElement:
    logo_asset_id: Optional[str] = None
    brand_name: str = "STUDIO"
    tagline: Optional[str] = None
    primary_color: str = "#00F0FF"
    accent_color: str = "#FF007F"
    reveal_progress: float = 1.0


@dataclass
class CinematicOverlayElement:
    overlay_type: str = "LIGHT_STREAK"  # LIGHT_STREAK, PARTICLES, GEOMETRIC_WIPE, GLITCH
    intensity: float = 1.0
    color: str = "#00F0FF"
    progress: float = 0.0


GraphicElementUnion = Union[
    TextElement, ShapeElement, ChartElement, HUDElement, BrandElement, CinematicOverlayElement
]


@dataclass
class MotionLayer:
    layer_id: str = field(default_factory=lambda: f"lyr_{uuid.uuid4().hex[:12]}")
    name: str = "Layer"
    z_index: int = 1
    layer_type: LayerType = LayerType.TEXT
    visible: bool = True
    transform: Transform2D = field(default_factory=Transform2D)
    element: Optional[GraphicElementUnion] = None
    animations: List[KeyframeAnimation] = field(default_factory=list)


@dataclass
class MotionScene:
    scene_id: str = field(default_factory=lambda: f"scn_{uuid.uuid4().hex[:12]}")
    name: str = "Scene 1"
    start_time: RationalTime = field(default_factory=lambda: RationalTime(0, 24.0))
    duration: RationalTime = field(default_factory=lambda: RationalTime(120, 24.0))
    layers: List[MotionLayer] = field(default_factory=list)


@dataclass
class RenderConfig:
    resolution: Tuple[int, int] = (1920, 1080)
    fps: float = 24.0
    pixel_format: str = "yuva444p10le"  # ProRes 4444 yuva444p10le, WebM yuva420p, or rgba
    output_format: str = "mov"          # 'mov', 'webm', 'png_sequence'
    codec: str = "prores_ks"            # 'prores_ks', 'libvpx-vp9', 'png'
    crf_or_bitrate: str = "high"
    straight_alpha: bool = True


@dataclass
class MotionComposition:
    composition_id: str = field(default_factory=lambda: f"cmp_{uuid.uuid4().hex[:12]}")
    project_id: str = "default_project"
    name: str = "Motion Composition"
    resolution: Tuple[int, int] = (1920, 1080)
    fps: float = 24.0
    duration: RationalTime = field(default_factory=lambda: RationalTime(120, 24.0))
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    scenes: List[MotionScene] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def total_frames(self) -> int:
        rescaled = self.duration.rescaled_to(self.fps)
        return int(round(rescaled.value))

    def to_dict(self) -> Dict[str, Any]:
        """Custom serialization preserving RationalTime values."""
        def _serialize(obj):
            if isinstance(obj, RationalTime):
                return {"value": obj.value, "rate": obj.rate}
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, (Transform2D, KeyframePoint, KeyframeAnimation, BackgroundConfig)):
                return {k: _serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, (TextElement, ShapeElement, ChartElement, ChartDataPoint,
                                HUDElement, BrandElement, CinematicOverlayElement)):
                return {k: _serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, MotionLayer):
                d = {k: _serialize(v) for k, v in obj.__dict__.items() if k != "element"}
                if obj.element:
                    d["element"] = _serialize(obj.element)
                    d["element_kind"] = obj.layer_type.value
                return d
            if isinstance(obj, MotionScene):
                return {k: _serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, MotionComposition):
                return {k: _serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [_serialize(x) for x in obj]
            if isinstance(obj, dict):
                return {k: _serialize(v) for k, v in obj.items()}
            return obj

        return _serialize(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MotionComposition":
        """Reconstruct MotionComposition from serialized dictionary."""
        dur_raw = data.get("duration", {"value": 120, "rate": 24.0})
        duration = RationalTime(int(dur_raw["value"]), float(dur_raw["rate"]))
        fps = float(data.get("fps", 24.0))
        res = tuple(data.get("resolution", (1920, 1080)))

        bg_data = data.get("background", {})
        bg = BackgroundConfig(
            type=BackgroundType(bg_data.get("type", "TRANSPARENT")),
            color=bg_data.get("color", "#00000000"),
            gradient_colors=bg_data.get("gradient_colors", []),
            gradient_angle_deg=float(bg_data.get("gradient_angle_deg", 0.0))
        )

        scenes: List[MotionScene] = []
        for scn_d in data.get("scenes", []):
            st_raw = scn_d.get("start_time", {"value": 0, "rate": fps})
            st = RationalTime(int(st_raw["value"]), float(st_raw["rate"]))
            sd_raw = scn_d.get("duration", {"value": int(duration.value), "rate": fps})
            sd = RationalTime(int(sd_raw["value"]), float(sd_raw["rate"]))

            layers: List[MotionLayer] = []
            for lyr_d in scn_d.get("layers", []):
                t_d = lyr_d.get("transform", {})
                transform = Transform2D(
                    x=float(t_d.get("x", 0.0)),
                    y=float(t_d.get("y", 0.0)),
                    scale_x=float(t_d.get("scale_x", 1.0)),
                    scale_y=float(t_d.get("scale_y", 1.0)),
                    rotation_deg=float(t_d.get("rotation_deg", 0.0)),
                    opacity=float(t_d.get("opacity", 1.0)),
                    anchor_x=float(t_d.get("anchor_x", 0.5)),
                    anchor_y=float(t_d.get("anchor_y", 0.5)),
                )

                ltype = LayerType(lyr_d.get("layer_type", "TEXT"))
                elem_d = lyr_d.get("element", {})
                elem = None
                if ltype == LayerType.TEXT and elem_d:
                    elem = TextElement(
                        text=elem_d.get("text", ""),
                        font_family=elem_d.get("font_family", "Inter"),
                        font_size=float(elem_d.get("font_size", 48.0)),
                        font_weight=elem_d.get("font_weight", "bold"),
                        fill_color=elem_d.get("fill_color", "#FFFFFF"),
                        stroke_color=elem_d.get("stroke_color"),
                        stroke_width=float(elem_d.get("stroke_width", 0.0)),
                        text_align=elem_d.get("text_align", "center"),
                        line_height=float(elem_d.get("line_height", 1.2)),
                        letter_spacing=float(elem_d.get("letter_spacing", 0.0)),
                        reveal_mode=TextRevealMode(elem_d.get("reveal_mode", "NONE")),
                        stagger_delay_sec=float(elem_d.get("stagger_delay_sec", 0.05)),
                        show_cursor=bool(elem_d.get("show_cursor", False)),
                        cursor_color=elem_d.get("cursor_color", "#00F0FF")
                    )
                elif ltype == LayerType.SHAPE and elem_d:
                    elem = ShapeElement(
                        shape_type=elem_d.get("shape_type", "RECTANGLE"),
                        width=float(elem_d.get("width", 200.0)),
                        height=float(elem_d.get("height", 100.0)),
                        radius=float(elem_d.get("radius", 50.0)),
                        fill_color=elem_d.get("fill_color", "#00F0FF"),
                        stroke_color=elem_d.get("stroke_color", "#FFFFFF"),
                        stroke_width=float(elem_d.get("stroke_width", 2.0)),
                        corner_radius=float(elem_d.get("corner_radius", 8.0))
                    )
                elif ltype == LayerType.CHART and elem_d:
                    data_points = [
                        ChartDataPoint(
                            label=p.get("label", ""),
                            value=float(p.get("value", 0.0)),
                            color=p.get("color", "#00F0FF")
                        ) for p in elem_d.get("data", [])
                    ]
                    elem = ChartElement(
                        chart_type=ChartType(elem_d.get("chart_type", "BAR")),
                        data=data_points,
                        max_value=float(elem_d["max_value"]) if elem_d.get("max_value") is not None else None,
                        animation_progress=float(elem_d.get("animation_progress", 1.0)),
                        show_labels=bool(elem_d.get("show_labels", True)),
                        show_values=bool(elem_d.get("show_values", True)),
                        unit_suffix=elem_d.get("unit_suffix", ""),
                        bar_width=float(elem_d.get("bar_width", 40.0)),
                        gap=float(elem_d.get("gap", 20.0))
                    )
                elif ltype == LayerType.HUD and elem_d:
                    elem = HUDElement(
                        hud_type=HUDType(elem_d.get("hud_type", "RETICLE")),
                        primary_color=elem_d.get("primary_color", "#00F0FF"),
                        secondary_color=elem_d.get("secondary_color", "#39FF14"),
                        line_width=float(elem_d.get("line_width", 2.0)),
                        rotation_speed=float(elem_d.get("rotation_speed", 30.0)),
                        scan_progress=float(elem_d.get("scan_progress", 0.0)),
                        telemetry_data=elem_d.get("telemetry_data", {})
                    )
                elif ltype == LayerType.BRAND and elem_d:
                    elem = BrandElement(
                        logo_asset_id=elem_d.get("logo_asset_id"),
                        brand_name=elem_d.get("brand_name", "STUDIO"),
                        tagline=elem_d.get("tagline"),
                        primary_color=elem_d.get("primary_color", "#00F0FF"),
                        accent_color=elem_d.get("accent_color", "#FF007F"),
                        reveal_progress=float(elem_d.get("reveal_progress", 1.0))
                    )
                elif ltype == LayerType.CINEMATIC_OVERLAY and elem_d:
                    elem = CinematicOverlayElement(
                        overlay_type=elem_d.get("overlay_type", "LIGHT_STREAK"),
                        intensity=float(elem_d.get("intensity", 1.0)),
                        color=elem_d.get("color", "#00F0FF"),
                        progress=float(elem_d.get("progress", 0.0))
                    )

                # Animations
                anims: List[KeyframeAnimation] = []
                for a_d in lyr_d.get("animations", []):
                    kfs: List[KeyframePoint] = []
                    for k_d in a_d.get("keyframes", []):
                        kt_raw = k_d.get("offset_time", {"value": 0, "rate": fps})
                        kt = RationalTime(int(kt_raw["value"]), float(kt_raw["rate"]))
                        kfs.append(KeyframePoint(
                            offset_time=kt,
                            value=k_d.get("value", 0.0),
                            easing=EasingType(k_d.get("easing", "LINEAR"))
                        ))
                    anims.append(KeyframeAnimation(
                        target_property=a_d.get("target_property", "opacity"),
                        keyframes=kfs
                    ))

                layers.append(MotionLayer(
                    layer_id=lyr_d.get("layer_id", f"lyr_{uuid.uuid4().hex[:12]}"),
                    name=lyr_d.get("name", "Layer"),
                    z_index=int(lyr_d.get("z_index", 1)),
                    layer_type=ltype,
                    visible=bool(lyr_d.get("visible", True)),
                    transform=transform,
                    element=elem,
                    animations=anims
                ))

            scenes.append(MotionScene(
                scene_id=scn_d.get("scene_id", f"scn_{uuid.uuid4().hex[:12]}"),
                name=scn_d.get("name", "Scene"),
                start_time=st,
                duration=sd,
                layers=layers
            ))

        return cls(
            composition_id=data.get("composition_id", f"cmp_{uuid.uuid4().hex[:12]}"),
            project_id=data.get("project_id", "default_project"),
            name=data.get("name", "Motion Composition"),
            resolution=res,
            fps=fps,
            duration=duration,
            background=bg,
            scenes=scenes,
            metadata=data.get("metadata", {})
        )
