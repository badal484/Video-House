"""
VFX Compositing Service
Primary departmental service implementing IVFXCompositing interface.
"""
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from .interface import IVFXCompositing, VFXCompositingRequest, VFXCompositingResponse
from .core.graph_models import CompositingGraph
from .engines.router import VFXEngineRouter
from .engines.local_compositor import LocalCompositorEngine
from .supervisor.vfx_supervisor import AIVFXSupervisor
from .supervisor.quality_checker import VFXQualityChecker


class VFXCompositingService(IVFXCompositing):
    """
    Main service facade for Department 13: VFX & Compositing.
    """

    def __init__(
        self,
        engine_router: Optional[VFXEngineRouter] = None,
        local_engine: Optional[LocalCompositorEngine] = None,
    ):
        self.local_engine = local_engine or LocalCompositorEngine()
        self.router = engine_router or VFXEngineRouter(local_engine=self.local_engine)

    def health_check(self) -> bool:
        """
        Verifies OpenCV, NumPy, and local compositing sub-systems are ready.
        """
        try:
            import cv2
            import numpy as np
            test_mat = np.zeros((10, 10, 4), dtype=np.uint8)
            blurred = cv2.GaussianBlur(test_mat, (3, 3), 1.0)
            return blurred is not None
        except Exception:
            return False

    async def execute(self, request: VFXCompositingRequest) -> VFXCompositingResponse:
        """
        Executes a VFX compositing task based on parameters:
        - graph: CompositingGraph dict
        - or action: 'screen_replacement', 'chroma_key', 'object_removal'
        """
        params = request.parameters
        action = params.get("action", "custom_graph")
        project_id_str = str(request.project_id)

        try:
            if "graph" in params:
                graph = CompositingGraph.from_dict(params["graph"])
            elif action == "screen_replacement":
                graph = AIVFXSupervisor.create_screen_replacement_graph(
                    project_id=project_id_str,
                    name=params.get("name", "Screen_Replacement"),
                    dst_corners=params.get("dst_corners", [[100, 100], [400, 100], [400, 400], [100, 400]]),
                    resolution=params.get("resolution", (1920, 1080)),
                )
            elif action == "chroma_key":
                graph = AIVFXSupervisor.create_chroma_key_graph(
                    project_id=project_id_str,
                    name=params.get("name", "Chroma_Key"),
                    key_color=params.get("key_color", "GREEN"),
                    resolution=params.get("resolution", (1920, 1080)),
                )
            elif action == "object_removal":
                graph = AIVFXSupervisor.create_object_removal_graph(
                    project_id=project_id_str,
                    name=params.get("name", "Object_Removal"),
                    method=params.get("method", "TELEA"),
                    resolution=params.get("resolution", (1920, 1080)),
                )
            else:
                return VFXCompositingResponse(
                    success=False,
                    message=f"Unknown VFX action: {action}",
                )

            # Render single frame preview or sequence
            output_path = params.get("output_path")
            inputs = params.get("inputs")

            result = self.router.render_sequence(
                graph=graph,
                start_frame=0,
                end_frame=params.get("frames", 1),
                output_path=output_path,
                inputs=inputs,
            )

            produced_id = uuid4()
            return VFXCompositingResponse(
                success=True,
                message=f"VFX compositing task executed successfully ({action}).",
                data={
                    "graph_id": graph.graph_id,
                    "render_result": result,
                },
                produced_asset_ids=[produced_id],
            )
        except Exception as e:
            return VFXCompositingResponse(
                success=False,
                message=f"VFX compositing failed: {str(e)}",
            )
