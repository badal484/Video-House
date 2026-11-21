"""
Preview and Playback Engine.
Provides low-latency proxy-based preview generation, frame caching,
thumbnail scrub generation, and incremental preview rendering.
"""
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, Optional
from uuid import UUID

from core.assets.database import AssetDatabase
from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import RenderJob, Timeline
from .render_engine import RenderEngine

logger = logging.getLogger("studio.video_editing.preview")


class PreviewEngine:
    """
    Fast interactive preview and scrub caching service.
    """

    def __init__(
        self,
        db: Optional[AssetDatabase] = None,
        render_engine: Optional[RenderEngine] = None,
        cache_dir: Optional[str] = None
    ):
        self.db = db
        self.renderer = render_engine or RenderEngine(db)
        self.cache_dir = Path(cache_dir) if cache_dir else Path("temp/preview_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._frame_cache: Dict[str, bytes] = {}

    def generate_timeline_preview(
        self,
        timeline: Timeline,
        preview_resolution_width: int = 640,
        preview_resolution_height: int = 360
    ) -> RenderJob:
        """
        Renders a lightweight, high-speed proxy video of the timeline for responsive UI playback.
        """
        h = hashlib.sha256(f"{timeline.timeline_id}_{timeline.version}".encode()).hexdigest()[:12]
        output_path = str(self.cache_dir / f"prev_{timeline.timeline_id}_{h}.mp4")

        # If cache exists and is fresh, reuse
        if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
            logger.info(f"Reusing cached preview -> {output_path}")
            return RenderJob(
                render_id=UUID(int=0),
                project_id=timeline.project_id,
                timeline_id=timeline.timeline_id,
                output_path=output_path,
                is_preview=True,
                status="COMPLETED",
                progress=1.0
            )

        job = self.renderer.render_timeline(
            timeline=timeline,
            output_path=output_path,
            is_preview=True,
            format_preset="PREVIEW_FAST_360P"
        )
        return job

    def extract_frame_at_time(
        self,
        media_path: str,
        timestamp_sec: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extracts an exact frame from media for thumbnail scrubbing or timeline playhead display.
        """
        if not output_path:
            h = hashlib.sha256(f"{media_path}_{timestamp_sec}".encode()).hexdigest()[:12]
            output_path = str(self.cache_dir / f"frame_{h}.jpg")

        if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
            return output_path

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{timestamp_sec:.3f}",
            "-i", media_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
