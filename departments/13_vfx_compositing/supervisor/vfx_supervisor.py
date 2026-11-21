"""
AI VFX Supervisor
Analyzes creative briefs and shot plates, then constructs production-grade CompositingGraphs.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import numpy as np

from ..core.graph_models import (
    CompositingGraph,
    VFXNode,
    VFXNodeType,
    NodePort,
    PortDataType,
    BlendMode,
)
from ..core.vfx_project_models import VFXShotTask, VFXType, VFXTaskStatus


class AIVFXSupervisor:
    """
    Creative reasoning and node graph synthesis engine for visual effects shots.
    """

    @staticmethod
    def create_screen_replacement_graph(
        project_id: str,
        name: str,
        dst_corners: List[List[float]],
        plate_asset_id: str = "plate_source",
        graphic_asset_id: str = "ui_graphic",
        resolution: Tuple[int, int] = (1920, 1080),
        add_glow: bool = True,
        light_wrap: bool = True,
    ) -> CompositingGraph:
        """
        Recipe: 4-Point Planar Screen Replacement with Perspective Warp, Screen Bleed, and Glow.
        """
        w, h = resolution
        graph = CompositingGraph(
            graph_id=str(uuid4()),
            project_id=project_id,
            name=name,
            resolution_w=w,
            resolution_h=h,
        )

        # 1. Plate Node
        node_plate = VFXNode(
            node_id="node_plate",
            node_type=VFXNodeType.MEDIA_INPUT,
            name="Source Plate",
            parameters={"asset_id": plate_asset_id},
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_plate)

        # 2. UI Graphic Node
        node_ui = VFXNode(
            node_id="node_ui",
            node_type=VFXNodeType.MEDIA_INPUT,
            name="Screen Graphic",
            parameters={"asset_id": graphic_asset_id},
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_ui)

        # 3. Planar Warp Node
        node_warp = VFXNode(
            node_id="node_warp",
            node_type=VFXNodeType.PLANAR_WARP,
            name="Corner Pin Warp",
            parameters={"dst_corners": dst_corners, "width": w, "height": h},
            inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_warp)
        graph.add_edge("node_ui", "output", "node_warp", "source")

        current_fg_id = "node_warp"

        # 4. Optional Screen Glow
        if add_glow:
            node_glow = VFXNode(
                node_id="node_glow",
                node_type=VFXNodeType.CINEMATIC_FX,
                name="Screen Glow",
                parameters={"type": "GLOW", "threshold": 0.6, "radius": 20, "intensity": 0.4},
                inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
                outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
            )
            graph.add_node(node_glow)
            graph.add_edge(current_fg_id, "output", "node_glow", "source")
            current_fg_id = "node_glow"

        # 5. Merge Node (Over)
        node_merge = VFXNode(
            node_id="node_merge",
            node_type=VFXNodeType.MERGE,
            name="Composite Merge",
            parameters={"blend_mode": BlendMode.OVER.value},
            inputs=[
                NodePort("background", PortDataType.IMAGE_RGBA, "Background", is_input=True),
                NodePort("foreground", PortDataType.IMAGE_RGBA, "Foreground", is_input=True),
            ],
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_merge)
        graph.add_edge("node_plate", "output", "node_merge", "background")
        graph.add_edge(current_fg_id, "output", "node_merge", "foreground")

        # 6. Terminal Output Node
        node_out = VFXNode(
            node_id="node_out",
            node_type=VFXNodeType.MEDIA_OUTPUT,
            name="Master Output",
            inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
        )
        graph.add_node(node_out)
        graph.add_edge("node_merge", "output", "node_out", "source")

        return graph

    @staticmethod
    def create_chroma_key_graph(
        project_id: str,
        name: str,
        key_color: str = "GREEN",
        plate_asset_id: str = "green_plate",
        bg_asset_id: str = "new_background",
        resolution: Tuple[int, int] = (1920, 1080),
        light_wrap: bool = True,
    ) -> CompositingGraph:
        """
        Recipe: Chroma Key Extraction, Despill, Light Wrap, and Background Composite.
        """
        w, h = resolution
        graph = CompositingGraph(
            graph_id=str(uuid4()),
            project_id=project_id,
            name=name,
            resolution_w=w,
            resolution_h=h,
        )

        # 1. Plate Node
        node_plate = VFXNode(
            node_id="node_plate",
            node_type=VFXNodeType.MEDIA_INPUT,
            name="Green Screen Plate",
            parameters={"asset_id": plate_asset_id},
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_plate)

        # 2. Keyer Node
        node_keyer = VFXNode(
            node_id="node_keyer",
            node_type=VFXNodeType.CHROMA_KEY,
            name="Chroma Keyer",
            parameters={"key_color": key_color, "despill_strength": 1.0},
            inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
            outputs=[
                NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False),
                NodePort("matte", PortDataType.MASK_ALPHA, "Matte", is_input=False),
            ],
        )
        graph.add_node(node_keyer)
        graph.add_edge("node_plate", "output", "node_keyer", "source")

        # 3. Background Node
        node_bg = VFXNode(
            node_id="node_bg",
            node_type=VFXNodeType.MEDIA_INPUT,
            name="Background Plate",
            parameters={"asset_id": bg_asset_id},
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_bg)

        current_fg_id = "node_keyer"

        # 4. Light Wrap Node
        if light_wrap:
            node_wrap = VFXNode(
                node_id="node_wrap",
                node_type=VFXNodeType.ATMOSPHERIC,
                name="Light Wrap Integration",
                parameters={"type": "LIGHT_WRAP", "wrap_amount": 0.4, "wrap_radius": 15},
                inputs=[
                    NodePort("source", PortDataType.IMAGE_RGBA, "Foreground", is_input=True),
                    NodePort("background", PortDataType.IMAGE_RGBA, "Background", is_input=True),
                ],
                outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
            )
            graph.add_node(node_wrap)
            graph.add_edge("node_keyer", "output", "node_wrap", "source")
            graph.add_edge("node_bg", "output", "node_wrap", "background")
            current_fg_id = "node_wrap"

        # 5. Merge Node (Over)
        node_merge = VFXNode(
            node_id="node_merge",
            node_type=VFXNodeType.MERGE,
            name="Final Composite",
            parameters={"blend_mode": BlendMode.OVER.value},
            inputs=[
                NodePort("background", PortDataType.IMAGE_RGBA, "Background", is_input=True),
                NodePort("foreground", PortDataType.IMAGE_RGBA, "Foreground", is_input=True),
            ],
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_merge)
        graph.add_edge("node_bg", "output", "node_merge", "background")
        graph.add_edge(current_fg_id, "output", "node_merge", "foreground")

        # 6. Terminal Output Node
        node_out = VFXNode(
            node_id="node_out",
            node_type=VFXNodeType.MEDIA_OUTPUT,
            name="Master Output",
            inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
        )
        graph.add_node(node_out)
        graph.add_edge("node_merge", "output", "node_out", "source")

        return graph

    @staticmethod
    def create_object_removal_graph(
        project_id: str,
        name: str,
        plate_asset_id: str = "plate_source",
        mask_asset_id: str = "cleanup_mask",
        method: str = "TELEA",
        resolution: Tuple[int, int] = (1920, 1080),
    ) -> CompositingGraph:
        """
        Recipe: Wire/Object Removal via Telea / Navier-Stokes Inpainting.
        """
        w, h = resolution
        graph = CompositingGraph(
            graph_id=str(uuid4()),
            project_id=project_id,
            name=name,
            resolution_w=w,
            resolution_h=h,
        )

        node_plate = VFXNode(
            node_id="node_plate",
            node_type=VFXNodeType.MEDIA_INPUT,
            name="Source Plate",
            parameters={"asset_id": plate_asset_id},
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_plate)

        node_inpaint = VFXNode(
            node_id="node_inpaint",
            node_type=VFXNodeType.INPAINT,
            name="Object Inpainter",
            parameters={"method": method, "radius": 3},
            inputs=[
                NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True),
                NodePort("mask", PortDataType.MASK_ALPHA, "Mask", is_input=True),
            ],
            outputs=[NodePort("output", PortDataType.IMAGE_RGBA, "Output", is_input=False)],
        )
        graph.add_node(node_inpaint)
        graph.add_edge("node_plate", "output", "node_inpaint", "source")

        node_out = VFXNode(
            node_id="node_out",
            node_type=VFXNodeType.MEDIA_OUTPUT,
            name="Master Output",
            inputs=[NodePort("source", PortDataType.IMAGE_RGBA, "Source", is_input=True)],
        )
        graph.add_node(node_out)
        graph.add_edge("node_inpaint", "output", "node_out", "source")

        return graph

