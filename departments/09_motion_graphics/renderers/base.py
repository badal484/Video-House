"""
Base Motion Renderer Interface.
Defines abstract contract for deterministic frame and video rendering engines.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..core.composition_models import MotionComposition, RenderConfig
from core.timeline.time_model import RationalTime


class IMotionRenderer(ABC):
    """Abstract interface for all motion graphics rendering backends."""

    @abstractmethod
    def render_frame_svg(self, composition: MotionComposition, current_time: RationalTime) -> str:
        """Renders a single frame at current_time as an SVG XML string."""
        pass

    @abstractmethod
    def render_frame_raster(self, composition: MotionComposition, current_time: RationalTime) -> bytes:
        """Renders a single frame at current_time as an RGBA PNG byte buffer."""
        pass

    @abstractmethod
    def render_video(
        self,
        composition: MotionComposition,
        output_path: str,
        config: Optional[RenderConfig] = None
    ) -> str:
        """
        Renders the complete motion composition to an alpha-capable video file or image sequence.
        Returns the absolute path of the rendered output file.
        """
        pass
