"""
Media Normalization and Analysis Proxy Pipeline.
Prepares video and audio media for multi-resolution temporal analysis:
- Inspects presentation timestamps (PTS), frame rates, and codecs.
- Produces lightweight 360p/720p analysis proxies to cap memory usage on Apple Silicon M4.
- Demuxes audio streams to 48kHz 16-bit uncompressed WAV.
- Cleans up intermediate analysis artifacts post-execution.
"""
import json
import logging
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger("studio.temporal_engine.normalization")

class MediaNormalizationService:
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "video_studio_temporal"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def probe_media(self, media_path: Path) -> Dict[str, Any]:
        """
        Extracts stream metadata, presentation timestamps, frame rates, and durations using ffprobe.
        """
        media_path = media_path.resolve()
        if not media_path.exists():
            raise FileNotFoundError(f"Media file {media_path} does not exist.")

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(media_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)
            format_info = info.get("format", {})
            streams = info.get("streams", [])

            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            fps = 24.0
            width = 0
            height = 0
            if video_stream:
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                r_frame_rate = video_stream.get("r_frame_rate", "24/1")
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / max(1.0, float(den))
                else:
                    fps = float(r_frame_rate) if r_frame_rate else 24.0

            duration = float(format_info.get("duration", 0.0))
            if duration == 0.0 and video_stream:
                duration = float(video_stream.get("duration", 0.0))

            return {
                "duration_seconds": duration,
                "fps": round(fps, 3),
                "width": width,
                "height": height,
                "aspect_ratio": f"{width}:{height}" if height else "16:9",
                "has_video": video_stream is not None,
                "has_audio": audio_stream is not None,
                "video_codec": video_stream.get("codec_name") if video_stream else None,
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None
            }
        except Exception as e:
            logger.warning(f"ffprobe probing failed on {media_path}: {e}")
            return {
                "duration_seconds": 1.0,
                "fps": 24.0,
                "width": 1920,
                "height": 1080,
                "aspect_ratio": "16:9",
                "has_video": True,
                "has_audio": False,
                "video_codec": None,
                "audio_codec": None
            }

    def generate_analysis_proxy(
        self, video_path: Path, max_height: int = 360
    ) -> Path:
        """
        Creates a downscaled analysis proxy for low-memory frame decoding.
        If video is already smaller or equal to max_height, returns the original path.
        """
        video_path = video_path.resolve()
        info = self.probe_media(video_path)
        if info["height"] <= max_height and info["height"] > 0:
            return video_path

        out_path = self.temp_dir / f"proxy_{video_path.stem}_{max_height}p_{uuid4().hex[:6]}.mp4"
        if out_path.exists():
            return out_path

        # Fast scale filter maintaining aspect ratio
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vf", f"scale=-2:{max_height}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-an",
            str(out_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_path.exists() and out_path.stat().st_size > 0:
                return out_path
        except Exception as e:
            logger.warning(f"Proxy generation failed ({e}); falling back to original media.")

        return video_path

    def extract_analysis_audio(self, media_path: Path) -> Optional[Path]:
        """
        Demuxes audio to standard 48kHz 16-bit uncompressed WAV in temp directory.
        """
        media_path = media_path.resolve()
        info = self.probe_media(media_path)
        if not info["has_audio"]:
            return None

        out_path = self.temp_dir / f"audio_{media_path.stem}_{uuid4().hex[:6]}.wav"
        if out_path.exists():
            return out_path

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(media_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "48000",
            "-ac", "2",
            str(out_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if out_path.exists() and out_path.stat().st_size > 0:
                return out_path
        except Exception as e:
            logger.warning(f"Audio extraction failed on {media_path}: {e}")

        return None

    def cleanup_artifacts(self, *paths: Optional[Path]) -> None:
        """Safely removes temporary proxy and audio artifacts."""
        for p in paths:
            if p and p.exists() and str(self.temp_dir) in str(p.resolve()):
                try:
                    p.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {p}: {e}")

