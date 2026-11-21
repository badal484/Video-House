"""
Cinematic Effects Module
Simulates optical phenomena: chromatic aberration, camera shake, and bloom/glow.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class CinematicEffects:
    """
    Renders optical and camera lens artifacts for cinematic realism.
    """

    @staticmethod
    def chromatic_aberration(
        image: np.ndarray,
        shift_pixels: int = 3,
    ) -> np.ndarray:
        """
        Applies radial or horizontal chromatic aberration by shifting Red and Blue color channels.
        """
        h, w = image.shape[:2]
        has_alpha = image.ndim == 3 and image.shape[2] == 4
        
        # Channel shift: Shift Red left, Blue right
        m_red = np.float32([[1, 0, -shift_pixels], [0, 1, 0]])
        m_blue = np.float32([[1, 0, shift_pixels], [0, 1, 0]])

        b = cv2.warpAffine(image[:, :, 0], m_blue, (w, h), borderMode=cv2.BORDER_REFLECT)
        g = image[:, :, 1]
        r = cv2.warpAffine(image[:, :, 2], m_red, (w, h), borderMode=cv2.BORDER_REFLECT)

        if has_alpha:
            alpha = image[:, :, 3]
            return np.dstack([b, g, r, alpha])
        return np.dstack([b, g, r])

    @staticmethod
    def lens_glow(
        image: np.ndarray,
        threshold: float = 0.7,
        glow_radius: int = 25,
        glow_intensity: float = 0.5,
    ) -> np.ndarray:
        """
        Generates atmospheric lens glow on bright highlights.
        """
        arr = image.astype(np.float32)
        is_uint8 = image.dtype == np.uint8
        if is_uint8:
            arr /= 255.0

        rgb = arr[:, :, :3]
        # Extract highlights exceeding threshold
        luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        highlight_mask = np.clip((luma - threshold) / max(1.0 - threshold, 1e-5), 0.0, 1.0)
        highlights = rgb * highlight_mask[:, :, np.newaxis]

        # Multi-scale Gaussian blur for natural falloff
        k1 = (glow_radius * 2 + 1, glow_radius * 2 + 1)
        k2 = (glow_radius * 4 + 1, glow_radius * 4 + 1)
        blur1 = cv2.GaussianBlur(highlights, k1, glow_radius / 2.0)
        blur2 = cv2.GaussianBlur(highlights, k2, glow_radius)

        bloom = (blur1 * 0.6 + blur2 * 0.4) * glow_intensity
        glowing_rgb = np.clip(rgb + bloom, 0.0, 1.0)

        if arr.shape[2] == 4:
            out = np.dstack([glowing_rgb, arr[:, :, 3]])
        else:
            out = glowing_rgb

        if is_uint8:
            return (out * 255.0).astype(np.uint8)
        return out
