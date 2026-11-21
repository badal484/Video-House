"""
Timeline Animation Adapter
Integrates rendered 2D animation masters into OpenTimelineIO NLE timelines
(as primary scene cuts on track V1 or transparent character overlays on track V3).
"""
from typing import Any, Dict, Optional
from uuid import UUID
from core.timeline.timeline_models import TrackType


class TimelineAnimationAdapter:
    """
    Connects Department 10 animation outputs with Department 08 NLE timeline tracks.
    """

    @staticmethod
    def insert_animation_to_timeline(
        timeline_manager: Any,
        timeline_id: Any,
        animation_asset_id: UUID,
        duration_seconds: float,
        timeline_start_seconds: float = 0.0,
        is_transparent_overlay: bool = True,
        track_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inserts an animation asset onto track V1 (full scene) or track V3 (transparent overlay).
        """
        target_name = track_name or ("V3_ANIMATION_OVERLAY" if is_transparent_overlay else "V1_PRIMARY_SCENE")
        tl_uuid = timeline_id.timeline_id if hasattr(timeline_id, "timeline_id") else timeline_id

        # Find or create target video track
        timeline = timeline_manager.get_timeline(tl_uuid)
        if timeline is None and hasattr(timeline_id, "tracks"):
            timeline = timeline_id

        target_track = None
        if timeline and hasattr(timeline, "tracks"):
            for track in timeline.tracks:
                if track.track_type == TrackType.VIDEO and track.name == target_name:
                    target_track = track
                    break

        if target_track is None:
            target_track = timeline_manager.add_track(
                timeline_id=tl_uuid,
                name=target_name,
                track_type=TrackType.VIDEO,
            )

        clip = timeline_manager.add_clip_to_track(
            timeline_id=tl_uuid,
            track_id=target_track.track_id,
            asset_id=animation_asset_id,
            timeline_start_sec=timeline_start_seconds,
            duration_sec=duration_seconds,
        )

        return {
            "success": True,
            "track_name": target_name,
            "track_id": str(target_track.track_id),
            "clip_id": str(clip.clip_id) if hasattr(clip, "clip_id") else str(animation_asset_id),
            "timeline_start_sec": timeline_start_seconds,
            "duration_sec": duration_seconds,
        }
