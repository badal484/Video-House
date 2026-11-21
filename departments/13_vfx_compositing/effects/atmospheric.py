"""
Atmospheric Effects & Light Wrapping Module
Implements optical light wrap (background bleed), procedural atmospheric fog,
and particle simulations (dust motes, sparks).
"""
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class AtmosphericEffects:
    """
    Renders atmospheric integration effects to seat composite elements photorealistically.
    """

    @staticmethod
    def apply_light_wrap(
        foreground_rgba: np.ndarray,
        background_rgb: np.ndarray,
        wrap_amount: float = 0.5,
        wrap_radius: int = 15,
    ) -> np.ndarray:
        """
        Bleeds background luminance into foreground edges where alpha transitions.
        """
        fg_float = foreground_rgba.astype(np.float32)
        if foreground_rgba.dtype == np.uint8:
            fg_float /= 255.0

        bg_float = background_rgb.astype(np.float32)
        if background_rgb.dtype == np.uint8:
            bg_float /= 255.0

        fg_rgb = fg_float[:, :, :3]
        alpha = fg_float[:, :, 3:4]

        # Invert alpha and blur to create background bleed mask onto foreground edges
        ksize = (wrap_radius * 2 + 1, wrap_radius * 2 + 1)
        blurred_bg = cv2.GaussianBlur(bg_float[:, :, :3], ksize, wrap_radius / 2.0)

        inv_alpha = 1.0 - alpha[:, :, 0]
        blurred_inv_alpha = cv2.GaussianBlur(inv_alpha, ksize, wrap_radius / 2.0)
        edge_weight = np.clip(blurred_inv_alpha[:, :, np.newaxis] * alpha * wrap_amount * 2.0, 0.0, 1.0)

        wrapped_rgb = fg_rgb + blurred_bg * edge_weight
        out_rgba = np.concatenate([np.clip(wrapped_rgb, 0.0, 1.0), alpha], axis=2)

        if foreground_rgba.dtype == np.uint8:
            return (out_rgba * 255.0).astype(np.uint8)
        return out_rgba

    @staticmethod
    def generate_dust_particles(
        resolution: Tuple[int, int],  # (height, width)
        count: int = 150,
        seed: int = 42,
        intensity: float = 0.8,
    ) -> np.ndarray:
        """
        Generates floating atmospheric dust particles with soft bokeh circles.
        Returns 4-channel RGBA float32 array.
        """
        h, w = resolution
        rng = np.random.RandomState(seed)
        particle_layer = np.zeros((h, w, 4), dtype=np.float32)

        xs = rng.uniform(0, w, count)
        ys = rng.uniform(0, h, count)
        radii = rng.uniform(1.5, 6.0, count)
        opacities = rng.uniform(0.1, intensity, count)

        for x, y, r, op in zip(xs, ys, radii, opacities):
            center = (int(x), int(y))
            # Draw glowing white particle
            overlay = np.zeros((h, w), dtype=np.float32)
            cv2.circle(overlay, center, int(r), 1.0, -1)
            ksize = int(np.ceil(r * 3.0)) | 1
            blurred = cv2.GaussianBlur(overlay, (ksize, ksize), r / 1.5)
            
            particle_layer[:, :, :3] += blurred[:, :, np.newaxis] * 1.0
            particle_layer[:, :, 3] += blurred * op

        particle_layer = np.clip(particle_layer, 0.0, 1.0)
        return particle_layer
