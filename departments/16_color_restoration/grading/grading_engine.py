"""
Grading Engine DAG Orchestrator for Department 16.
Executes an ordered or DAG-structured GradingGraph across image frames in linear float32 space.
"""
import numpy as np
from ..core.models import GradingGraph, GradingNodeType
from .primary_corrector import PrimaryCorrector
from .curves_corrector import CurvesCorrector
from .secondary_qualifier import SecondaryQualifier
from .power_windows import PowerWindowManager
from .creative_looks import CreativeLooksEngine


class GradingEngine:
    """
    Executes a structured node graph of color grading operations.
    """

    @classmethod
    def apply_graph(cls, image: np.ndarray, graph: GradingGraph) -> np.ndarray:
        """
        Executes all enabled nodes in the GradingGraph on an input float32 image array.
        """
        current_img = image.astype(np.float32).copy()

        for node in graph.nodes:
            if not node.enabled or node.opacity <= 0.0:
                continue

            node_out = current_img.copy()

            if node.node_type == GradingNodeType.PRIMARY and node.primary_params:
                node_out = PrimaryCorrector.apply_primary(current_img, node.primary_params)

            elif node.node_type == GradingNodeType.CURVES and node.curves_params:
                node_out = CurvesCorrector.apply_curves(current_img, node.curves_params)

            elif node.node_type == GradingNodeType.SECONDARY_QUALIFIER and node.qualifier_params:
                node_out = SecondaryQualifier.apply_qualifier(current_img, node.qualifier_params)

            elif node.node_type == GradingNodeType.CREATIVE_LOOK and node.look_preset_name:
                node_out = CreativeLooksEngine.apply_look(current_img, node.look_preset_name, intensity=node.opacity)

            # Spatial Power Window masking if attached to node
            if node.power_window_params and node.power_window_params.enabled:
                h, w = current_img.shape[:2]
                pw_mask = PowerWindowManager.generate_window_mask(h, w, node.power_window_params)[:, :, np.newaxis]
                node_out = current_img * (1.0 - pw_mask) + node_out * pw_mask

            # Apply node-level opacity blending
            if node.opacity < 1.0 and node.node_type != GradingNodeType.CREATIVE_LOOK:
                current_img = current_img * (1.0 - node.opacity) + node_out * node.opacity
            else:
                current_img = node_out

        return current_img
