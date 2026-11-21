"""
Video Cleanup & Inpainting Engine
Performs object removal, wire removal, and logo cleanups using Fast Marching (Telea)
and Navier-Stokes differential equations.
"""
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


class InpaintingEngine:
    """
    Removes unwanted objects, rigs, wires, and blemishes from footage.
    """

    @staticmethod
    def inpaint_frame(
        image: np.ndarray,
        mask: np.ndarray,
        method: str = "TELEA",  # "TELEA" or "NS" (Navier-Stokes)
        inpaint_radius: int = 3,
    ) -> np.ndarray:
        """
        Inpaints missing pixels defined by non-zero mask pixels.
        Image: uint8 or float32 BGR/BGRA array.
        Mask: uint8 single channel [0, 255].
        """
        is_uint8 = image.dtype == np.uint8
        arr = image.copy()
        if not is_uint8:
            arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)

        # Ensure mask is uint8 single channel
        if mask.dtype != np.uint8:
            clean_mask = (mask > 0.1).astype(np.uint8) * 255
        else:
            clean_mask = mask

        inpaint_flag = cv2.INPAINT_TELEA if method.upper() == "TELEA" else cv2.INPAINT_NS

        # If 4-channel BGRA, inpaint BGR and reset alpha in mask to 255 or 0
        if arr.ndim == 3 and arr.shape[2] == 4:
            bgr = arr[:, :, :3]
            alpha = arr[:, :, 3]
            inp_bgr = cv2.inpaint(bgr, clean_mask, inpaint_radius, inpaint_flag)
            out = np.concatenate([inp_bgr, alpha[:, :, np.newaxis]], axis=2)
        else:
            out = cv2.inpaint(arr[:, :, :3], clean_mask, inpaint_radius, inpaint_flag)

        if not is_uint8:
            return out.astype(np.float32) / 255.0
        return out
