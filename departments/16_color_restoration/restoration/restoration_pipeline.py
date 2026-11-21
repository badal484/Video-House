"""
Modular Restoration Pipeline Orchestrator for Department 16.
Executes configured chains of non-destructive restoration filters for:
- Low-quality mobile footage (Denoise + Retinex + Deblur)
- Old archival footage (Deinterlace + Deflicker + Inpaint Scratches + Stabilize)
- 2D Animation / Anime (Line-preserving bilateral + Contrast)
- Social media compressed footage (De-blocking + Edge enhancement)
"""
from typing import List, Optional
import numpy as np
from ..core.models import RestorationParameters, RestorationType
from .denoiser import VideoDenoiser
from .deblurrer import VideoDeblurrer
from .deinterlacer import VideoDeinterlacer
from .deflickerer import VideoDeflickerer
from .stabilizer import VideoStabilizer
from .inpaint_scratches import ScratchDustRemover
from .low_light import LowLightEnhancer


class RestorationPipeline:
    """
    Executes staged restoration filters on video frame sequences.
    """

    @classmethod
    def process_frames(
        cls,
        frames: List[np.ndarray],
        tasks: List[RestorationParameters]
    ) -> List[np.ndarray]:
        """
        Executes an ordered sequence of restoration tasks non-destructively across frames.
        """
        current_frames = [f.astype(np.float32).copy() for f in frames]

        for task in tasks:
            t_type = task.restoration_type

            if t_type == RestorationType.DEINTERLACE:
                current_frames = [VideoDeinterlacer.deinterlace_frame(f) for f in current_frames]

            elif t_type == RestorationType.DEFLICKER:
                current_frames = VideoDeflickerer.deflicker_sequence(current_frames)

            elif t_type == RestorationType.STABILIZE:
                current_frames = VideoStabilizer.stabilize_sequence(current_frames)

            elif t_type == RestorationType.SCRATCH_REMOVAL:
                current_frames = [ScratchDustRemover.inpaint_scratches(f) for f in current_frames]

            elif t_type == RestorationType.DENOISE:
                current_frames = [VideoDenoiser.denoise_frame_bilateral(f) for f in current_frames]

            elif t_type == RestorationType.DEBLUR:
                current_frames = [VideoDeblurrer.deblur_wiener(f) for f in current_frames]

            elif t_type == RestorationType.LOW_LIGHT_ENHANCE:
                current_frames = [LowLightEnhancer.enhance_clahe(f) for f in current_frames]

        return current_frames
