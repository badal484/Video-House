"""
VFX Quality Control Checker
Inspects rendered composite frames for matte holes, spill leakage, edge halos, and jitter.
"""
from typing import Any, Dict, List, Optional
import cv2
import numpy as np


class VFXQualityChecker:
    """
    Automated optical and spatial quality auditor for visual effects composites.
    """

    @staticmethod
    def inspect_matte_integrity(alpha_mask: np.ndarray) -> Dict[str, Any]:
        """
        Detects accidental pinholes inside solid foreground regions.
        """
        # Binarize core foreground
        core = (alpha_mask > 0.95).astype(np.uint8) * 255
        # Fill holes
        h, w = core.shape[:2]
        flood = core.copy()
        mask = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(flood, mask, (0, 0), 255)
        filled = cv2.bitwise_not(flood) | core

        # Pinholes are differences between filled and core
        pinholes = cv2.bitwise_and(filled, cv2.bitwise_not(core))
        num_pinholes = int(np.sum(pinholes > 0))

        return {
            "passed": num_pinholes < 50,
            "pinhole_pixel_count": num_pinholes,
            "severity": "HIGH" if num_pinholes > 200 else ("MEDIUM" if num_pinholes > 50 else "NONE"),
        }

    @staticmethod
    def inspect_spill_leakage(rgb_image: np.ndarray, alpha_mask: np.ndarray, key_color: str = "GREEN") -> Dict[str, Any]:
        """
        Checks for residual green or blue spill reflections on foreground subject.
        """
        fg_pixels = alpha_mask > 0.8
        if not np.any(fg_pixels):
            return {"passed": True, "spill_ratio_max": 0.0}

        r = rgb_image[:, :, 0].astype(np.float32)
        g = rgb_image[:, :, 1].astype(np.float32)
        b = rgb_image[:, :, 2].astype(np.float32)

        if key_color.upper() == "GREEN":
            spill_ratio = g[fg_pixels] / (r[fg_pixels] + b[fg_pixels] + 1e-5)
        else:
            spill_ratio = b[fg_pixels] / (r[fg_pixels] + g[fg_pixels] + 1e-5)

        max_ratio = float(np.max(spill_ratio))
        mean_ratio = float(np.mean(spill_ratio))
        passed = max_ratio < 0.75

        return {
            "passed": passed,
            "max_spill_ratio": round(max_ratio, 3),
            "mean_spill_ratio": round(mean_ratio, 3),
            "severity": "HIGH" if max_ratio > 0.85 else ("MEDIUM" if max_ratio > 0.75 else "NONE"),
        }

    @staticmethod
    def inspect_edge_halos(rgb_image: np.ndarray, alpha_mask: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes edge transition variance to detect dark fringes or halo borders.
        """
        edge_zone = (alpha_mask > 0.1) & (alpha_mask < 0.9)
        if not np.any(edge_zone):
            return {"passed": True, "edge_luminance_variance": 0.0}

        gray = cv2.cvtColor(rgb_image, cv2.COLOR_BGR2GRAY) if rgb_image.ndim == 3 else rgb_image
        edge_pixels = gray[edge_zone]
        variance = float(np.var(edge_pixels))

        return {
            "passed": variance < 1500.0,
            "edge_luminance_variance": round(variance, 2),
        }

    @classmethod
    def audit_composite(
        cls,
        composite_rgba: np.ndarray,
        key_color: str = "GREEN",
    ) -> Dict[str, Any]:
        """
        Full QC audit of a rendered composite frame.
        """
        alpha = composite_rgba[:, :, 3].astype(np.float32) / 255.0 if composite_rgba.shape[2] == 4 else np.ones(composite_rgba.shape[:2], dtype=np.float32)
        rgb = composite_rgba[:, :, :3]

        m_check = cls.inspect_matte_integrity(alpha)
        s_check = cls.inspect_spill_leakage(rgb, alpha, key_color)
        e_check = cls.inspect_edge_halos(rgb, alpha)

        all_passed = m_check["passed"] and s_check["passed"] and e_check["passed"]
        score = 1.0
        if not m_check["passed"]: score -= 0.3
        if not s_check["passed"]: score -= 0.3
        if not e_check["passed"]: score -= 0.2

        return {
            "qc_status": "PASSED" if all_passed else "WARNING",
            "score": max(round(score, 2), 0.0),
            "checks": {
                "matte_integrity": m_check,
                "color_spill": s_check,
                "edge_halos": e_check,
            },
        }

