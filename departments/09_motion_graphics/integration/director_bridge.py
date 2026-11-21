"""
AI Director Creative Motion Bridge.
Translates Part 04 Creative Briefs, Planned Shots, and natural language instructions
into validated MotionComposition instances.
"""
from typing import Any, Dict, Optional, Tuple
from ..core.composition_models import (
    BackgroundConfig, BackgroundType, MotionComposition, MotionScene, RenderConfig
)
from ..presets.preset_registry import PresetRegistry
from ..core.design_validator import DesignValidator
from core.timeline.time_model import RationalTime


class DirectorMotionBridge:
    """
    Translates AI Director instructions into structured motion compositions.
    """

    def __init__(self, preset_registry: Optional[PresetRegistry] = None):
        self.presets = preset_registry or PresetRegistry()

    def create_lower_third_from_prompt(
        self,
        name: str,
        role: str,
        primary_color: str = "#00F0FF",
        duration_sec: float = 4.0,
        resolution: Tuple[int, int] = (1920, 1080),
        fps: float = 24.0
    ) -> MotionComposition:
        """Constructs an approved lower third composition."""
        params = {
            "name": name,
            "role": role,
            "accent_color": primary_color,
            "duration_sec": duration_sec,
            "resolution": resolution,
            "fps": fps
        }
        comp = self.presets.instantiate("preset_lower_third_documentary", params)
        DesignValidator.validate_composition(comp)
        return comp

    def create_title_from_prompt(
        self,
        title: str,
        subtitle: Optional[str] = None,
        duration_sec: float = 5.0,
        resolution: Tuple[int, int] = (1920, 1080),
        fps: float = 24.0
    ) -> MotionComposition:
        """Constructs an approved cinematic title composition."""
        params = {
            "title": title,
            "subtitle": subtitle or "",
            "duration_sec": duration_sec,
            "resolution": resolution,
            "fps": fps
        }
        comp = self.presets.instantiate("preset_title_cinematic_hero", params)
        DesignValidator.validate_composition(comp)
        return comp

    def create_infographic_from_data(
        self,
        labels: list,
        values: list,
        chart_type: str = "BAR",
        unit_suffix: str = "",
        duration_sec: float = 4.0,
        resolution: Tuple[int, int] = (1920, 1080),
        fps: float = 24.0
    ) -> MotionComposition:
        """Constructs an infographic composition based on supplied data points."""
        if chart_type.upper() == "PROGRESS":
            val = float(values[0]) if values else 75.0
            params = {
                "percentage": val,
                "label": labels[0] if labels else "EFFICIENCY",
                "duration_sec": duration_sec,
                "resolution": resolution,
                "fps": fps
            }
            return self.presets.instantiate("preset_chart_progress_ring", params)
        else:
            params = {
                "labels": labels,
                "values": values,
                "unit_suffix": unit_suffix,
                "duration_sec": duration_sec,
                "resolution": resolution,
                "fps": fps
            }
            return self.presets.instantiate("preset_chart_animated_bar", params)
