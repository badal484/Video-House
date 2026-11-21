"""
Chroma Keying & Despill Module
Provides production-grade green and blue screen matte extraction,
color difference despill, and edge refinement.
"""
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np
from ..core.color_space import apply_green_despill, apply_blue_despill


class ChromaKeyer:
    """
    Extracts foreground subjects from green/blue screens with soft matte ramps and despill suppression.
    """
    def __init__(
        self,
        key_color: str = "GREEN",  # "GREEN" or "BLUE"
        screen_color_bgr: Optional[Tuple[int, int, int]] = None,
        threshold_low: float = 0.05,
        threshold_high: float = 0.35,
        despill_strength: float = 1.0,
        edge_erode: int = 1,
        edge_dilate: int = 1,
        edge_feather: float = 1.5,
    ):
        self.key_color = key_color.upper()
        self.screen_color_bgr = screen_color_bgr
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
        self.despill_strength = despill_strength
        self.edge_erode = edge_erode
        self.edge_dilate = edge_dilate
        self.edge_feather = edge_feather

    def extract_matte(self, image: np.ndarray) -> np.ndarray:
        """
        Generates a float32 alpha matte [0.0 (bg), 1.0 (fg)] using color difference metrics.
        Input image can be BGR or BGRA uint8 or float32.
        """
        arr = image.astype(np.float32)
        if image.dtype == np.uint8:
            arr = arr / 255.0

        b = arr[:, :, 0]
        g = arr[:, :, 1]
        r = arr[:, :, 2]

        if self.key_color == "GREEN":
            # Green screen difference: Delta = G - max(R, B)
            max_rb = np.maximum(r, b)
            delta = g - max_rb
        elif self.key_color == "BLUE":
            # Blue screen difference: Delta = B - max(R, G)
            max_rg = np.maximum(r, g)
            delta = b - max_rg
        else:
            raise ValueError(f"Unsupported key_color: {self.key_color}. Use GREEN or BLUE.")

        # Soft ramp calculation
        # If delta > threshold_high => matte = 0.0 (pure background)
        # If delta < threshold_low  => matte = 1.0 (pure foreground)
        range_span = max(self.threshold_high - self.threshold_low, 1e-5)
        raw_matte = 1.0 - np.clip((delta - self.threshold_low) / range_span, 0.0, 1.0)

        # Edge refinement
        matte_uint8 = (raw_matte * 255.0).astype(np.uint8)

        # Erosion (clean outer fringe)
        if self.edge_erode > 0:
            kernel_erode = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * self.edge_erode + 1, 2 * self.edge_erode + 1)
            )
            matte_uint8 = cv2.erode(matte_uint8, kernel_erode)

        # Dilation (bridge small holes)
        if self.edge_dilate > 0:
            kernel_dilate = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * self.edge_dilate + 1, 2 * self.edge_dilate + 1)
            )
            matte_uint8 = cv2.dilate(matte_uint8, kernel_dilate)

        # Gaussian feathering
        refined_matte = matte_uint8.astype(np.float32) / 255.0
        if self.edge_feather > 0.0:
            ksize = int(np.ceil(self.edge_feather * 4.0)) | 1
            refined_matte = cv2.GaussianBlur(refined_matte, (ksize, ksize), self.edge_feather)

        return np.clip(refined_matte, 0.0, 1.0)

    def process(self, image: np.ndarray) -> np.ndarray:
        """
        Executes full chroma key extraction and despill color correction.
        Returns 4-channel BGRA image (uint8 or float32 matching input dtype).
        """
        is_uint8 = image.dtype == np.uint8
        arr = image.astype(np.float32)
        if is_uint8:
            arr = arr / 255.0

        # 1. Extract Alpha Matte
        alpha_matte = self.extract_matte(image)

        # 2. Despill Color Correction
        bgr = arr[:, :, :3]
        rgba = np.concatenate([bgr, alpha_matte[:, :, np.newaxis]], axis=2)

        if self.key_color == "GREEN" and self.despill_strength > 0:
            # Reorder BGR to RGB for despill function
            rgb = rgba[:, :, [2, 1, 0, 3]]
            despilled_rgb = apply_green_despill(rgb, strength=self.despill_strength)
            rgba[:, :, :3] = despilled_rgb[:, :, [2, 1, 0]]
        elif self.key_color == "BLUE" and self.despill_strength > 0:
            rgb = rgba[:, :, [2, 1, 0, 3]]
            despilled_rgb = apply_blue_despill(rgb, strength=self.despill_strength)
            rgba[:, :, :3] = despilled_rgb[:, :, [2, 1, 0]]

        if is_uint8:
            return np.clip(rgba * 255.0, 0, 255).astype(np.uint8)
        return rgba
