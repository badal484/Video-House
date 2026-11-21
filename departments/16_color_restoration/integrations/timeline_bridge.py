"""
OpenTimelineIO (OTIO) Timeline Color Bridge for Department 16.
Attaches clip-level and track-level color grades to Part 05 OpenTimelineIO editorial tracks
without altering editorial cut boundaries or audio sync.
"""
from typing import Any, Dict, Optional
import opentimelineio as otio
from ..core.models import GradingGraph


class TimelineColorBridge:
    """
    Bridges grading node graphs directly into OpenTimelineIO clip metadata and effects.
    """

    @staticmethod
    def attach_grade_to_clip(clip: otio.schema.Clip, graph: GradingGraph) -> otio.schema.Clip:
        """
        Attaches a GradingGraph specification to an OTIO Clip metadata dictionary.
        """
        if "color_grading" not in clip.metadata:
            clip.metadata["color_grading"] = {}

        clip.metadata["color_grading"] = {
            "graph_id": str(graph.id),
            "graph_name": graph.name,
            "working_color_space": graph.working_color_space.value,
            "node_count": len(graph.nodes),
            "serialized_graph": graph.model_dump(mode="json")
        }

        # Add as OTIO ColorEffect representation
        effect = otio.schema.Effect(
            name=f"ColorGrade_{graph.name}",
            effect_name="CDL/GradingNodeGraph",
            metadata={"graph_id": str(graph.id)}
        )
        clip.effects.append(effect)
        return clip

    @staticmethod
    def extract_grade_from_clip(clip: otio.schema.Clip) -> Optional[GradingGraph]:
        """
        Reconstructs a GradingGraph from an OTIO Clip's metadata.
        """
        color_meta = clip.metadata.get("color_grading", {})
        serialized = color_meta.get("serialized_graph")
        if serialized:
            return GradingGraph.model_validate(serialized)
        return None
