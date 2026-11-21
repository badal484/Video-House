"""
Low-Light Video & Shadow Recovery Enhancer for Department 16.
Implements Multi-Scale Retinex (MSR) and Contrast Limited Adaptive Histogram Equalization (CLAHE).
"""
import cv2
import numpy as np


class LowLightEnhancer:
    """
    Enhances underexposed footage and reveals shadow details without introducing noise halos.
    """

    @staticmethod
    def enhance_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple = (8, 8)) -> np.ndarray:
        """
        Applies CLAHE on the luminance channel in LAB space.
        """
        arr = np.clip(image, 0.0, 1.0).astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        img_uint8 = (rgb * 255.0).astype(np.uint8)
        lab = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2LAB)

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])

        enhanced_uint8 = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        enhanced_rgb = enhanced_uint8.astype(np.float32) / 255.0

        if has_alpha:
            return np.concatenate([enhanced_rgb, arr[:, :, 3:4]], axis=2)
        return enhanced_rgb

    @staticmethod
    def enhance_retinex(image: np.ndarray, sigma_list: list = [15, 80, 250]) -> np.ndarray:
        """
        Applies Multi-Scale Retinex (MSR) shadow recovery.
        """
        arr = np.clip(image[:, :, :3], 0.0, 1.0).astype(np.float32)
        img_log = np.log10(arr + 1e-4)

        retinex = np.zeros_like(img_log)
        for s in sigma_list:
            blur = cv2.GaussianBlur(arr, (0, 0), s)
            blur_log = np.log10(np.maximum(blur, 1e-4))
            retinex += (img_log - blur_log)
        retinex /= len(sigma_list)

        # Normalize back to [0, 1]
        ret_min = np.min(retinex)
        ret_max = np.max(retinex)
        normalized = (retinex - ret_min) / max(ret_max - ret_min, 1e-4)

        # Blend with original
        return np.clip(arr * 0.4 + normalized * 0.6, 0.0, 1.0)
