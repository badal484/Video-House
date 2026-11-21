"""
Timeline Bridge: Conforming Generated Media for OpenTimelineIO Tracks
Department 15: 15_ai_generation
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from core.timeline.time_model import RationalTime


class TimelineGenerationBridge:
    """Prepares clip metadata to drop generated video and audio directly into NLE tracks."""

    @staticmethod
    def format_clip_for_timeline(
        asset_id: str,
        name: str,
        duration_sec: float,
        start_time_sec: float = 0.0,
        fps: int = 24,
    ) -> Dict[str, Any]:
        """Formats an asset into an OpenTimelineIO-compatible clip manifest."""
        return {
            "name": name,
            "asset_id": asset_id,
            "source_range": {
                "start_time": RationalTime(0, fps),
                "duration": RationalTime(int(round(duration_sec * fps)), fps),
            },
            "timeline_range": {
                "start_time": RationalTime(int(round(start_time_sec * fps)), fps),
                "duration": RationalTime(int(round(duration_sec * fps)), fps),
            },
        }
