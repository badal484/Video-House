"""
3D Lattice & 1D LUT Interpolation Engine for Department 16.
Implements vectorized trilinear 3D interpolation with float32 accuracy and intensity blending.
"""
import numpy as np


class LUTInterpolator:
    """
    Interpolates 3D and 1D lookup tables against image arrays.
    """

    @staticmethod
    def apply_3d_lut(image: np.ndarray, lut_data: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        """
        Applies a 3D LUT (shape: [N, N, N, 3]) to image (shape: [H, W, 3] or [H, W, 4])
        using fast vectorized trilinear interpolation.
        Input values are expected in [0.0, 1.0].
        """
        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = np.clip(arr[:, :, :3] if has_alpha else arr, 0.0, 1.0)

        lut_size = lut_data.shape[0] # N (e.g. 33)
        scale = lut_size - 1

        # Continuous coordinates in LUT grid space
        r = rgb[:, :, 0] * scale
        g = rgb[:, :, 1] * scale
        b = rgb[:, :, 2] * scale

        # Base corner indices (lower bound)
        r0 = np.clip(np.floor(r).astype(np.int32), 0, scale - 1)
        g0 = np.clip(np.floor(g).astype(np.int32), 0, scale - 1)
        b0 = np.clip(np.floor(b).astype(np.int32), 0, scale - 1)

        # Upper corner indices
        r1 = np.minimum(r0 + 1, scale)
        g1 = np.minimum(g0 + 1, scale)
        b1 = np.minimum(b0 + 1, scale)

        # Fractional offsets
        dr = (r - r0)[:, :, np.newaxis]
        dg = (g - g0)[:, :, np.newaxis]
        db = (b - b0)[:, :, np.newaxis]

        # Fetch 8 cube corner samples: lut[r, g, b]
        c000 = lut_data[r0, g0, b0]
        c001 = lut_data[r0, g0, b1]
        c010 = lut_data[r0, g1, b0]
        c011 = lut_data[r0, g1, b1]
        c100 = lut_data[r1, g0, b0]
        c101 = lut_data[r1, g0, b1]
        c110 = lut_data[r1, g1, b0]
        c111 = lut_data[r1, g1, b1]

        # Trilinear interpolation along R, G, B
        c00 = c000 * (1.0 - db) + c001 * db
        c01 = c010 * (1.0 - db) + c011 * db
        c10 = c100 * (1.0 - db) + c101 * db
        c11 = c110 * (1.0 - db) + c111 * db

        c0 = c00 * (1.0 - dg) + c01 * dg
        c1 = c10 * (1.0 - dg) + c11 * dg

        sampled = c0 * (1.0 - dr) + c1 * dr

        # Intensity blend
        if intensity < 1.0:
            sampled = rgb * (1.0 - intensity) + sampled * intensity

        if has_alpha:
            return np.concatenate([sampled, arr[:, :, 3:4]], axis=2)
        return sampled

    @staticmethod
    def apply_1d_lut(image: np.ndarray, lut_data: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        """
        Applies a 1D LUT (shape: [N, 3] or [N,]) to image array.
        """
        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = np.clip(arr[:, :, :3] if has_alpha else arr, 0.0, 1.0)

        n = len(lut_data)
        indices = np.clip(rgb * (n - 1), 0, n - 1).astype(np.int32)

        if lut_data.ndim == 2 and lut_data.shape[1] == 3:
            out_r = lut_data[indices[:, :, 0], 0]
            out_g = lut_data[indices[:, :, 1], 1]
            out_b = lut_data[indices[:, :, 2], 2]
            sampled = np.stack([out_r, out_g, out_b], axis=2)
        else:
            sampled = lut_data[indices]

        if intensity < 1.0:
            sampled = rgb * (1.0 - intensity) + sampled * intensity

        if has_alpha:
            return np.concatenate([sampled, arr[:, :, 3:4]], axis=2)
        return sampled
