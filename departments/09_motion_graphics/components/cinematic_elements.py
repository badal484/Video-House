"""
Cinematic Graphic Elements and Overlays.
Provides light streaks, geometric transitions, particles, and abstract backgrounds.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    CinematicOverlayElement, EasingType, KeyframeAnimation, KeyframePoint, LayerType,
    MotionLayer, Transform2D
)
from core.timeline.time_model import RationalTime


class CinematicOverlayBuilder:
    """Factory for building cinematic optical and geometric overlays."""

    @staticmethod
    def create_light_streak_layer(
        color: str = "#00F0FF",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates an anamorphic light streak sweeping horizontally across the screen."""
        elem = CinematicOverlayElement(
            overlay_type="LIGHT_STREAK",
            intensity=1.0,
            color=color,
            progress=0.0
        )

        anim_x = KeyframeAnimation(
            target_property="x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=-200.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.5 * fps)), fps), value=2120.0, easing=EasingType.EASE_IN_OUT),
            ]
        )

        return MotionLayer(
            name="Anamorphic Light Streak",
            layer_type=LayerType.CINEMATIC_OVERLAY,
            transform=Transform2D(x=-200.0, y=pos[1], opacity=0.85),
            element=elem,
            animations=[anim_x]
        )

    @staticmethod
    def create_geometric_wipe_layer(
        color: str = "#0F172A",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates a dynamic angled geometric wipe transition."""
        elem = CinematicOverlayElement(
            overlay_type="GEOMETRIC_WIPE",
            intensity=1.0,
            color=color,
            progress=0.0
        )

        anim_p = KeyframeAnimation(
            target_property="progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.0 * fps)), fps), value=1.0, easing=EasingType.EASE_IN_OUT),
            ]
        )

        return MotionLayer(
            name="Geometric Wipe",
            layer_type=LayerType.CINEMATIC_OVERLAY,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=elem,
            animations=[anim_p]
        )
