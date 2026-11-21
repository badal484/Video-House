"""
Planar Tracking & Perspective Warping Module
Computes 4-point perspective transformations and warps graphics onto target planes.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class PlanarTracker:
    """
    Performs 4-point homography estimation and perspective warping for screen/billboard replacements.
    """

    @staticmethod
    def compute_homography(
        src_corners: np.ndarray,
        dst_corners: np.ndarray,
    ) -> np.ndarray:
        """
        Computes 3x3 perspective homography matrix from 4 corresponding points:
        src_corners: (4, 2) array [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
        dst_corners: (4, 2) array [[x0', y0'], [x1', y1'], [x2', y2'], [x3', y3']]
        """
        src = src_corners.astype(np.float32)
        dst = dst_corners.astype(np.float32)
        H = cv2.getPerspectiveTransform(src, dst)
        return H

    @staticmethod
    def warp_graphic(
        graphic_rgba: np.ndarray,
        target_shape: Tuple[int, int],  # (height, width)
        dst_corners: np.ndarray,        # (4, 2) target quad
        border_mode: int = cv2.BORDER_CONSTANT,
    ) -> np.ndarray:
        """
        Warps a source graphic (RGBA) to fit inside the quadrilateral specified by dst_corners
        in a canvas of target_shape.
        """
        h_g, w_g = graphic_rgba.shape[:2]
        src_corners = np.array([
            [0.0, 0.0],
            [float(w_g - 1), 0.0],
            [float(w_g - 1), float(h_g - 1)],
            [0.0, float(h_g - 1)],
        ], dtype=np.float32)

        H = PlanarTracker.compute_homography(src_corners, dst_corners)
        target_h, target_w = target_shape

        warped = cv2.warpPerspective(
            graphic_rgba,
            H,
            (target_w, target_h),
            flags=cv2.INTER_LANCZOS4,
            borderMode=border_mode,
            borderValue=(0, 0, 0, 0),
        )
        return warped

    @staticmethod
    def generate_planar_mask(
        target_shape: Tuple[int, int],
        dst_corners: np.ndarray,
    ) -> np.ndarray:
        """
        Generates a 1-channel binary mask corresponding to the quadrilateral polygon.
        """
        target_h, target_w = target_shape
        mask = np.zeros((target_h, target_w), dtype=np.uint8)
        pts = dst_corners.astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts], 255)
        return mask
