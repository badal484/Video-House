"""
Timeline Subtitles Bridge for Department 17.
Bridges subtitle cues and tracks into Department 05 OpenTimelineIO multi-track editorial assembly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from ..core.models import SubtitleCue, SubtitleTrack


class TimelineSubtitlesBridge:
    """Converts SubtitleTrack into OpenTimelineIO schema representations."""

    @classmethod
    def track_to_otio_dict(cls, track: SubtitleTrack, frame_rate: float = 24.0) -> Dict[str, Any]:
        """
        Converts a SubtitleTrack into an OpenTimelineIO Track dictionary representation
        with rational time markers.
        """
        clips: List[Dict[str, Any]] = []

        for cue in track.cues:
            start_frame = int(round(cue.start_time * frame_rate))
            duration_frames = max(1, int(round((cue.end_time - cue.start_time) * frame_rate)))

            clips.append({
                "schema": "Clip",
                "name": f"Subtitle_{cue.cue_index}",
                "source_range": {
                    "start_time": {"value": 0, "rate": frame_rate},
                    "duration": {"value": duration_frames, "rate": frame_rate},
                },
                "metadata": {
                    "text": cue.text,
                    "speaker_id": cue.speaker_id,
                    "cue_index": cue.cue_index,
                    "start_seconds": cue.start_time,
                    "end_seconds": cue.end_time,
                },
            })

        return {
            "schema": "Track",
            "name": f"Subtitles_{track.language_code.upper()}",
            "kind": "Text",
            "children": clips,
            "metadata": {
                "track_id": str(track.track_id),
                "language_code": track.language_code,
                "style_preset": track.style_preset.value,
            },
        }
