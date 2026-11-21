"""
Multi-Video Comparison and Style Matching Service.
Compares source footage against reference profiles to calculate pacing,
visual lighting, and camera motion compatibility scores.
Identifies suitable moments in source footage matching reference techniques.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.assets.intelligence_models import (
    ReferenceProfile,
    ShotRecord
)

logger = logging.getLogger("studio.video_comparator")

class MultiVideoComparisonService:
    def compare_to_reference(
        self,
        source_profile: ReferenceProfile,
        reference_profile: ReferenceProfile
    ) -> Dict[str, Any]:
        """
        Compares source footage style against target reference profile.
        Computes metric similarity scores and gives editorial recommendations.
        """
        # 1. Pacing & Cut Velocity Compatibility
        source_asl = source_profile.editing_style.get("average_shot_length_sec", 3.0)
        ref_asl = reference_profile.editing_style.get("average_shot_length_sec", 3.0)
        asl_ratio = min(source_asl, ref_asl) / max(0.1, max(source_asl, ref_asl))
        pacing_score = round(float(asl_ratio), 3)

        # 2. Visual Lighting & Luminance Compatibility
        source_lum = source_profile.visual_style.get("average_luminance", 128.0)
        ref_lum = reference_profile.visual_style.get("average_luminance", 128.0)
        lum_diff = abs(source_lum - ref_lum) / 255.0
        visual_score = round(max(0.0, 1.0 - lum_diff), 3)

        # 3. Camera Motion Alignment
        source_motion = source_profile.visual_style.get("primary_camera_motion", "STATIC")
        ref_motion = reference_profile.visual_style.get("primary_camera_motion", "STATIC")
        motion_score = 1.0 if source_motion == ref_motion else 0.5

        # 4. Overall Weighted Compatibility (Pacing 40%, Visual 35%, Motion 25%)
        overall = round(0.40 * pacing_score + 0.35 * visual_score + 0.25 * motion_score, 3)

        recommendations = []
        if pacing_score < 0.6:
            recommendations.append(
                f"Source footage pacing ({source_asl}s ASL) differs significantly from reference ({ref_asl}s ASL). "
                f"Recommend tightening cut points to match reference rhythm."
            )
        if visual_score < 0.7:
            recommendations.append(
                f"Luminance disparity detected (Source: {source_lum}, Ref: {ref_lum}). "
                f"Recommend color grading / CDL transform toward reference palette."
            )
        if motion_score < 1.0:
            recommendations.append(
                f"Reference emphasizes {ref_motion} camera movements while source is predominantly {source_motion}. "
                f"Select source shots featuring dynamic movement for hero sequences."
            )

        return {
            "source_asset_id": str(source_profile.asset_id),
            "reference_asset_id": str(reference_profile.asset_id),
            "overall_compatibility_score": overall,
            "metrics": {
                "pacing_match": pacing_score,
                "visual_lighting_match": visual_score,
                "camera_motion_match": motion_score
            },
            "source_editing_pacing": source_profile.editing_style.get("pacing"),
            "reference_editing_pacing": reference_profile.editing_style.get("pacing"),
            "editorial_recommendations": recommendations
        }
