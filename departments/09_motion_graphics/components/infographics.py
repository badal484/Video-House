"""
Infographics and Data Visualization Components.
Provides animated bar charts, progress rings, line graphs, and numerical counters.
"""
from typing import Dict, List, Optional, Tuple
from ..core.composition_models import (
    ChartDataPoint, ChartElement, ChartType, EasingType, KeyframeAnimation,
    KeyframePoint, LayerType, MotionLayer, TextElement, Transform2D
)
from core.timeline.time_model import RationalTime


class InfographicsBuilder:
    """Factory for building animated data visualization components."""

    @staticmethod
    def create_bar_chart_layer(
        labels: List[str],
        values: List[float],
        colors: Optional[List[str]] = None,
        unit_suffix: str = "",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates an animated vertical bar chart growing from bottom up."""
        data_points = []
        default_colors = ["#00F0FF", "#39FF14", "#FF007F", "#FFE600", "#7928CA"]

        for i, (l, v) in enumerate(zip(labels, values)):
            c = colors[i % len(colors)] if colors else default_colors[i % len(default_colors)]
            data_points.append(ChartDataPoint(label=l, value=float(v), color=c))

        chart = ChartElement(
            chart_type=ChartType.BAR,
            data=data_points,
            max_value=max(values) * 1.15 if values else 100.0,
            animation_progress=0.0,
            unit_suffix=unit_suffix,
            bar_width=45.0,
            gap=25.0
        )

        anim_progress = KeyframeAnimation(
            target_property="animation_progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.2 * fps)), fps), value=1.0, easing=EasingType.EASE_OUT),
            ]
        )

        return MotionLayer(
            name="Animated Bar Chart",
            layer_type=LayerType.CHART,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=chart,
            animations=[anim_progress]
        )

    @staticmethod
    def create_progress_ring_layer(
        target_percentage: float,
        label: str = "COMPLETION",
        color: str = "#00F0FF",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates a circular animated progress ring with center percentage."""
        data_points = [
            ChartDataPoint(label=label, value=min(100.0, max(0.0, target_percentage)), color=color)
        ]

        chart = ChartElement(
            chart_type=ChartType.PROGRESS_RING,
            data=data_points,
            max_value=100.0,
            animation_progress=0.0,
            unit_suffix="%"
        )

        anim_progress = KeyframeAnimation(
            target_property="animation_progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_IN_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.5 * fps)), fps), value=1.0, easing=EasingType.EASE_IN_OUT),
            ]
        )

        return MotionLayer(
            name="Animated Progress Ring",
            layer_type=LayerType.CHART,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=chart,
            animations=[anim_progress]
        )

    @staticmethod
    def create_metric_counter_layer(
        target_value: float,
        unit: str = "",
        label: str = "TOTAL REVENUE",
        pos: Tuple[float, float] = (960.0, 540.0),
        fps: float = 24.0
    ) -> MotionLayer:
        """Creates an animated metric counter counting from 0 up to target_value."""
        data_points = [ChartDataPoint(label=label, value=target_value, color="#00F0FF")]

        chart = ChartElement(
            chart_type=ChartType.COUNTER,
            data=data_points,
            max_value=target_value,
            animation_progress=0.0,
            unit_suffix=unit
        )

        anim = KeyframeAnimation(
            target_property="animation_progress",
            keyframes=[
                KeyframePoint(offset_time=RationalTime(0, fps), value=0.0, easing=EasingType.EASE_OUT),
                KeyframePoint(offset_time=RationalTime(int(round(1.5 * fps)), fps), value=1.0, easing=EasingType.EASE_OUT),
            ]
        )

        return MotionLayer(
            name="Animated Metric Counter",
            layer_type=LayerType.CHART,
            transform=Transform2D(x=pos[0], y=pos[1], opacity=1.0),
            element=chart,
            animations=[anim]
        )
