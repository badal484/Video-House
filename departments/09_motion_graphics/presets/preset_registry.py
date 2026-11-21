"""
Motion Graphics Preset Registry.
Provides a collection of production-ready, parameterized motion graphics presets.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.composition_models import (
    BackgroundConfig, BackgroundType, MotionComposition, MotionScene, RenderConfig
)
from ..components.kinetic_text import KineticTextBuilder
from ..components.titles import TitleBuilder
from ..components.infographics import InfographicsBuilder
from ..components.brand_animation import BrandBuilder
from ..components.hud_elements import HUDBuilder
from ..components.cinematic_elements import CinematicOverlayBuilder
from core.timeline.time_model import RationalTime


@dataclass
class MotionPreset:
    preset_id: str
    name: str
    category: str
    description: str
    default_duration: RationalTime
    supported_aspect_ratios: List[str] = field(default_factory=lambda: ["16:9", "9:16", "1:1"])
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    factory_fn: Optional[Callable[[Dict[str, Any]], MotionComposition]] = None


class PresetRegistry:
    """Registry managing configurable motion graphics presets."""

    def __init__(self):
        self._presets: Dict[str, MotionPreset] = {}
        self._register_default_presets()

    def register(self, preset: MotionPreset) -> None:
        self._presets[preset.preset_id] = preset

    def get(self, preset_id: str) -> Optional[MotionPreset]:
        return self._presets.get(preset_id)

    def list_presets(self, category: Optional[str] = None) -> List[MotionPreset]:
        if category:
            return [p for p in self._presets.values() if p.category.lower() == category.lower()]
        return list(self._presets.values())

    def instantiate(self, preset_id: str, params: Dict[str, Any]) -> MotionComposition:
        """Instantiates a composition from a registered preset using provided parameters."""
        preset = self.get(preset_id)
        if not preset:
            raise KeyError(f"Preset '{preset_id}' not found in registry.")
        if not preset.factory_fn:
            raise ValueError(f"Preset '{preset_id}' has no factory function.")
        return preset.factory_fn(params)

    def _register_default_presets(self) -> None:
        # 1. Kinetic Typewriter
        def _build_typewriter(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Typewriter Sequence",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layer = KineticTextBuilder.create_typewriter_layer(
                text=params.get("text", "INTELLIGENT EDITORIAL PIPELINE ACTIVE_"),
                duration=dur,
                font_family=params.get("font_family", "Roboto Mono"),
                font_size=float(params.get("font_size", 44.0)),
                fill_color=params.get("color", "#00F0FF"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Main Scene", start_time=RationalTime(0, fps), duration=dur, layers=[layer]))
            return comp

        self.register(MotionPreset(
            preset_id="preset_kinetic_typewriter",
            name="Kinetic Typewriter",
            category="Typography",
            description="Classic typewriter text with glowing blinking cursor.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"text": "str", "font_size": "float", "color": "str"},
            factory_fn=_build_typewriter
        ))

        # 2. Cinematic Hero Title
        def _build_cinematic_title(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 5.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Cinematic Hero Title",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layers = TitleBuilder.create_cinematic_title_layers(
                main_title=params.get("title", "UNIVERSAL STUDIO"),
                subtitle=params.get("subtitle", "AN AUTONOMOUS CREATIVE PRODUCTION"),
                font_family=params.get("font_family", "Playfair Display"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0 - 20.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Title Scene", start_time=RationalTime(0, fps), duration=dur, layers=layers))
            return comp

        self.register(MotionPreset(
            preset_id="preset_title_cinematic_hero",
            name="Cinematic Hero Title",
            category="Titles",
            description="Elegant film title with slow zoom and glowing typography.",
            default_duration=RationalTime(120, 24.0),
            parameters_schema={"title": "str", "subtitle": "str"},
            factory_fn=_build_cinematic_title
        ))

        # 3. Documentary Lower Third
        def _build_lower_third(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Documentary Lower Third",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layers = TitleBuilder.create_lower_third_layers(
                name=params.get("name", "DR. ELENA VANCE"),
                role=params.get("role", "CHIEF RESEARCH SCIENTIST"),
                accent_color=params.get("accent_color", "#00F0FF"),
                pos=(params.get("pos_x", 240.0), params.get("pos_y", 840.0)),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Lower Third Scene", start_time=RationalTime(0, fps), duration=dur, layers=layers))
            return comp

        self.register(MotionPreset(
            preset_id="preset_lower_third_documentary",
            name="Documentary Lower Third",
            category="Lower Thirds",
            description="Clean two-line nameplate with animated vertical accent line.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"name": "str", "role": "str", "accent_color": "str"},
            factory_fn=_build_lower_third
        ))

        # 4. Animated Bar Chart
        def _build_bar_chart(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Animated Bar Chart",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            labels = params.get("labels", ["Q1", "Q2", "Q3", "Q4"])
            values = params.get("values", [45.0, 78.0, 62.0, 95.0])
            layer = InfographicsBuilder.create_bar_chart_layer(
                labels=labels,
                values=values,
                unit_suffix=params.get("unit_suffix", "M"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Chart Scene", start_time=RationalTime(0, fps), duration=dur, layers=[layer]))
            return comp

        self.register(MotionPreset(
            preset_id="preset_chart_animated_bar",
            name="Animated Bar Chart",
            category="Infographics",
            description="Dynamic growing vertical bars with value labels.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"labels": "list[str]", "values": "list[float]"},
            factory_fn=_build_bar_chart
        ))

        # 5. Progress Ring
        def _build_progress_ring(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 3.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Progress Ring",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layer = InfographicsBuilder.create_progress_ring_layer(
                target_percentage=float(params.get("percentage", 85.0)),
                label=params.get("label", "EFFICIENCY"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Ring Scene", start_time=RationalTime(0, fps), duration=dur, layers=[layer]))
            return comp

        self.register(MotionPreset(
            preset_id="preset_chart_progress_ring",
            name="Progress Ring",
            category="Infographics",
            description="Circular animated progress sweep with center percentage counter.",
            default_duration=RationalTime(72, 24.0),
            parameters_schema={"percentage": "float", "label": "str"},
            factory_fn=_build_progress_ring
        ))

        # 6. Brand Logo Assembly
        def _build_brand_reveal(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Brand Logo Assembly",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layers = BrandBuilder.create_logo_reveal_layers(
                brand_name=params.get("brand_name", "QUANTUM"),
                tagline=params.get("tagline", "FUTURE COMPUTING"),
                primary_color=params.get("primary_color", "#00F0FF"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Brand Scene", start_time=RationalTime(0, fps), duration=dur, layers=layers))
            return comp

        self.register(MotionPreset(
            preset_id="preset_brand_shape_reveal",
            name="Brand Shape Assembly",
            category="Brand",
            description="Geometric shape assembly and wordmark appearance.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"brand_name": "str", "tagline": "str"},
            factory_fn=_build_brand_reveal
        ))

        # 7. HUD Targeting Reticle
        def _build_hud_reticle(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="HUD Targeting Reticle",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layer = HUDBuilder.create_targeting_reticle_layer(
                primary_color=params.get("color", "#00F0FF"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="HUD Scene", start_time=RationalTime(0, fps), duration=dur, layers=[layer]))
            return comp

        self.register(MotionPreset(
            preset_id="preset_hud_targeting_reticle",
            name="HUD Targeting Reticle",
            category="HUD",
            description="Cybernetic rotating reticle with telemetry indicators.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"color": "str"},
            factory_fn=_build_hud_reticle
        ))

        # 8. Multilingual Indic / Devanagari Headline
        def _build_multilingual_headline(params: Dict[str, Any]) -> MotionComposition:
            fps = float(params.get("fps", 24.0))
            dur_sec = float(params.get("duration_sec", 4.0))
            dur = RationalTime(int(round(dur_sec * fps)), fps)
            comp = MotionComposition(
                name="Multilingual Indic Headline",
                resolution=tuple(params.get("resolution", (1920, 1080))),
                fps=fps,
                duration=dur,
                background=BackgroundConfig(type=BackgroundType.TRANSPARENT)
            )
            layer = KineticTextBuilder.create_typewriter_layer(
                text=params.get("text", "नमस्ते भारत - सार्वभौमिक स्टूडियो"),
                duration=dur,
                font_family="Noto Sans Devanagari",
                font_size=float(params.get("font_size", 52.0)),
                fill_color=params.get("color", "#FFE600"),
                pos=(comp.resolution[0] / 2.0, comp.resolution[1] / 2.0),
                fps=fps
            )
            comp.scenes.append(MotionScene(name="Indic Scene", start_time=RationalTime(0, fps), duration=dur, layers=[layer]))
            return comp

        self.register(MotionPreset(
            preset_id="preset_multilingual_headline",
            name="Multilingual Indic Headline",
            category="Typography",
            description="Typewriter headline supporting Hindi / Devanagari complex script shaping.",
            default_duration=RationalTime(96, 24.0),
            parameters_schema={"text": "str", "font_size": "float"},
            factory_fn=_build_multilingual_headline
        ))
