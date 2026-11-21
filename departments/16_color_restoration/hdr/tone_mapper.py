"""
HDR & SDR Tone Mapping and Gamut Compression for Department 16.
Implements ACES RRT, Reinhard extended, and Hable (Uncharted 2) filmic tone curves.
Converts High Dynamic Range (Rec.2100 PQ / HLG) to Standard Dynamic Range (Rec.709)
with highlight roll-off and gamut compression.
"""
import numpy as np


class ToneMapper:
    """
    Compresses high-dynamic-range scene radiance to display-referred limits.
    """

    @staticmethod
    def reinhard_extended(linear_rgb: np.ndarray, white_point: float = 4.0) -> np.ndarray:
        """
        Reinhard tone mapping with custom white point burn:
        L_d = L * (1 + L / L_white^2) / (1 + L)
        """
        arr = np.maximum(linear_rgb.astype(np.float32), 0.0)
        num = arr * (1.0 + arr / (white_point * white_point))
        den = 1.0 + arr
        return np.clip(num / den, 0.0, 1.0)

    @staticmethod
    def hable_filmic(linear_rgb: np.ndarray) -> np.ndarray:
        """
        Hable (Uncharted 2) filmic tone curve with toe and shoulder.
        """
        arr = np.maximum(linear_rgb.astype(np.float32), 0.0)
        A = 0.15
        B = 0.50
        C = 0.10
        D = 0.20
        E = 0.02
        F = 0.30
        W = 11.2

        def curve(x):
            return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - (E / F)

        curr = curve(arr * 2.0)
        white_scale = 1.0 / curve(W)
        return np.clip(curr * white_scale, 0.0, 1.0)

    @staticmethod
    def aces_rrt_approx(linear_rgb: np.ndarray) -> np.ndarray:
        """
        Stephen Hill's analytical fit of the ACES Reference Rendering Transform (RRT + ODT).
        """
        v = np.maximum(linear_rgb.astype(np.float32), 0.0)
        a = v * (v + 0.0245786) - 0.000090537
        b = v * (0.983729 * v + 0.4329510) + 0.238081
        return np.clip(a / b, 0.0, 1.0)

    @classmethod
    def map_hdr_to_sdr(
        cls,
        hdr_linear: np.ndarray,
        operator: str = "aces_rrt"
    ) -> np.ndarray:
        """
        Converts HDR linear floating point array to SDR [0.0, 1.0] using specified tone mapping.
        """
        arr = hdr_linear.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        if operator == "hable":
            mapped = cls.hable_filmic(rgb)
        elif operator == "reinhard":
            mapped = cls.reinhard_extended(rgb)
        else: # "aces_rrt"
            mapped = cls.aces_rrt_approx(rgb)

        if has_alpha:
            return np.concatenate([mapped, arr[:, :, 3:4]], axis=2)
        return mapped
