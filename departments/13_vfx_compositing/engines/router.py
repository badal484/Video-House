"""
VFX Engine Router
Inspects CompositingGraph nodes and dispatches to LocalCompositorEngine or BlenderCompositorEngine.
"""
from typing import Any, Dict, Optional
import numpy as np
from .base import ICompositorEngine
from .local_compositor import LocalCompositorEngine
from .blender_compositor import BlenderCompositorEngine
from ..core.graph_models import CompositingGraph, VFXNodeType


class VFXEngineRouter(ICompositorEngine):
    """
    Dynamically routes compositing requests to the appropriate engine.
    """

    def __init__(
        self,
        local_engine: Optional[LocalCompositorEngine] = None,
        blender_engine: Optional[BlenderCompositorEngine] = None,
    ):
        self.local_engine = local_engine or LocalCompositorEngine()
        self.blender_engine = blender_engine or BlenderCompositorEngine()

    def select_engine(self, graph: CompositingGraph) -> ICompositorEngine:
        """
        Inspects node types: routes 3D passes to Blender, 2D compositions to LocalCompositor.
        """
        requires_3d = False
        for node in graph.nodes:
            if "3d" in node.node_type.value.lower() or node.parameters.get("requires_3d_render"):
                requires_3d = True
                break
        return self.blender_engine if requires_3d else self.local_engine

    def evaluate_frame(
        self,
        graph: CompositingGraph,
        frame_index: int = 0,
        inputs: Optional[Dict[str, np.ndarray]] = None,
    ) -> np.ndarray:
        engine = self.select_engine(graph)
        return engine.evaluate_frame(graph, frame_index=frame_index, inputs=inputs)

    def render_sequence(
        self,
        graph: CompositingGraph,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        output_path: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        engine = self.select_engine(graph)
        return engine.render_sequence(
            graph,
            start_frame=start_frame,
            end_frame=end_frame,
            output_path=output_path,
            inputs=inputs,
        )
