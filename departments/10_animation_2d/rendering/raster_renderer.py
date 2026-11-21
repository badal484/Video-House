"""
Raster Animation Renderer
Renders animation frames to RGBA arrays via Pillow and streams directly
to FFmpeg for transparent Apple ProRes 4444 and WebM video export.
"""
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from ..core.models import AnimationScene


class RasterAnimationRenderer:
    """
    Renders 32-bit RGBA raster animation frames and encodes transparent video masters.
    """

    @staticmethod
    def render_video(
        frames: List[np.ndarray],  # List of 4-channel BGRA uint8 arrays
        output_path: str,
        fps: float = 24.0,
        codec: str = "prores_ks",  # "prores_ks" or "libvpx-vp9"
    ) -> Dict[str, Any]:
        """
        Pipes raw BGRA frames directly to FFmpeg with alpha channel preservation.
        """
        if not frames:
            raise ValueError("No frames provided for video rendering.")

        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        h, w = frames[0].shape[:2]

        if codec == "prores_ks":
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{w}x{h}",
                "-pix_fmt", "bgra",
                "-r", str(fps),
                "-i", "-",
                "-c:v", "prores_ks",
                "-profile:v", "4",  # ProRes 4444
                "-pix_fmt", "yuva444p10le",
                str(out_p),
            ]
        elif codec == "libvpx-vp9":
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{w}x{h}",
                "-pix_fmt", "bgra",
                "-r", str(fps),
                "-i", "-",
                "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p",
                "-b:v", "2M",
                str(out_p),
            ]
        else:
            # Standard MP4 fallback (no alpha)
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{w}x{h}",
                "-pix_fmt", "bgra",
                "-r", str(fps),
                "-i", "-",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(out_p),
            ]

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for frame in frames:
            proc.stdin.write(frame.tobytes())

        proc.stdin.flush()
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg animation render failed: {stderr.decode('utf-8', errors='ignore')}")

        return {
            "status": "COMPLETED",
            "output_path": str(out_p),
            "frame_count": len(frames),
            "resolution": [w, h],
            "fps": fps,
            "codec": codec,
        }
