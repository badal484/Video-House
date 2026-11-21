"""
AI Director Creative Blueprint Color Bridge for Department 16.
Translates Part 04 ProductionBlueprint creative visual style and lighting cues
into validated GradingGraph presets.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from ..core.models import (
    GradingGraph, GradingNode, GradingNodeType, PrimaryGradingParameters
)


class DirectorColorBridge:
    """
    Parses creative direction briefs and blueprints into executable color grading graphs.
    """

    @classmethod
    def blueprint_to_grading_graph(
        cls,
        project_id: UUID,
        creative_style: str,
        lighting_cues: Optional[str] = None
    ) -> GradingGraph:
        """
        Synthesizes a grading graph tailored to creative director intent.
        """
        style = creative_style.lower()
        lighting = (lighting_cues or "").lower()

        nodes: List[GradingNode] = []

        # 1. Primary balance based on lighting
        primary = PrimaryGradingParameters()
        if "sunset" in lighting or "golden hour" in lighting:
            primary.temperature_k = 4800.0
            primary.exposure_ev = 0.2
            primary.contrast = 1.15
            primary.vibrance = 0.2
        elif "night" in lighting or "noir" in lighting:
            primary.exposure_ev = -0.5
            primary.temperature_k = 7200.0
            primary.contrast = 1.3
            primary.shadows = -0.2
        elif "overcast" in lighting or "cold" in lighting:
            primary.temperature_k = 7500.0
            primary.saturation = 0.85
            primary.contrast = 0.95

        nodes.append(GradingNode(
            name="Director Lighting Compensation",
            node_type=GradingNodeType.PRIMARY,
            primary_params=primary
        ))

        # 2. Creative Look based on style
        if "teal" in style or "blockbuster" in style or "cinematic" in style:
            nodes.append(GradingNode(
                name="Cinematic Blockbuster",
                node_type=GradingNodeType.CREATIVE_LOOK,
                look_preset_name="Teal and Orange",
                opacity=0.75
            ))
        elif "vintage" in style or "retro" in style or "film" in style:
            nodes.append(GradingNode(
                name="Vintage Print Emulation",
                node_type=GradingNodeType.CREATIVE_LOOK,
                look_preset_name="Film Stock",
                opacity=0.85
            ))
        elif "noir" in style or "monochrome" in style or "b&w" in style:
            nodes.append(GradingNode(
                name="Dramatic Black & White",
                node_type=GradingNodeType.CREATIVE_LOOK,
                look_preset_name="Monochrome",
                opacity=1.0
            ))
        elif "bleach" in style:
            nodes.append(GradingNode(
                name="Gritty Bleach Bypass",
                node_type=GradingNodeType.CREATIVE_LOOK,
                look_preset_name="Bleach Bypass",
                opacity=0.8
            ))

        return GradingGraph(
            project_id=project_id,
            name=f"Director Style: {creative_style.title()}",
            nodes=nodes,
            description=f"Automated translation of creative style '{creative_style}' and lighting '{lighting_cues}'."
        )
