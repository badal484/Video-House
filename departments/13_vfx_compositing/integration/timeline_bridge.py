"""
Timeline VFX Bridge
Integrates rendered VFX composite clips into OpenTimelineIO NLE timelines
(as clip replacements on track V1 or composited overlays on track V2).
"""
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from core.timeline.timeline_models import Clip, TrackType


class TimelineVFXBridge:
    """
    Connects Department 13 VFX outputs with Department 08 NLE timeline tracks.
    """

    @staticmethod
    def replace_clip_on_timeline(
        timeline_manager: Any,
        timeline_id: UUID,
        track_id: UUID,
        clip_index: int,
        vfx_asset_id: UUID,
        duration_seconds: float,
        timeline_start_seconds: float,
    ) -> Dict[str, Any]:
        """
        Replaces an existing offline clip with the rendered VFX master asset.
        """
        # Call timeline manager to insert clip into track
        new_clip = timeline_manager.add_clip_to_track(
            timeline_id=timeline_id,
            track_id=track_id,
            asset_id=vfx_asset_id,
            timeline_start_sec=timeline_start_seconds,
            duration_sec=duration_seconds,
        )
        return {
            "success": True,
            "action": "REPLACED_CLIP",
            "clip_id": str(new_clip.clip_id) if hasattr(new_clip, "clip_id") else str(vfx_asset_id),
            "track_id": str(track_id),
        }

    @staticmethod
    def add_vfx_overlay_track(
        timeline_manager: Any,
        timeline_id: UUID,
        vfx_asset_id: UUID,
        timeline_start_seconds: float,
        duration_seconds: float,
        track_name: str = "V2_VFX_OVERLAY",
    ) -> Dict[str, Any]:
        """
        Adds a dedicated V2 video track for overlaying alpha-channel VFX composites.
        """
        track = timeline_manager.add_track(
            timeline_id=timeline_id,
            name=track_name,
            track_type=TrackType.VIDEO,
        )
        clip = timeline_manager.add_clip_to_track(
            timeline_id=timeline_id,
            track_id=track.track_id,
            asset_id=vfx_asset_id,
            timeline_start_sec=timeline_start_seconds,
            duration_sec=duration_seconds,
        )
        return {
            "success": True,
            "action": "ADDED_VFX_OVERLAY",
            "track_id": str(track.track_id),
            "clip_id": str(clip.clip_id) if hasattr(clip, "clip_id") else str(vfx_asset_id),
        }

