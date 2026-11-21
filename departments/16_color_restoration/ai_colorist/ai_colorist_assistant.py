"""
AI Colorist Assistant for Department 16.
Performs objective image analysis (exposure, color cast, dynamic range, clipping, skin-tone vectorscope)
and generates explainable, human-approvable grading recommendations.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import cv2
import numpy as np
from ..core.models import (
    ColorSpace, GradingGraph, GradingNode, GradingNodeType, PrimaryGradingParameters
)


class AIColoristAssistant:
    """
    AI-driven color intelligence analyzing footage and synthesizing explainable grades.
    """

    @classmethod
    def analyze_frame(cls, image_rgb: np.ndarray) -> Dict[str, Any]:
        """
        Calculates objective colorimetric and exposure statistics from an RGB image.
        """
        arr = np.clip(image_rgb[:, :, :3], 0.0, 1.0).astype(np.float32)
        h, w = arr.shape[:2]
        total_pixels = float(h * w)

        # 1. Luminance (Rec.709 coefficients)
        lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        mean_lum = float(np.mean(lum))
        std_lum = float(np.std(lum))

        # 2. Clipping & Dynamic Range
        highlight_clipping_pct = float(np.sum(lum >= 0.98) / total_pixels) * 100.0
        shadow_crush_pct = float(np.sum(lum <= 0.02) / total_pixels) * 100.0
        dynamic_range_stops = float(np.log2(max(np.max(lum), 1e-4) / max(np.min(lum[lum > 0]), 1e-4)))

        # 3. White Balance & Color Cast (Gray World Hypothesis)
        mean_r = float(np.mean(arr[:, :, 0]))
        mean_g = float(np.mean(arr[:, :, 1]))
        mean_b = float(np.mean(arr[:, :, 2]))

        # Chromatic deviation from neutral gray
        avg_channel = (mean_r + mean_g + mean_b) / 3.0
        r_dev = (mean_r - avg_channel) / max(avg_channel, 1e-4)
        b_dev = (mean_b - avg_channel) / max(avg_channel, 1e-4)

        # Estimate Kelvin color temperature (approximate shift)
        # Red heavy -> low Kelvin (warm ~4500K); Blue heavy -> high Kelvin (cool ~8000K)
        temp_shift_k = - (r_dev - b_dev) * 2500.0
        estimated_temp_k = float(np.clip(6500.0 + temp_shift_k, 3000.0, 10000.0))
        estimated_tint = float(np.clip((mean_g - (mean_r + mean_b) / 2.0) * 100.0, -50.0, 50.0))

        # 4. Skin Tone Isolation & Vectorscope Alignment
        skin_mask, skin_angle_deg = cls._detect_skin_and_vectorscope_angle(arr)

        return {
            "mean_luminance": mean_lum,
            "std_luminance": std_lum,
            "highlight_clipping_pct": highlight_clipping_pct,
            "shadow_crush_pct": shadow_crush_pct,
            "dynamic_range_stops": dynamic_range_stops,
            "color_cast": {
                "red_deviation": r_dev,
                "blue_deviation": b_dev,
                "estimated_temp_k": estimated_temp_k,
                "estimated_tint": estimated_tint
            },
            "skin_detected": bool(np.sum(skin_mask) > 100),
            "skin_vectorscope_angle_deg": skin_angle_deg
        }

    @staticmethod
    def _detect_skin_and_vectorscope_angle(arr_rgb: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Detects human skin pixels in YCbCr and measures angular deviation from the 123 deg I-line.
        """
        img_uint8 = (arr_rgb * 255.0).astype(np.uint8)
        ycbcr = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2YCrCb)
        cr = ycbcr[:, :, 1].astype(np.float32)
        cb = ycbcr[:, :, 2].astype(np.float32)

        # Standard skin cluster bounding box in Cr-Cb space
        skin_mask = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)

        if np.sum(skin_mask) > 50:
            mean_cr = np.mean(cr[skin_mask]) - 128.0
            mean_cb = np.mean(cb[skin_mask]) - 128.0
            # Vectorscope angle relative to neutral (0,0)
            angle = float(np.degrees(np.arctan2(mean_cr, mean_cb))) % 360.0
            return skin_mask, angle
        return skin_mask, 123.0 # Default I-line

    @classmethod
    def recommend_grade(
        cls,
        image_rgb: np.ndarray,
        project_id: UUID,
        creative_intent: Optional[str] = None
    ) -> Tuple[GradingGraph, List[str]]:
        """
        Synthesizes an editable GradingGraph accompanied by explainable justifications.
        """
        stats = cls.analyze_frame(image_rgb)
        explanations = []

        params = PrimaryGradingParameters()

        # Exposure correction: target middle gray ~ 0.18
        mean_lum = stats["mean_luminance"]
        if mean_lum < 0.12:
            ev_boost = min(float(np.log2(0.18 / max(mean_lum, 0.02))), 2.0)
            params.exposure_ev = round(ev_boost, 2)
            explanations.append(f"Underexposed frame (mean luminance {mean_lum:.2f}); recommended +{params.exposure_ev} EV exposure compensation.")
        elif mean_lum > 0.35 and stats["highlight_clipping_pct"] > 5.0:
            ev_cut = max(float(np.log2(0.20 / mean_lum)), -1.5)
            params.exposure_ev = round(ev_cut, 2)
            params.highlights = -0.4
            explanations.append(f"Overexposed highlights ({stats['highlight_clipping_pct']:.1f}% clipping); recommended {params.exposure_ev} EV reduction with highlight roll-off.")

        # White balance correction: neutralize cast
        cast = stats["color_cast"]
        temp_k = cast["estimated_temp_k"]
        if abs(temp_k - 6500.0) > 300.0:
            # Shift in opposite direction to neutralize
            target_k = 6500.0 - (temp_k - 6500.0) * 0.7
            params.temperature_k = round(float(np.clip(target_k, 3500.0, 9500.0)), 0)
            explanations.append(f"Color temperature cast detected ({temp_k:.0f}K); compensated to {params.temperature_k:.0f}K.")

        if abs(cast["estimated_tint"]) > 5.0:
            params.tint = round(-cast["estimated_tint"] * 0.5, 1)
            explanations.append(f"Green/magenta tint cast detected ({cast['estimated_tint']:.1f}); neutralized tint to {params.tint}.")

        # Contrast adjustment
        if stats["std_luminance"] < 0.15:
            params.contrast = 1.15
            explanations.append("Low contrast detected; boosted contrast slope to 1.15 with 18% pivot.")

        # Construct GradingGraph
        primary_node = GradingNode(
            name="AI Corrective Primary",
            node_type=GradingNodeType.PRIMARY,
            primary_params=params
        )

        nodes = [primary_node]

        # If creative intent requested (e.g., cinematic), add second node
        if creative_intent and "cinematic" in creative_intent.lower():
            look_node = GradingNode(
                name="AI Cinematic Look",
                node_type=GradingNodeType.CREATIVE_LOOK,
                look_preset_name="Teal and Orange",
                opacity=0.65
            )
            nodes.append(look_node)
            explanations.append("Applied subtle Teal & Orange cinematic look at 65% opacity.")

        graph = GradingGraph(
            project_id=project_id,
            name="AI Recommended Grade",
            nodes=nodes,
            description="; ".join(explanations)
        )

        return graph, explanations
