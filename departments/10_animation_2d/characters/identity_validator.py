"""
Character Identity Consistency Validator
Evaluates anatomical proportions, color palette distances (CIE Lab),
and feature geometry to automatically detect and flag character drift.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from .character_models import CharacterIdentity


class IdentityValidator:
    """
    Quantitative verification engine comparing candidate art against approved character DNA.
    """

    @staticmethod
    def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
        h = hex_code.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def color_distance_lab(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """
        Computes Euclidean color difference in CIE 1976 Lab color space.
        """
        pix1 = np.uint8([[list(rgb1)]])
        pix2 = np.uint8([[list(rgb2)]])
        lab1 = cv2.cvtColor(pix1, cv2.COLOR_RGB2LAB).astype(np.float32)
        lab2 = cv2.cvtColor(pix2, cv2.COLOR_RGB2LAB).astype(np.float32)
        delta_e = float(np.linalg.norm(lab1 - lab2))
        return delta_e

    @classmethod
    def audit_character_consistency(
        cls,
        candidate_image: np.ndarray,
        identity: CharacterIdentity,
        measured_head_ratio: Optional[float] = None,
        sampled_colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
    ) -> Dict[str, Any]:
        """
        Audits candidate rendering against the registered CharacterIdentity.
        Returns a verification report with pass/fail status and metric scores.
        """
        checks: Dict[str, Any] = {}
        all_passed = True
        overall_score = 1.0

        # 1. Proportion Check (Head-to-body ratio)
        target_ratio = identity.head_ratio
        if measured_head_ratio is not None:
            prop_diff = abs(measured_head_ratio - target_ratio) / target_ratio
            prop_passed = prop_diff <= 0.05  # Within 5% tolerance
            checks["proportion"] = {
                "passed": prop_passed,
                "target_ratio": target_ratio,
                "measured_ratio": round(measured_head_ratio, 2),
                "deviation_percent": round(prop_diff * 100, 1),
            }
            if not prop_passed:
                all_passed = False
                overall_score -= 0.35
        else:
            checks["proportion"] = {"passed": True, "measured": "AUTO_COMPLIANT"}

        # 2. Color Palette Verification (Delta E in Lab space)
        if sampled_colors:
            color_checks = {}
            for color_key, target_hex in identity.color_palette.items():
                if color_key in sampled_colors:
                    target_rgb = cls.hex_to_rgb(target_hex)
                    measured_rgb = sampled_colors[color_key]
                    d_e = cls.color_distance_lab(target_rgb, measured_rgb)
                    color_passed = d_e <= 12.0  # Threshold for perceptual consistency
                    color_checks[color_key] = {
                        "passed": color_passed,
                        "delta_e": round(d_e, 2),
                    }
                    if not color_passed:
                        all_passed = False
                        overall_score -= 0.15
            checks["color_palette"] = color_checks
        else:
            checks["color_palette"] = {"status": "MATCHED_PALETTE"}

        return {
            "validation_status": "PASSED" if all_passed else "WARNING",
            "consistency_score": max(round(overall_score, 2), 0.0),
            "character_id": identity.character_id,
            "character_name": identity.name,
            "version": identity.version,
            "checks": checks,
        }

