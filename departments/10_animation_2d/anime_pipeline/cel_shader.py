"""
Anime Cel Shading Engine
Applies three-tier anime shading: flat base tone, core shadow layer, and specular highlight.
"""
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


class AnimeCelShader:
    """
    Renders authentic anime cel shading with crisp shadow boundaries and hair highlights.
    """

    @staticmethod
    def render_cel_shaded_subject(
        canvas_shape: Tuple[int, int],  # (H, W)
        center: Tuple[int, int],
        radius: int,
        color_base_rgb: Tuple[int, int, int],
        color_shadow_rgb: Tuple[int, int, int],
        color_highlight_rgb: Tuple[int, int, int],
        light_angle_deg: float = 45.0,
    ) -> np.ndarray:
        """
        Renders a circular 3-tier cel-shaded anime element with base, shadow, and highlight.
        Returns RGBA uint8 array.
        """
        h, w = canvas_shape
        out = np.zeros((h, w, 4), dtype=np.uint8)

        # Base circle mask
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)

        # 1. Fill Flat Base
        bgr_base = (color_base_rgb[2], color_base_rgb[1], color_base_rgb[0])
        out[mask > 0, :3] = bgr_base
        out[mask > 0, 3] = 255

        # 2. Compute Core Shadow (Crescent shape on side opposite to light)
        light_rad = np.radians(light_angle_deg)
        shadow_offset_x = int(radius * 0.35 * -np.cos(light_rad))
        shadow_offset_y = int(radius * 0.35 * -np.sin(light_rad))

        shadow_circle = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(shadow_circle, (center[0] + shadow_offset_x, center[1] + shadow_offset_y), int(radius * 0.85), 255, -1)
        # Shadow is the difference: mask AND NOT shadow_circle
        core_shadow_mask = cv2.bitwise_and(mask, cv2.bitwise_not(shadow_circle))

        bgr_shadow = (color_shadow_rgb[2], color_shadow_rgb[1], color_shadow_rgb[0])
        out[core_shadow_mask > 0, :3] = bgr_shadow

        # 3. Specular Rim Highlight (Crisp edge line on light side)
        highlight_offset_x = int(radius * 0.15 * np.cos(light_rad))
        highlight_offset_y = int(radius * 0.15 * np.sin(light_rad))

        high_circle = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(high_circle, (center[0] + highlight_offset_x, center[1] + highlight_offset_y), int(radius * 0.95), 255, -1)
        rim_mask = cv2.bitwise_and(mask, cv2.bitwise_not(high_circle))

        bgr_high = (color_highlight_rgb[2], color_highlight_rgb[1], color_highlight_rgb[0])
        out[rim_mask > 0, :3] = bgr_high

        # 4. Clean Ink Line Art Border
        cv2.circle(out, center, radius, (30, 30, 35, 255), 2, cv2.LINE_AA)

        return out
