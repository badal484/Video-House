"""
Department 09: Motion Graphics and Typography Studio.
"""
from .interface import (
    IMotionGraphics, MotionGraphicsRequest, MotionGraphicsResponse
)
from .service import MotionGraphicsService
from .core import (
    MotionComposition, MotionScene, MotionLayer, TextElement, ShapeElement,
    ChartElement, HUDElement, BrandElement, RenderConfig
)
from .presets import PresetRegistry, MotionPreset
from .renderers import (
    SVGVectorRenderer, CanvasRasterRenderer, MotionRendererRouter
)
from .integration import (
    TimelineMotionAdapter, DirectorMotionBridge
)

__all__ = [
    "IMotionGraphics",
    "MotionGraphicsRequest",
    "MotionGraphicsResponse",
    "MotionGraphicsService",
    "MotionComposition",
    "MotionScene",
    "MotionLayer",
    "TextElement",
    "ShapeElement",
    "ChartElement",
    "HUDElement",
    "BrandElement",
    "RenderConfig",
    "PresetRegistry",
    "MotionPreset",
    "SVGVectorRenderer",
    "CanvasRasterRenderer",
    "MotionRendererRouter",
    "TimelineMotionAdapter",
    "DirectorMotionBridge",
]
