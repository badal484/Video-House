"""
Audio-Video Synchronization and Editorial Rhythm Engine.
Coordinates linked media clips, audio delay offsets, J-cuts, L-cuts,
and drift detection between visual frame indices and audio sample positions.
"""
import logging
from typing import Optional, Tuple
from uuid import UUID

from core.timeline.time_model import RationalTime
from core.timeline.timeline_models import Clip, Timeline, Track, TrackType

logger = logging.getLogger("studio.video_editing.sync_engine")


class AudioVideoSyncEngine:
    """
    Manages audio-video stream synchronization and split edits (J/L cuts).
    """

    @staticmethod
    def link_clips(video_clip: Clip, audio_clip: Clip) -> None:
        """Binds a video clip and audio clip together for synchronous editing."""
        video_clip.linked_clip_id = audio_clip.clip_id
        audio_clip.linked_clip_id = video_clip.clip_id

    @staticmethod
    def unlink_clips(clip_a: Clip, clip_b: Clip) -> None:
        """Removes the sync link between two clips, enabling independent trimming."""
        clip_a.linked_clip_id = None
        clip_b.linked_clip_id = None

    @staticmethod
    def create_j_cut(
        video_clip: Clip,
        audio_clip: Clip,
        lead_time_sec: float
    ) -> Tuple[Clip, Clip]:
        """
        J-Cut: Audio from the incoming scene begins before the visual cut occurs.
        Shifts audio start earlier by lead_time_sec and expands its source range.
        """
        lead_rt = RationalTime.from_seconds(lead_time_sec, audio_clip.timeline_start.rate)
        if audio_clip.source_in.to_seconds() < lead_time_sec:
            raise ValueError(f"Insufficient source media head for J-cut lead of {lead_time_sec}s")

        audio_clip.timeline_start = audio_clip.timeline_start - lead_rt
        audio_clip.timeline_duration = audio_clip.timeline_duration + lead_rt
        audio_clip.source_in = audio_clip.source_in - (lead_rt * audio_clip.speed)
        return (video_clip, audio_clip)

    @staticmethod
    def create_l_cut(
        video_clip: Clip,
        audio_clip: Clip,
        lag_time_sec: float
    ) -> Tuple[Clip, Clip]:
        """
        L-Cut: Audio from the outgoing scene continues past the visual cut into the next shot.
        Extends audio duration by lag_time_sec.
        """
        lag_rt = RationalTime.from_seconds(lag_time_sec, audio_clip.timeline_duration.rate)
        audio_clip.timeline_duration = audio_clip.timeline_duration + lag_rt
        audio_clip.source_out = audio_clip.source_in + (audio_clip.timeline_duration * audio_clip.speed)
        return (video_clip, audio_clip)

    @staticmethod
    def verify_sync(video_clip: Clip, audio_clip: Clip) -> float:
        """
        Calculates synchronization offset in seconds between linked video and audio clips.
        A result of 0.0 indicates perfect alignment.
        """
        v_start = video_clip.timeline_start.to_seconds()
        a_start = audio_clip.timeline_start.to_seconds()
        drift = round(a_start - v_start, 4)
        return drift
