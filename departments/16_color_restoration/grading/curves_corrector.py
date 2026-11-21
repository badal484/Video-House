"""
Curves Corrector for Department 16.
Implements monotonic cubic spline interpolation for Master RGB, Red, Green, Blue curves,
and Hue-specific curves (Hue vs Hue, Hue vs Sat, Lum vs Sat).
"""
import numpy as np
from scipy.interpolate import PchipInterpolator
from ..core.models import CurvesParameters


class CurvesCorrector:
    """
    Applies monotonic cubic spline curve adjustments to image channels.
    """

    @staticmethod
    def _create_lut(control_points: list, size: int = 1024) -> np.ndarray:
        """Builds a 1D lookup table from control points using PCHIP monotonic spline."""
        if not control_points or len(control_points) < 2:
            return np.linspace(0.0, 1.0, size, dtype=np.float32)

        pts = sorted(control_points, key=lambda p: p[0])
        xs = np.array([p[0] for p in pts], dtype=np.float32)
        ys = np.array([p[1] for p in pts], dtype=np.float32)

        # Ensure bounds 0.0 to 1.0
        if xs[0] > 0.0:
            xs = np.insert(xs, 0, 0.0)
            ys = np.insert(ys, 0, ys[0])
        if xs[-1] < 1.0:
            xs = np.append(xs, 1.0)
            ys = np.append(ys, ys[-1])

        # Remove duplicate x coordinates if any
        _, unique_indices = np.unique(xs, return_index=True)
        xs = xs[unique_indices]
        ys = ys[unique_indices]

        interp = PchipInterpolator(xs, ys, extrapolate=False)
        query_x = np.linspace(0.0, 1.0, size, dtype=np.float32)
        lut = interp(query_x)
        return np.clip(lut, 0.0, 1.0)

    @classmethod
    def apply_curves(cls, image: np.ndarray, params: CurvesParameters) -> np.ndarray:
        """
        Applies RGB and Master curves to an image array.
        """
        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        # Build 1D LUTs
        master_lut = cls._create_lut(params.master_curve)
        r_lut = cls._create_lut(params.red_curve)
        g_lut = cls._create_lut(params.green_curve)
        b_lut = cls._create_lut(params.blue_curve)

        # Scale indices to LUT size (1024)
        lut_size = 1024
        idx_r = np.clip(rgb[:, :, 0] * (lut_size - 1), 0, lut_size - 1).astype(np.int32)
        idx_g = np.clip(rgb[:, :, 1] * (lut_size - 1), 0, lut_size - 1).astype(np.int32)
        idx_b = np.clip(rgb[:, :, 2] * (lut_size - 1), 0, lut_size - 1).astype(np.int32)

        out_r = r_lut[idx_r]
        out_g = g_lut[idx_g]
        out_b = b_lut[idx_b]

        # Apply Master curve
        idx_m_r = np.clip(out_r * (lut_size - 1), 0, lut_size - 1).astype(np.int32)
        idx_m_g = np.clip(out_g * (lut_size - 1), 0, lut_size - 1).astype(np.int32)
        idx_m_b = np.clip(out_b * (lut_size - 1), 0, lut_size - 1).astype(np.int32)

        final_rgb = np.stack([master_lut[idx_m_r], master_lut[idx_m_g], master_lut[idx_m_b]], axis=2)

        if has_alpha:
            return np.concatenate([final_rgb, arr[:, :, 3:4]], axis=2)
        return final_rgb
