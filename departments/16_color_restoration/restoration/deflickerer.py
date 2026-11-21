"""
Deflickerer Engine for Department 16.
Eliminates temporal luminance fluctuations caused by vintage camera shutters,
fluorescent light strobing, or time-lapse exposure steps.
"""
import numpy as np


class VideoDeflickerer:
    """
    Stabilizes temporal exposure fluctuations across video frame sequences.
    """

    @staticmethod
    def deflicker_sequence(
        frames: list[np.ndarray],
        window_size: int = 5
    ) -> list[np.ndarray]:
        """
        Applies a rolling temporal moving average to frame mean luminance.
        """
        if len(frames) <= 2:
            return frames

        # Compute average luminance of each frame
        means = []
        for f in frames:
            lum = 0.2126 * f[:, :, 0] + 0.7152 * f[:, :, 1] + 0.0722 * f[:, :, 2]
            means.append(float(np.mean(lum)))

        # Moving average target luminance
        target_means = []
        n = len(means)
        radius = window_size // 2
        for i in range(n):
            start = max(0, i - radius)
            end = min(n, i + radius + 1)
            target_means.append(float(np.mean(means[start:end])))

        # Scale frames to match target luminance
        deflickered = []
        for i, f in enumerate(frames):
            cur_mean = max(means[i], 1e-4)
            tgt_mean = target_means[i]
            scale = tgt_mean / cur_mean
            # Limit scale to reasonable bounds [0.8, 1.25]
            scale = float(np.clip(scale, 0.8, 1.25))
            deflickered.append(np.clip(f * scale, 0.0, 1.0))

        return deflickered
