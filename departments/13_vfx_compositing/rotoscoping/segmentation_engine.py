"""
Roto & Segmentation Engine
Performs bounding box segmentation, GrabCut energy minimization, and temporal mask propagation.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class SegmentationEngine:
    """
    Isolates foreground subjects and creates high-fidelity rotoscoping masks.
    """

    @staticmethod
    def segment_box(
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],  # (x, y, width, height)
        iterations: int = 5,
    ) -> np.ndarray:
        """
        Segments an object inside a bounding box using OpenCV GrabCut algorithm.
        Returns single-channel float32 alpha mask [0.0, 1.0].
        """
        h, w = image.shape[:2]
        x, y, bw, bh = bbox
        # Constrain bbox to image boundaries
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        bw = max(1, min(bw, w - x))
        bh = max(1, min(bh, h - y))
        rect = (x, y, bw, bh)

        bgr = image[:, :, :3] if image.ndim == 3 and image.shape[2] >= 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if bgr.dtype != np.uint8:
            bgr = np.clip(bgr * 255.0, 0, 255).astype(np.uint8)

        mask = np.zeros((h, w), dtype=np.uint8)
        bgd_model = np.zeros((1, 65), dtype=np.float64)
        fgd_model = np.zeros((1, 65), dtype=np.float64)

        try:
            cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_RECT)
            # GC_FGD (1) and GC_PR_FGD (3) are foreground
            fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
            # Soft feather boundary
            fg_float = fg_mask.astype(np.float32) / 255.0
            feathered = cv2.GaussianBlur(fg_float, (7, 7), 2.0)
            return np.clip(feathered, 0.0, 1.0)
        except Exception:
            # Fallback simple rectangle mask
            fallback = np.zeros((h, w), dtype=np.float32)
            fallback[y : y + bh, x : x + bw] = 1.0
            return fallback

    @staticmethod
    def propagate_mask_optical_flow(
        prev_frame: np.ndarray,
        curr_frame: np.ndarray,
        prev_mask: np.ndarray,
    ) -> np.ndarray:
        """
        Propagates a rotoscoping mask from prev_frame to curr_frame using dense Farneback optical flow.
        """
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) if prev_frame.ndim == 3 else prev_frame
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY) if curr_frame.ndim == 3 else curr_frame

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        h, w = prev_mask.shape[:2]
        flow_x = flow[:, :, 0]
        flow_y = flow[:, :, 1]

        map_x = (np.arange(w) + flow_x).astype(np.float32)
        map_y = (np.arange(h)[:, np.newaxis] + flow_y).astype(np.float32)

        warped_mask = cv2.remap(
            prev_mask, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0
        )
        return np.clip(warped_mask, 0.0, 1.0)

