"""
3D Camera Solver Module
Recovers 3D camera rotation, translation, and projection matrix from 2D point tracks.
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class CameraSolver:
    """
    Estimates 3D camera pose and relative motion between consecutive frames or across a sequence.
    """

    @staticmethod
    def estimate_camera_pose(
        pts1: np.ndarray,  # (N, 2) points in frame 1
        pts2: np.ndarray,  # (N, 2) points in frame 2
        focal_length: float = 1000.0,
        principal_point: Tuple[float, float] = (960.0, 540.0),
    ) -> Dict[str, Any]:
        """
        Estimates Essential Matrix, Rotation matrix R, and Translation vector t
        using the 8-point RANSAC algorithm.
        """
        if len(pts1) < 8 or len(pts2) < 8:
            return {
                "success": False,
                "message": "At least 8 feature correspondences required for 3D camera solve.",
            }

        K = np.array([
            [focal_length, 0, principal_point[0]],
            [0, focal_length, principal_point[1]],
            [0, 0, 1],
        ], dtype=np.float64)

        E, inlier_mask = cv2.findEssentialMat(
            pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0
        )

        if E is None:
            return {"success": False, "message": "Failed to estimate Essential Matrix."}

        _, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K)

        return {
            "success": True,
            "rotation_matrix": R.tolist(),
            "translation_vector": t.ravel().tolist(),
            "camera_intrinsics": K.tolist(),
            "inlier_count": int(np.sum(inlier_mask)),
        }

