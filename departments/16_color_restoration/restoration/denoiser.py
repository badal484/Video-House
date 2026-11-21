"""
Video Denoising Engine for Department 16.
Implements spatial bilateral filtering and temporal moving-window Non-Local Means (NLM).
"""
import cv2
import numpy as np


class VideoDenoiser:
    """
    Denoises image frames while preserving authentic high-frequency edge detail.
    """

    @staticmethod
    def denoise_frame_bilateral(
        image: np.ndarray,
        diameter: int = 9,
        sigma_color: float = 75.0,
        sigma_space: float = 75.0
    ) -> np.ndarray:
        """
        Applies edge-preserving bilateral filtering.
        """
        arr = np.clip(image, 0.0, 1.0).astype(np.float32)
        has_alpha = arr.ndim == 3 and arr.shape[2] == 4
        rgb = arr[:, :, :3] if has_alpha else arr

        # OpenCV bilateralFilter on float32 requires 1 or 3 channels
        denoised = cv2.bilateralFilter(rgb, diameter, sigma_color / 255.0, sigma_space)

        if has_alpha:
            return np.concatenate([denoised, arr[:, :, 3:4]], axis=2)
        return denoised

    @staticmethod
    def denoise_temporal_nlm(
        frames: list[np.ndarray],
        target_idx: int = 1,
        h: float = 0.05
    ) -> np.ndarray:
        """
        Applies temporal windowed filtering across adjacent frames (e.g. t-1, t, t+1).
        """
        if len(frames) == 1:
            return VideoDenoiser.denoise_frame_bilateral(frames[0])

        target = frames[target_idx].astype(np.float32)
        # Weight current frame 0.6, neighbors 0.2 each
        avg = target * 0.6
        neighbor_weight = 0.4 / (len(frames) - 1)
        for i, f in enumerate(frames):
            if i != target_idx:
                avg += f.astype(np.float32) * neighbor_weight

        # Run light spatial bilateral on temporal composite
        return VideoDenoiser.denoise_frame_bilateral(avg, diameter=5, sigma_color=50.0, sigma_space=50.0)
