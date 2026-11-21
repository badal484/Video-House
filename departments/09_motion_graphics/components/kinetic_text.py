"""
Kinetic Typography Components.
Provides pre-assembled kinetic text reveal layers and animations.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    EasingType, KeyframeAnimation, KeyframePoint, LayerType, MotionLayer,
    TextElement, TextRevealMode, Transform2D
)
from core.timeline.time_model import RationalTime


class KineticTextBuilder:
    """Factory for building kinetic text layers and animations."""

    @staticmethod
    def create_typewriter_layer(
        text: str,
        duration: RationalTime,
        font_family: str = "Roboto Mono",
        font_size: float = 48.0,
        fill_color: str = "#00F0FF",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates a typewriter text layer with animated cursor."""
        element = TextElement(
            text=text,
            font_family=font_family,
            font_size=font_size,
            fill_color=fill_color,
            text_align="center",
            reveal_mode=TextRevealMode.TYPEWRITER,
            show_cursor=True,
            cursor_color="#00F0FF"
        )

        anim = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(int(round(0.2 * fps)), fps), value=1.0, easing=EasingType.LINEAR),
            ]
        )

        return MotionLayer(
            name="Kinetic Typewriter",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=element,
            animations=[anim]
        )

    @staticmethod
    def create_word_pop_layer(
        text: str,
        duration: RationalTime,
        font_family: str = "Montserrat",
        font_size: float = 64.0,
        fill_color: str = "#FFFFFF",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates a punchy word-by-word reveal layer with spring scale animation."""
        element = TextElement(
            text=text,
            font_family=font_family,
            font_size=font_size,
            fill_color=fill_color,
            text_align="center",
            reveal_mode=TextRevealMode.WORD_BY_WORD
        )

        anim_scale = KeyframeAnimation(
            target_property="scale_x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.8, easing=EasingType.SPRING),
                KeyframePoint(offset_time=RationalTime(int(round(0.3 * fps)), fps), value=1.0, easing=EasingType.SPRING)
            ]
        )
        anim_scale_y = KeyframeAnimation(
            target_property="scale_y",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.8, easing=EasingType.SPRING),
                KeyframePoint(offset_time=RationalTime(int(round(0.3 * fps)), fps), value=1.0, easing=EasingType.SPRING)
            ]
        )

        return MotionLayer(
            name="Word Pop Typography",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=element,
            animations=[anim_scale, anim_scale_y]
        )
