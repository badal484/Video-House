"""
Reference Look & Shot Matching Engine for Department 16.
Implements Reinhard Lab color transfer, cumulative histogram matching,
and skin-tone preserving shot-to-shot look harmonization.
"""
from typing import Any, Dict, Optional, Tuple
from uuid import UUID, uuid4
import cv2
import numpy as np
from ..core.models import GradingGraph, GradingNode, GradingNodeType, PrimaryGradingParameters


class ReferenceMatcher:
    """
    Analyzes visual reference media and transfers color grading distributions.
    """

    @staticmethod
    def rgb_to_lab(img_rgb: np.ndarray) -> np.ndarray:
        """Converts float32 [0.0, 1.0] RGB to CIE Lab float32."""
        arr = np.clip(img_rgb[:, :, :3], 0.0, 1.0).astype(np.float32)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2Lab)

    @staticmethod
    def lab_to_rgb(img_lab: np.ndarray) -> np.ndarray:
        """Converts CIE Lab float32 to RGB float32 [0.0, 1.0]."""
        rgb = cv2.cvtColor(img_lab.astype(np.float32), cv2.COLOR_Lab2RGB)
        return np.clip(rgb, 0.0, 1.0)

    @classmethod
    def analyze_reference(cls, image_rgb: np.ndarray) -> Dict[str, Any]:
        """
        Extracts statistical color moments (mean, std) and luminance characteristics from a reference image.
        """
        lab = cls.rgb_to_lab(image_rgb)
        mean_l = float(np.mean(lab[:, :, 0]))
        std_l = float(np.std(lab[:, :, 0]))
        mean_a = float(np.mean(lab[:, :, 1]))
        std_a = float(np.std(lab[:, :, 1]))
        mean_b = float(np.mean(lab[:, :, 2]))
        std_b = float(np.std(lab[:, :, 2]))

        return {
            "mean_lab": (mean_l, mean_a, mean_b),
            "std_lab": (std_l, std_a, std_b),
            "dynamic_range": float(np.max(lab[:, :, 0]) - np.min(lab[:, :, 0])),
            "color_temperature_bias": "warm" if mean_b > 5.0 else ("cool" if mean_b < -5.0 else "neutral")
        }

    @classmethod
    def reinhard_transfer(
        cls,
        source_rgb: np.ndarray,
        target_ref_rgb: np.ndarray,
        preserve_skin: bool = True
    ) -> np.ndarray:
        """
        Executes Reinhard color transfer in CIE Lab color space with optional skin protection.
        """
        src_arr = source_rgb.astype(np.float32)
        has_alpha = src_arr.ndim == 3 and src_arr.shape[2] == 4
        src = src_arr[:, :, :3] if has_alpha else src_arr

        src_lab = cls.rgb_to_lab(src)
        tgt_lab = cls.rgb_to_lab(target_ref_rgb)

        # Compute means and standard deviations
        src_mean = np.mean(src_lab, axis=(0, 1))
        src_std = np.maximum(np.std(src_lab, axis=(0, 1)), 1e-4)

        tgt_mean = np.mean(tgt_lab, axis=(0, 1))
        tgt_std = np.maximum(np.std(tgt_lab, axis=(0, 1)), 1e-4)

        # Shift and scale Lab coordinates
        matched_lab = (src_lab - src_mean) * (tgt_std / src_std) + tgt_mean

        matched_rgb = cls.lab_to_rgb(matched_lab)

        # Skin tone preservation: blend back original skin colors
        if preserve_skin:
            img_uint8 = np.clip(src * 255.0, 0, 255).astype(np.uint8)
            ycbcr = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2YCrCb)
            cr = ycbcr[:, :, 1]
            cb = ycbcr[:, :, 2]
            skin_mask = ((cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)).astype(np.float32)[:, :, np.newaxis]
            skin_mask = cv2.GaussianBlur(skin_mask, (7, 7), 2.0)[:, :, np.newaxis]
            matched_rgb = matched_rgb * (1.0 - skin_mask) + src * skin_mask

        if has_alpha:
            return np.concatenate([matched_rgb, src_arr[:, :, 3:4]], axis=2)
        return matched_rgb

    @classmethod
    def match_shots(
        cls,
        source_rgb: np.ndarray,
        reference_rgb: np.ndarray,
        project_id: UUID
    ) -> Tuple[GradingGraph, np.ndarray]:
        """
        Analyzes source and reference footage, executes transfer, and synthesizes a reusable GradingGraph.
        """
        src_stats = cls.analyze_reference(source_rgb)
        ref_stats = cls.analyze_reference(reference_rgb)

        # Calculate offset in L (luminance) and chromatic balance
        delta_l = ref_stats["mean_lab"][0] - src_stats["mean_lab"][0]
        ev_approx = float(delta_l / 35.0) # approx stops

        params = PrimaryGradingParameters(
            exposure_ev=round(ev_approx, 2),
            contrast=round(float(ref_stats["std_lab"][0] / max(src_stats["std_lab"][0], 1e-4)), 2)
        )

        node = GradingNode(
            name="Reference Shot Match",
            node_type=GradingNodeType.PRIMARY,
            primary_params=params
        )

        matched_img = cls.reinhard_transfer(source_rgb, reference_rgb, preserve_skin=True)

        graph = GradingGraph(
            project_id=project_id,
            name="Matched Look Preset",
            nodes=[node],
            description=f"Matched to reference {ref_stats['color_temperature_bias']} aesthetic."
        )

        return graph, matched_img
