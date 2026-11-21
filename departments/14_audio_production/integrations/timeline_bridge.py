"""
Timeline Bridge: Bidirectional synchronization between OpenTimelineIO and AudioSession
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional
from core.timeline.time_model import RationalTime
from ..core.session_models import (
    AudioSession,
    AudioTrack,
    AudioClip,
    AudioTrackType,
)


class TimelineAudioBridge:
    """Synchronizes audio tracks between the NLE timeline and the AudioSession."""

    @staticmethod
    def timeline_to_audio_session(timeline: Any, project_id: str = "default_project") -> AudioSession:
        """
        Extracts audio tracks and clips from an OpenTimelineIO or Studio Timeline object.
        """
        session = AudioSession(
            project_id=project_id,
            name=f"Timeline Audio Session - {getattr(timeline, 'name', 'Untitled')}",
        )

        # Iterate over tracks
        tracks = getattr(timeline, "tracks", [])
        if isinstance(tracks, dict):
            tracks = list(tracks.values())

        for trk in tracks:
            # Check if audio track
            kind = getattr(trk, "kind", "").lower()
            if kind == "audio" or "audio" in str(getattr(trk, "name", "")).lower():
                trk_name = getattr(trk, "name", "Audio Track")
                
                # Determine role from name
                name_lower = trk_name.lower()
                if "diag" in name_lower or "dialogue" in name_lower or "voice" in name_lower:
                    ttype = AudioTrackType.DIALOGUE
                elif "music" in name_lower or "score" in name_lower:
                    ttype = AudioTrackType.MUSIC
                elif "foley" in name_lower:
                    ttype = AudioTrackType.FOLEY
                else:
                    ttype = AudioTrackType.SOUND_EFFECTS

                session_trk = session.add_track(name=trk_name, track_type=ttype)

                # Iterate clips
                clips = getattr(trk, "clips", [])
                if isinstance(clips, dict):
                    clips = list(clips.values())

                for c in clips:
                    start_sec = 0.0
                    dur_sec = 1.0

                    # Support RationalTime or float seconds
                    t_range = getattr(c, "source_range", None)
                    if t_range:
                        start_time = getattr(t_range, "start_time", None)
                        duration = getattr(t_range, "duration", None)
                        if hasattr(start_time, "to_seconds"):
                            start_sec = start_time.to_seconds()
                        elif isinstance(start_time, (int, float)):
                            start_sec = float(start_time)
                        if hasattr(duration, "to_seconds"):
                            dur_sec = duration.to_seconds()
                        elif isinstance(duration, (int, float)):
                            dur_sec = float(duration)

                    audio_clip = AudioClip(
                        track_id=session_trk.track_id,
                        asset_id=str(getattr(c, "asset_id", uuid.uuid4())),
                        name=getattr(c, "name", "Timeline Clip"),
                        start_time_sec=start_sec,
                        duration_sec=dur_sec,
                    )
                    session_trk.add_clip(audio_clip)

        return session
