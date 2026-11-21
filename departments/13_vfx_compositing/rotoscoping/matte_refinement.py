"""
Matte Refinement & Edge Processing Module
Suppresses edge halos, cleans fringe noise, and feathers alpha mattes.
"""
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


class MatteRefiner:
    """
    Enhances and filters alpha mattes to ensure seamless blending without dark fringing.
    """

    @staticmethod
    def suppress_halo(
        rgb_image: np.ndarray,
        alpha_mask: np.ndarray,
        halo_radius: int = 2,
    ) -> np.ndarray:
        """
        Suppresses dark edge fringes by expanding foreground color outwards into the semi-transparent zone.
        """
        h, w = alpha_mask.shape[:2]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * halo_radius + 1, 2 * halo_radius + 1))
        
        # Binary core of foreground
        core_mask = (alpha_mask > 0.85).astype(np.uint8) * 255
        dilated_rgb = cv2.dilate(rgb_image, kernel)

        # Blend dilated color in the transition boundary (0.05 < alpha < 0.85)
        edge_zone = ((alpha_mask > 0.05) & (alpha_mask <= 0.85))[:, :, np.newaxis]
        out_rgb = np.where(edge_zone, dilated_rgb, rgb_image)
        return out_rgb

    @staticmethod
    def feather_matte(
        alpha_mask: np.ndarray,
        blur_radius: float = 2.0,
    ) -> np.ndarray:
        """
        Applies smooth sub-pixel Gaussian edge feathering.
        """
        if blur_radius <= 0.0:
            return alpha_mask
        ksize = int(np.ceil(blur_radius * 4.0)) | 1
        feathered = cv2.GaussianBlur(alpha_mask.astype(np.float32), (ksize, ksize), blur_radius)
        return np.clip(feathered, 0.0, 1.0)

