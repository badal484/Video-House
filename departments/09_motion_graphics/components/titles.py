"""
Editorial Titles and Lower Thirds Components.
Provides cinematic opening titles, film credits, documentary lower thirds, and quote cards.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    EasingType, KeyframeAnimation, KeyframePoint, LayerType, MotionLayer,
    ShapeElement, TextElement, TextRevealMode, Transform2D
)
from core.timeline.time_model import RationalTime


class TitleBuilder:
    """Factory for building editorial titles and lower thirds."""

    @staticmethod
    def create_cinematic_title_layers(
        main_title: str,
        subtitle: Optional[str] = None,
        font_family: str = "Playfair Display",
        pos: Tuple[float, float] = (960.0, 500.0),
        fps: float = 24.0
    ) -> List[MotionLayer]:
        """Creates a cinematic slow-zoom title with subtle fade-in."""
        layers: List[MotionLayer] = []

        main_elem = TextElement(
            text=main_title.upper(),
            font_family=font_family,
            font_size=72.0,
            font_weight="bold",
            fill_color="#FFFFFF",
            letter_spacing=6.0,
            text_align="center"
        )

        anim_opacity = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.0 * fps)), fps), value=1.0, easing=EasingType.EASE_IN_OUT),
            ]
        )
        anim_scale_x = KeyframeAnimation(
            target_property="scale_x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.95, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(int(round(5.0 * fps)), fps), value=1.05, easing=EasingType.LINEAR),
            ]
        )
        anim_scale_y = KeyframeAnimation(
            target_property="scale_y",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.95, easing=EasingType.LINEAR),
                KeyframePoint(offset_time=RationalTime(int(round(5.0 * fps)), fps), value=1.05, easing=EasingType.LINEAR),
            ]
        )

        layers.append(MotionLayer(
            name="Cinematic Main Title",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=0.0),
            element=main_elem,
            animations=[anim_opacity, anim_scale_x, anim_scale_y]
        ))

        if subtitle:
            sub_elem = TextElement(
                text=subtitle.upper(),
                font_family="Inter",
                font_size=24.0,
                font_weight="regular",
                fill_color="#00F0FF",
                letter_spacing=4.0,
                text_align="center"
            )
            sub_opacity = KeyframeAnimation(
                target_property="opacity",
                keyframes=[
                    KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                    KeyframePoint(offset_time=RationalTime(int(round(0.8 * fps)), fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                    KeyframePoint(offset_time=RationalTime(int(round(1.8 * fps)), fps), value=0.9, easing=EasingType.EASE_IN_OUT),
                ]
            )
            layers.append(MotionLayer(
                name="Cinematic Subtitle",
                layer_type=LayerType.TEXT,
                transform=Transform2D(x=pos[0], y=pos[1] + 80.0, opacity=0.0),
                element=sub_elem,
                animations=[sub_opacity]
            ))

        return layers

    @staticmethod
    def create_lower_third_layers(
        name: str,
        role: str,
        accent_color: str = "#00F0FF",
        pos: Tuple[float, float] = (250.0, 850.0),
        fps: float = 24.0
    ) -> List[MotionLayer]:
        """Creates a modern documentary lower third with accent bar and nameplate."""
        layers: List[MotionLayer] = []

        # Accent Bar Shape
        bar = ShapeElement(
            shape_type="RECTANGLE",
            width=6.0,
            height=70.0,
            fill_color=accent_color,
            stroke_width=0.0,
            corner_radius=2.0
        )
        bar_anim = KeyframeAnimation(
            target_property="scale_y",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.4 * fps)), fps), value=1.0, easing=EasingType.EASE_OUT),
            ]
        )
        layers.append(MotionLayer(
            name="Lower Third Accent Bar",
            layer_type=LayerType.SHAPE,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=bar,
            animations=[bar_anim]
        ))

        # Person Name
        name_elem = TextElement(
            text=name,
            font_family="Montserrat",
            font_size=36.0,
            font_weight="bold",
            fill_color="#FFFFFF",
            text_align="left"
        )
        name_anim = KeyframeAnimation(
            target_property="x",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=pos[0] + 10.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.5 * fps)), fps), value=pos[0] + 30.0, easing=EasingType.EASE_OUT),
            ]
        )
        name_opacity = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.4 * fps)), fps), value=1.0, easing=EasingType.EASE_IN_OUT),
            ]
        )
        layers.append(MotionLayer(
            name="Lower Third Name",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=pos[0] + 30.0, y=pos[1] - 14.0, opacity=0.0),
            element=name_elem,
            animations=[name_anim, name_opacity]
        ))

        # Role / Title
        role_elem = TextElement(
            text=role,
            font_family="Inter",
            font_size=20.0,
            font_weight="regular",
            fill_color="#CCCCCC",
            text_align="left"
        )
        role_opacity = KeyframeAnimation(
            target_property="opacity",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.3 * fps)), fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(0.7 * fps)), fps), value=1.0, easing=EasingType.EASE_IN_OUT),
            ]
        )
        layers.append(MotionLayer(
            name="Lower Third Role",
            layer_type=LayerType.TEXT,
            transform=Transform2D(x=pos[0] + 30.0, y=pos[1] + 24.0, opacity=0.0),
            element=role_elem,
            animations=[role_opacity]
        ))

        return layers
