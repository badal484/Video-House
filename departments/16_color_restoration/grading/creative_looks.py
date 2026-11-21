"""
Creative Looks & Film Emulation Engine for Department 16.
Implements standard cinematic looks as parametric operations:
- Teal & Orange (Blockbuster high-contrast dual-tone)
- Bleach Bypass (Silver retention, desaturated crushed shadows)
- Film Stock Emulation (Kodak 2383 / Fuji 3513 print characteristics)
- Monochrome High Contrast (Noir / Silver halide)
- Warm Sunset & Golden Hour
- Cool Sci-Fi / Cyberpunk
"""
import numpy as np


class CreativeLooksEngine:
    """
    Applies cinematic and film look presets as adjustable operations.
    """

    @staticmethod
    def apply_look(image: np.ndarray, look_name: str, intensity: float = 1.0) -> np.ndarray:
        """
        Applies a named creative look with an intensity blend slider [0.0, 1.0].
        """
        arr = image.astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        norm_name = look_name.lower().replace(" ", "_").replace("-", "_")
        graded = rgb.copy()

        # Compute luminance
        lum = 0.2126 * rgb[:, :, 0:1] + 0.7152 * rgb[:, :, 1:2] + 0.0722 * rgb[:, :, 2:3]

        if "teal_and_orange" in norm_name or "blockbuster" in norm_name:
            # Teal in shadows, warm orange in highlights
            shadow_mask = np.clip((0.6 - lum) / 0.6, 0.0, 1.0)
            hl_mask = np.clip((lum - 0.3) / 0.7, 0.0, 1.0)

            # Push shadows to Teal (Red down, Blue & Green up)
            graded[:, :, 0] -= 0.15 * shadow_mask[:, :, 0]
            graded[:, :, 1] += 0.05 * shadow_mask[:, :, 0]
            graded[:, :, 2] += 0.18 * shadow_mask[:, :, 0]

            # Push highlights to Warm Orange (Red up, Blue down)
            graded[:, :, 0] += 0.18 * hl_mask[:, :, 0]
            graded[:, :, 1] += 0.08 * hl_mask[:, :, 0]
            graded[:, :, 2] -= 0.12 * hl_mask[:, :, 0]

        elif "bleach_bypass" in norm_name:
            # High contrast, low saturation, crushed blacks
            desat = lum + (rgb - lum) * 0.35
            # S-curve contrast
            contrast = np.where(
                desat < 0.5,
                2.0 * np.square(desat),
                1.0 - 2.0 * np.square(1.0 - desat)
            )
            graded = contrast

        elif "film_stock" in norm_name or "kodak_2383" in norm_name:
            # Kodak 2383: warm highlights, rich cyan-green shadows, roll-off toe
            graded[:, :, 0] *= 1.08 # slight warm red
            graded[:, :, 2] *= 0.94 # slight yellow/amber shift
            # Toe soft compression
            graded = np.where(graded < 0.1, graded * 0.85, graded)
            # Slight saturation boost in midtones
            mid_mask = np.sin(np.clip(lum, 0.0, 1.0) * np.pi)
            graded = lum + (graded - lum) * (1.0 + 0.2 * mid_mask)

        elif "monochrome" in norm_name or "black_and_white" in norm_name:
            # High-contrast photographic B&W
            bw = 0.299 * rgb[:, :, 0:1] + 0.587 * rgb[:, :, 1:2] + 0.114 * rgb[:, :, 2:3]
            # S-curve
            bw_contrast = np.clip(np.power(bw, 1.25) * 1.05, 0.0, 1.0)
            graded = np.repeat(bw_contrast, 3, axis=2)

        elif "warm_sunset" in norm_name or "golden_hour" in norm_name:
            graded[:, :, 0] *= 1.25 # rich red/orange
            graded[:, :, 1] *= 1.08 # golden amber
            graded[:, :, 2] *= 0.85 # deep golden shadows
            # Warm glow
            graded = np.clip(graded, 0.0, 1.5)

        elif "cool_scifi" in norm_name or "cyberpunk" in norm_name:
            graded[:, :, 0] *= 0.85
            graded[:, :, 1] *= 1.10 # neon cyan
            graded[:, :, 2] *= 1.30 # deep electric blue

        # Blend via intensity slider [0.0, 1.0]
        final_rgb = rgb * (1.0 - intensity) + graded * intensity
        final_rgb = np.clip(final_rgb, 0.0, 2.0)

        if has_alpha:
            return np.concatenate([final_rgb, arr[:, :, 3:4]], axis=2)
        return final_rgb
