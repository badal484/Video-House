"""
Color Restoration Service Implementation for Department 16.
Implements the IColorRestoration contract and provides high-level facade methods
for color grading, color management, AI colorist assistant, reference matching, and video restoration.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import numpy as np

from .interface import IColorRestoration, ColorRestorationRequest, ColorRestorationResponse
from .core.models import (
    ColorSpace, GradingGraph, RestorationParameters, RestorationType, QualityReviewState
)
from .color_management.color_manager import ColorManager
from .grading.grading_engine import GradingEngine
from .lut.lut_manager import LUTManager
from .ai_colorist.ai_colorist_assistant import AIColoristAssistant
from .matching.reference_matcher import ReferenceMatcher
from .restoration.restoration_pipeline import RestorationPipeline
from .super_resolution.upscaler import SuperResolutionEngine
from .hdr.tone_mapper import ToneMapper
from .qc.color_qc import ColorQualityController
from .qc.restoration_qc import RestorationQualityController
from .integrations.timeline_bridge import TimelineColorBridge
from .integrations.director_bridge import DirectorColorBridge
from .integrations.asset_bridge import AssetStoreBridge
from .integrations.generation_bridge import GeneratedMediaColorBridge


class ColorRestorationService(IColorRestoration):
    """
    Main Service implementation for Department 16: Color & Restoration.
    """

    def __init__(self, ocio_config_path: Optional[str] = None):
        self.color_manager = ColorManager(ocio_config_path)
        self.grading_engine = GradingEngine()
        self.lut_manager = LUTManager()
        self.ai_colorist = AIColoristAssistant()
        self.reference_matcher = ReferenceMatcher()
        self.restoration_pipeline = RestorationPipeline()
        self.upscaler = SuperResolutionEngine()
        self.tone_mapper = ToneMapper()
        self.color_qc = ColorQualityController()
        self.restoration_qc = RestorationQualityController()
        self.timeline_bridge = TimelineColorBridge()
        self.director_bridge = DirectorColorBridge()
        self.asset_bridge = AssetStoreBridge()
        self.generation_bridge = GeneratedMediaColorBridge(self.color_manager)

    async def execute(self, request: ColorRestorationRequest) -> ColorRestorationResponse:
        """
        Executes a high-level color grading or restoration job requested by an agent or user.
        """
        task = request.parameters.get("task", "health_check")
        produced_ids: List[UUID] = []

        if task == "grade_image":
            # Apply grading graph to provided image array
            img_arr = request.parameters.get("image")
            graph_data = request.parameters.get("graph")
            if img_arr is not None and graph_data is not None:
                graph = GradingGraph.model_validate(graph_data) if isinstance(graph_data, dict) else graph_data
                source_cs = ColorSpace(request.parameters.get("source_color_space", "rec709"))
                target_cs = ColorSpace(request.parameters.get("target_color_space", "rec709"))

                # 1. IDT to ACEScg
                acescg = self.color_manager.to_linear_acescg(img_arr, source_cs=source_cs)
                # 2. Apply Grading DAG
                graded_acescg = self.grading_engine.apply_graph(acescg, graph)
                # 3. ODT to target display
                out_img = self.color_manager.from_linear_acescg(graded_acescg, target_cs=target_cs)

                return ColorRestorationResponse(
                    success=True,
                    message="Color grading graph executed successfully.",
                    data={"output_shape": list(out_img.shape), "result_array": out_img}
                )

        elif task == "restore_frames":
            frames = request.parameters.get("frames", [])
            tasks_data = request.parameters.get("restoration_tasks", [])
            tasks = [RestorationParameters.model_validate(t) if isinstance(t, dict) else t for t in tasks_data]
            restored = self.restoration_pipeline.process_frames(frames, tasks)
            return ColorRestorationResponse(
                success=True,
                message=f"Restored {len(restored)} frames across {len(tasks)} filter stages.",
                data={"restored_frame_count": len(restored)}
            )

        return ColorRestorationResponse(
            success=True,
            message="Department 16 Color & Restoration service operational.",
            data={"status": "READY", "project_id": str(request.project_id)}
        )

    def health_check(self) -> bool:
        """Verifies underlying tooling, color models, and math engines are ready."""
        try:
            # Test color matrix conversion
            test_arr = np.ones((4, 4, 3), dtype=np.float32) * 0.5
            acescg = self.color_manager.to_linear_acescg(test_arr, ColorSpace.REC709)
            rec709 = self.color_manager.from_linear_acescg(acescg, ColorSpace.REC709)
            assert rec709.shape == (4, 4, 3)
            return True
        except Exception:
            return False
