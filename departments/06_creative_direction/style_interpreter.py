"""
Reference Style Interpretation Service.
Bridges Part 03's deconstructed ReferenceProfile into creative planning decisions,
modulating shot pacing, color palette, camera motion distributions, and typography.
Enforces commercial intellectual property hygiene and originality boundaries.
"""
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.intelligence_models import (
    CameraMotionType,
    ReferenceProfile
)
from core.planning.planning_models import (
    CreativeBrief,
    CreativeConcept,
    PacingStyle
)

logger = logging.getLogger("studio.creative_direction.style_interpreter")

class ReferenceMatchingDegree(str, Enum):
    INSPIRATION_ONLY = "INSPIRATION_ONLY"
    MODERATE_INFLUENCE = "MODERATE_INFLUENCE"
    STRONG_MATCHING = "STRONG_MATCHING"
    DETAILED_TECHNIQUE_MATCHING = "DETAILED_TECHNIQUE_MATCHING"

class ReferenceStyleInterpreter:
    def __init__(self):
        pass

    def apply_reference_to_brief(
        self,
        brief: CreativeBrief,
        ref_profile: ReferenceProfile,
        matching_degree: ReferenceMatchingDegree = ReferenceMatchingDegree.STRONG_MATCHING
    ) -> CreativeBrief:
        """
        Transfers stylistic, rhythmic, and color palettes from a reference video into the creative brief.
        """
        # 1. Color Palette Transfer
        ref_palette = ref_profile.visual_style.get("dominant_palette_hex", [])
        if ref_palette and matching_degree in [
            ReferenceMatchingDegree.MODERATE_INFLUENCE,
            ReferenceMatchingDegree.STRONG_MATCHING,
            ReferenceMatchingDegree.DETAILED_TECHNIQUE_MATCHING
        ]:
            brief.color_palette = list(ref_palette)
            brief.assumptions.append(f"Adopted 5-color dominant palette from reference: {', '.join(ref_palette)}")

        # 2. Pacing Style & ASL Alignment
        asl = ref_profile.editing_style.get("average_shot_length_sec", 3.0)
        pacing_str = ref_profile.editing_style.get("pacing", "DYNAMIC_BALANCED")
        try:
            brief.pacing_style = PacingStyle(pacing_str)
        except ValueError:
            if asl <= 2.0:
                brief.pacing_style = PacingStyle.FAST_PACED
            elif asl > 5.0:
                brief.pacing_style = PacingStyle.CALM_CONTEMPLATIVE
            else:
                brief.pacing_style = PacingStyle.DYNAMIC_BALANCED

        brief.assumptions.append(
            f"Aligned editing pacing to reference Average Shot Length ({asl:.2f}s, {brief.pacing_style.value})."
        )

        # 3. Audio & Music Pacing
        bpm = ref_profile.audio_style.get("estimated_bpm")
        if bpm:
            brief.music_direction = f"Rhythmic tempo calibrated to {bpm:.1f} BPM reference score."

        # 4. Motion Graphics & Typography
        mograph = ref_profile.motion_graphics
        if mograph:
            brief.typography_style = f"{mograph.get('typography_style', 'Clean Minimal')} with {mograph.get('text_overlay_frequency', 'SPARSE').lower()} overlays."

        # 5. IP Hygiene Guardrail
        brief.exclusions.append("Prohibited from copying proprietary character likenesses, protected logos, or trademarked assets from reference footage.")

        return brief

    def extract_cinematography_guidelines(
        self,
        ref_profile: ReferenceProfile
    ) -> Dict[str, Any]:
        """
        Extracts camera motion preferences and average shot durations from the reference profile.
        """
        asl = ref_profile.editing_style.get("average_shot_length_sec", 3.0)
        cpm = ref_profile.editing_style.get("cut_frequency_cpm", 20.0)
        dominant_motion = ref_profile.visual_style.get("dominant_camera_motion", "STATIC")

        return {
            "recommended_asl_sec": round(asl, 2),
            "cuts_per_minute": round(cpm, 1),
            "dominant_camera_motion": dominant_motion,
            "color_grading_lut_target": "Matches reference dominant luminance and contrast curve",
            "ip_compliance": "Style and grammar transferred; source trademark assets quarantined."
        }

