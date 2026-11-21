"""
Core package exports for Department 09 Motion Graphics.
"""
from .composition_models import (
    BackgroundConfig, BackgroundType, BrandElement, ChartDataPoint, ChartElement,
    ChartType, CinematicOverlayElement, EasingType, GraphicElementUnion, HUDElement,
    HUDType, KeyframeAnimation, KeyframePoint, LayerType, MotionComposition,
    MotionLayer, MotionScene, RenderConfig, ShapeElement, TextElement, TextRevealMode,
    Transform2D
)
from .time_sync import TimeSynchronizer
from .typography import TypographyEngine
from .animation_engine import AnimationEngine
from .design_validator import DesignValidator

__all__ = [
    "BackgroundConfig",
    "BackgroundType",
    "BrandElement",
    "ChartDataPoint",
    "ChartElement",
    "ChartType",
    "CinematicOverlayElement",
    "EasingType",
    "GraphicElementUnion",
    "HUDElement",
    "HUDType",
    "KeyframeAnimation",
    "KeyframePoint",
    "LayerType",
    "MotionComposition",
    "MotionLayer",
    "MotionScene",
    "RenderConfig",
    "ShapeElement",
    "TextElement",
    "TextRevealMode",
    "Transform2D",
    "TimeSynchronizer",
    "TypographyEngine",
    "AnimationEngine",
    "DesignValidator",
]
