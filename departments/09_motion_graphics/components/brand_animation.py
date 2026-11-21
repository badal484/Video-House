"""
Brand and Logo Animation Components.
Provides logo reveals, shape-based logo assemblies, and animated wordmarks.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    BrandElement, EasingType, KeyframeAnimation, KeyframePoint, LayerType,
    MotionLayer, Transform2D
)
from core.timeline.time_model import RationalTime


class BrandBuilder:
    """Factory for building animated brand reveals and wordmarks."""

    @staticmethod
    def create_logo_reveal_layers(
        brand_name: str,
        tagline: Optional[str] = None,
        primary_color: str = "#00F0FF",
        accent_color: str = "#FF007F",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> List[MotionLayer]:
        """Creates a high-end geometric shape reveal for a brand mark."""
        layers: List[MotionLayer] = []

        brand = BrandElement(
            brand_name=brand_name,
            tagline=tagline,
            primary_color=primary_color,
            accent_color=accent_color,
            reveal_progress=0.0
        )

        anim_reveal = KeyframeAnimation(
            target_property="reveal_progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.2 * fps)), fps), value=1.0, easing=EasingType.EASE_OUT),
            ]
        )
        anim_scale = KeyframeAnimation(
            target_property="scale_x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.8, easing=EasingType.SPRING),
                KeyframePoint(offset_time=RationalTime(int(round(1.0 * fps)), fps), value=1.0, easing=EasingType.SPRING),
            ]
        )
        anim_scale_y = KeyframeAnimation(
            target_property="scale_y",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.8, easing=EasingType.SPRING),
                KeyframePoint(offset_time=RationalTime(int(round(1.0 * fps)), fps), value=1.0, easing=EasingType.SPRING),
            ]
        )

        layers.append(MotionLayer(
            name="Brand Logo Assembly",
            layer_type=LayerType.BRAND,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=brand,
            animations=[anim_reveal, anim_scale, anim_scale_y]
        ))

        return layers
