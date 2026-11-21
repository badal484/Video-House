"""
3D HSL & Skin-Tone Secondary Qualifier for Department 16.
Isolates specific color ranges (Hue, Saturation, Luminance) with soft edge feathering,
allowing selective adjustments (e.g. skin-tone warming, foliage desaturation, sky deepening).
"""
import cv2
import numpy as np
from ..core.models import SecondaryQualifierParameters


class SecondaryQualifier:
    """
    Isolates regions by color properties (HSL) and applies selective adjustments.
    """

    @staticmethod
    def generate_mask(image_rgb: np.ndarray, params: SecondaryQualifierParameters) -> np.ndarray:
        """
        Generates a continuous float32 alpha matte [0.0, 1.0] matching the HSL qualifier bounds.
        """
        arr = np.clip(image_rgb[:, :, :3], 0.0, 1.0).astype(np.float32)
        # Convert RGB to HLS in OpenCV (expects uint8 or float32 [0, 1])
        hls = cv2.cvtColor(arr, cv2.COLOR_RGB2HLS)
        # OpenCV HLS: H in [0, 360], L in [0, 1], S in [0, 1]
        h = hls[:, :, 0]
        l = hls[:, :, 1]
        s = hls[:, :, 2]

        # 1. Hue Distance (circular angular difference on 360 deg wheel)
        h_diff = np.abs(h - params.hue_center)
        h_dist = np.minimum(h_diff, 360.0 - h_diff)
        h_half_w = params.hue_width / 2.0
        h_soft = max(params.hue_softness, 1e-4)

        h_mask = np.clip((h_half_w + h_soft - h_dist) / h_soft, 0.0, 1.0)
        h_mask = np.where(h_dist <= h_half_w, 1.0, h_mask)

        # 2. Saturation Window
        s_soft = max(params.sat_softness, 1e-4)
        s_mask_low = np.clip((s - (params.sat_min - s_soft)) / s_soft, 0.0, 1.0)
        s_mask_high = np.clip(((params.sat_max + s_soft) - s) / s_soft, 0.0, 1.0)
        s_mask = np.minimum(s_mask_low, s_mask_high)

        # 3. Luminance Window
        l_soft = max(params.lum_softness, 1e-4)
        l_mask_low = np.clip((l - (params.lum_min - l_soft)) / l_soft, 0.0, 1.0)
        l_mask_high = np.clip(((params.lum_max + l_soft) - l) / l_soft, 0.0, 1.0)
        l_mask = np.minimum(l_mask_low, l_mask_high)

        # Combined Qualifier Matte
        combined_mask = h_mask * s_mask * l_mask

        # Apply slight spatial blur to eliminate pixel chatter
        blurred_mask = cv2.GaussianBlur(combined_mask, (5, 5), 1.5)

        if params.invert_mask:
            return 1.0 - blurred_mask
        return blurred_mask

    @classmethod
    def apply_qualifier(cls, image: np.ndarray, params: SecondaryQualifierParameters) -> np.ndarray:
        """
        Isolates color selection and applies gain, saturation, and hue adjustments inside matte.
        """
        if not params.enabled:
            return image

        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        mask = cls.generate_mask(rgb, params)[:, :, np.newaxis] # (H, W, 1)

        # Modified RGB inside mask
        adjusted_rgb = rgb.copy()

        # Gain adjustment
        if any(g != 1.0 for g in params.gain):
            adjusted_rgb = adjusted_rgb * np.array(params.gain, dtype=np.float32)

        # Saturation adjustment
        if params.saturation != 1.0:
            lum = 0.2126 * adjusted_rgb[:, :, 0:1] + 0.7152 * adjusted_rgb[:, :, 1:2] + 0.0722 * adjusted_rgb[:, :, 2:3]
            adjusted_rgb = lum + (adjusted_rgb - lum) * params.saturation

        # Blend original and adjusted via qualifier mask
        final_rgb = rgb * (1.0 - mask) + adjusted_rgb * mask

        if has_alpha:
            return np.concatenate([final_rgb, arr[:, :, 3:4]], axis=2)
        return final_rgb
