"""
Motion Graphics Renderer Router.
Selects optimal rendering engine based on composition element complexity, performance, and format.
"""
from typing import Dict, Optional
from ..renderers.base import IMotionRenderer
from ..renderers.svg_vector_renderer import SVGVectorRenderer
from ..renderers.canvas_renderer import CanvasRasterRenderer
from ..core.composition_models import (
    LayerType, MotionComposition, RenderConfig
)


class MotionRendererRouter:
    """
    Intelligent routing between SVG Vector and Canvas Raster engines.
    """

    def __init__(self):
        self._svg_renderer = SVGVectorRenderer()
        self._canvas_renderer = CanvasRasterRenderer()

    def select_renderer(self, composition: MotionComposition) -> IMotionRenderer:
        """
        Inspects layer types in composition to choose the optimal engine.
        - Text, Shapes, Charts, Vector Overlays -> SVGVectorRenderer (Crisp, vector precision).
        - High-density particles, pixel-heavy HUDs, raster effects -> CanvasRasterRenderer.
        """
        for scene in composition.scenes:
            for layer in scene.layers:
                # If layer contains HUD or particles, canvas raster provides high-speed rasterization
                if layer.layer_type in (LayerType.HUD, LayerType.CINEMATIC_OVERLAY):
                    return self._canvas_renderer

        # Default to SVG vector renderer for pristine typography and infographics
        return self._svg_renderer

    def render(
        self,
        composition: MotionComposition,
        output_path: str,
        config: Optional[RenderConfig] = None,
        force_engine: Optional[str] = None
    ) -> str:
        """Dispatches render job to the selected or forced engine."""
        if force_engine == "canvas":
            renderer = self._canvas_renderer
        elif force_engine == "svg":
            renderer = self._svg_renderer
        else:
            renderer = self.select_renderer(composition)

        return renderer.render_video(composition, output_path, config)
