"""
Primary Color Corrector for Department 16.
Implements scene-referred linear operations:
- Photographic exposure adjustment (EV stops)
- Lift, Gamma, Gain (3-way color balance)
- Offset (uniform luminance/chrominance shift)
- Contrast with parametric pivot (default 18% middle gray)
- Correlated Color Temperature (Kelvin) & Tint
- Saturation & Vibrance
- Highlight recovery & Shadow roll-off
"""
import numpy as np
from ..core.models import PrimaryGradingParameters


class PrimaryCorrector:
    """
    Executes primary color corrections in linear scene-referred float32 space.
    """

    @staticmethod
    def apply_primary(image: np.ndarray, params: PrimaryGradingParameters) -> np.ndarray:
        """
        Applies primary grading parameters to a float32 linear image array.
        """
        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        # 1. Exposure (in EV stops: 2^EV)
        if params.exposure_ev != 0.0:
            rgb = rgb * np.power(2.0, params.exposure_ev)

        # 2. Lift / Gamma / Gain (ASC-CDL / Tone style)
        # Offset
        if any(v != 0.0 for v in params.offset):
            rgb = rgb + np.array(params.offset, dtype=np.float32)

        # Gain (highlights)
        if any(v != 1.0 for v in params.gain):
            rgb = rgb * np.array(params.gain, dtype=np.float32)

        # Lift (shadows: add lift scaled by (1 - lum))
        if any(v != 0.0 for v in params.lift):
            lum = 0.2126 * rgb[:, :, 0:1] + 0.7152 * rgb[:, :, 1:2] + 0.0722 * rgb[:, :, 2:3]
            shadow_mask = np.clip(1.0 - lum, 0.0, 1.0)
            rgb = rgb + np.array(params.lift, dtype=np.float32) * shadow_mask

        # Gamma (midtones)
        if any(v != 1.0 for v in params.gamma):
            gamma_arr = np.array(params.gamma, dtype=np.float32)
            # Safe positive power
            rgb = np.sign(rgb) * np.power(np.maximum(np.abs(rgb), 1e-7), 1.0 / np.maximum(gamma_arr, 0.1))

        # 3. Contrast & Pivot
        if params.contrast != 1.0:
            pivot = params.pivot
            rgb = pivot * np.power(np.maximum(rgb / pivot, 1e-7), params.contrast)

        # 4. Temperature (Kelvin) & Tint
        if params.temperature_k != 6500.0 or params.tint != 0.0:
            temp_ratio = params.temperature_k / 6500.0
            r_scale = np.power(temp_ratio, 0.6)
            b_scale = np.power(1.0 / temp_ratio, 0.6)
            g_scale = 1.0 + (params.tint / 100.0) * 0.1
            rgb[:, :, 0] *= r_scale
            rgb[:, :, 1] *= g_scale
            rgb[:, :, 2] *= b_scale

        # 5. Saturation & Vibrance
        if params.saturation != 1.0 or params.vibrance != 0.0:
            lum = 0.2126 * rgb[:, :, 0:1] + 0.7152 * rgb[:, :, 1:2] + 0.0722 * rgb[:, :, 2:3]
            sat_factor = params.saturation
            if params.vibrance != 0.0:
                # Vibrance affects low-saturation pixels more than high-saturation pixels
                max_c = np.maximum.reduce([rgb[:, :, 0:1], rgb[:, :, 1:2], rgb[:, :, 2:3]])
                min_c = np.minimum.reduce([rgb[:, :, 0:1], rgb[:, :, 1:2], rgb[:, :, 2:3]])
                current_sat = (max_c - min_c) / np.maximum(max_c, 1e-6)
                vibrance_boost = (1.0 - current_sat) * params.vibrance
                sat_factor += vibrance_boost

            rgb = lum + (rgb - lum) * sat_factor

        # 6. Highlights & Shadows adjustment
        if params.highlights != 0.0:
            # Highlight knee roll-off / recovery
            hl_mask = np.clip((rgb - 0.5) / 0.5, 0.0, 1.0)
            rgb = rgb + rgb * params.highlights * hl_mask * 0.3

        if params.shadows != 0.0:
            sh_mask = np.clip((0.5 - rgb) / 0.5, 0.0, 1.0)
            rgb = rgb + params.shadows * sh_mask * 0.2

        if has_alpha:
            return np.concatenate([rgb, arr[:, :, 3:4]], axis=2)
        return rgb
