"""
Technical HUD and Cybernetic Graphic Components.
Provides animated reticles, scan lines, coordinate readouts, and telemetry overlays.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    EasingType, HUDElement, HUDType, KeyframeAnimation, KeyframePoint, LayerType,
    MotionLayer, Transform2D
)
from core.timeline.time_model import RationalTime


class HUDBuilder:
    """Factory for building sci-fi and technical HUD overlays."""

    @staticmethod
    def create_targeting_reticle_layer(
        primary_color: str = "#00F0FF",
        secondary_color: str = "#39FF14",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates an animated rotating targeting reticle with tracking brackets."""
        hud = HUDElement(
            hud_type=HUDType.RETICLE,
            primary_color=primary_color,
            secondary_color=secondary_color,
            rotation_speed=45.0,
            telemetry_data={"SYS": "ONLINE", "LOCK": "ACQUIRED", "DIST": "142.8m"}
        )

        anim_rot = KeyframeAnimation(
            target_property="rotation_deg",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(int(round(4.0 * fps)), fps), value=180.0, easing=EasingType.LINEAR),
            ]
        )

        return MotionLayer(
            name="HUD Targeting Reticle",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.9),
            element=hud,
            animations=[anim_rot]
        )

    @staticmethod
    def create_telemetry_grid_layer(
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates a background cybernetic telemetry grid with scan line."""
        hud = HUDElement(
            hud_type=HUDType.TECH_GRID,
            primary_color="#00F0FF",
            secondary_color="#0A2540",
            scan_progress=0.0,
            telemetry_data={"LAT": "37.7749 N", "LON": "122.4194 W", "ALT": "1284 FT"}
        )

        anim_scan = KeyframeAnimation(
            target_property="scan_progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(int(round(2.0 * fps)), fps), value=1.0, easing=EasingType.LINEAR),
            ]
        )

        return MotionLayer(
            name="HUD Telemetry Grid",
            layer_type=LayerType.HUD,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.8),
            element=hud,
            animations=[anim_scan]
        )
