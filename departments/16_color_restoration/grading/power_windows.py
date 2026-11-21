"""
Power Windows (Geometric Vignettes & Masks) for Department 16.
Generates elliptical and rectangular spatial masks with feathering, rotation, and inversion.
"""
import cv2
import numpy as np
from ..core.models import PowerWindowParameters


class PowerWindowManager:
    """
    Renders soft spatial power window mattes for localized grading.
    """

    @staticmethod
    def generate_window_mask(height: int, width: int, params: PowerWindowParameters) -> np.ndarray:
        """
        Generates a 2D float32 mask [0.0, 1.0] representing the power window.
        """
        if not params.enabled:
            return np.ones((height, width), dtype=np.float32)

        # Coordinate grid normalized [0, 1]
        y_grid, x_grid = np.mgrid[0:height, 0:width].astype(np.float32)
        x_norm = x_grid / float(width)
        y_norm = y_grid / float(height)

        # Center offset
        dx = x_norm - params.center_x
        dy = y_norm - params.center_y

        # Rotation
        angle_rad = np.radians(params.rotation_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        rot_x = cos_a * dx + sin_a * dy
        rot_y = -sin_a * dx + cos_a * dy

        rx = max(params.radius_x, 1e-4)
        ry = max(params.radius_y, 1e-4)

        if params.shape == "ellipse":
            # Normalized distance from center
            dist = np.sqrt(np.square(rot_x / rx) + np.square(rot_y / ry))
            feather = max(params.feather, 1e-4)
            mask = np.clip((1.0 + feather - dist) / feather, 0.0, 1.0)
            mask = np.where(dist <= 1.0, 1.0, mask)
        else: # rectangle
            dist_x = np.abs(rot_x) / rx
            dist_y = np.abs(rot_y) / ry
            dist = np.maximum(dist_x, dist_y)
            feather = max(params.feather, 1e-4)
            mask = np.clip((1.0 + feather - dist) / feather, 0.0, 1.0)
            mask = np.where(dist <= 1.0, 1.0, mask)

        # Smooth boundary
        kernel_size = int(max(width, height) * params.feather * 0.1) | 1
        if kernel_size > 1:
            mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)

        if params.invert:
            return 1.0 - mask
        return mask
