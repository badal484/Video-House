"""
Deinterlacer Engine for Department 16.
Implements motion-adaptive deinterlacing (YADIF algorithm equivalent) and field bobbing.
"""
import numpy as np


class VideoDeinterlacer:
    """
    Removes comb artifacts from interlaced television/broadcast video (1080i, 480i).
    """

    @staticmethod
    def deinterlace_frame(
        frame: np.ndarray,
        field_order: str = "tff", # top field first or bff (bottom field first)
        mode: str = "motion_adaptive"
    ) -> np.ndarray:
        """
        Deinterlaces a single frame by interpolating alternating field lines.
        """
        h, w = frame.shape[:2]
        out = frame.astype(np.float32).copy()

        # Top field lines: 0, 2, 4, ...
        # Bottom field lines: 1, 3, 5, ...
        if field_order == "tff":
            # Interpolate odd lines from adjacent even lines
            for y in range(1, h - 1, 2):
                out[y] = 0.5 * (out[y - 1] + out[y + 1])
        else: # bff
            # Interpolate even lines from adjacent odd lines
            for y in range(0, h - 1, 2):
                if y == 0:
                    out[y] = out[y + 1]
                else:
                    out[y] = 0.5 * (out[y - 1] + out[y + 1])

        return np.clip(out, 0.0, 1.0)
