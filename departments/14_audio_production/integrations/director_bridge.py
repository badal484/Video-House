"""
Director Bridge: Synthesizing AudioSessions from AI Director ProductionBlueprints
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from ..core.session_models import (
    AudioSession,
    AudioTrack,
    AudioClip,
    AudioTrackType,
    AudioEffectConfig,
)


class DirectorAudioBridge:
    """Translates creative direction blueprints into fully configured AudioSessions."""

    @staticmethod
    def blueprint_to_audio_session(blueprint_data: Dict[str, Any], project_id: str) -> AudioSession:
        """
        Creates an AudioSession with dedicated tracks for Dialogue, Music, and SFX
        configured to match the creative pace, mood, and sound design of the production blueprint.
        """
        session = AudioSession(
            project_id=project_id,
            name=blueprint_data.get("title", f"Director Audio Session - {project_id[:8]}"),
            tempo_bpm=float(blueprint_data.get("tempo_bpm", 120.0)),
        )

        # 1. Dialogue Track
        diag_track = session.add_track(
            name="Dialogue & Voiceover",
            track_type=AudioTrackType.DIALOGUE,
            gain_db=0.0,
        )
        # Add highpass rumble filter and compressor to dialogue track
        diag_track.fx_chain.append(
            AudioEffectConfig(effect_type="highpass", parameters={"cutoff_hz": 80.0})
        )
        diag_track.fx_chain.append(
            AudioEffectConfig(effect_type="compressor", parameters={"threshold_db": -20.0, "ratio": 3.0})
        )

        # 2. Music Bed Track
        music_track = session.add_track(
            name="Music Bed",
            track_type=AudioTrackType.MUSIC,
            gain_db=-6.0,
        )
        music_track.fx_chain.append(
            AudioEffectConfig(effect_type="compressor", parameters={"threshold_db": -16.0, "ratio": 2.0})
        )

        # 3. Sound Effects & Foley Track
        sfx_track = session.add_track(
            name="Sound Effects & Impacts",
            track_type=AudioTrackType.SOUND_EFFECTS,
            gain_db=-2.0,
        )
        sfx_track.fx_chain.append(
            AudioEffectConfig(effect_type="reverb", parameters={"wet_level": 0.2})
        )

        # 4. Ambience Track
        amb_track = session.add_track(
            name="Environmental Ambience",
            track_type=AudioTrackType.AMBIENCE,
            gain_db=-12.0,
        )

        # Parse audio cues if provided in blueprint
        cues = blueprint_data.get("audio_cues", [])
        for cue in cues:
            start_t = float(cue.get("start_time_sec", 0.0))
            dur = float(cue.get("duration_sec", 2.0))
            cue_type = cue.get("type", "sfx").lower()
            
            clip = AudioClip(
                track_id="",
                name=cue.get("description", "Audio Cue"),
                start_time_sec=start_t,
                duration_sec=dur,
                gain_db=float(cue.get("gain_db", 0.0)),
            )

            if "diag" in cue_type or "voice" in cue_type:
                diag_track.add_clip(clip)
            elif "music" in cue_type:
                music_track.add_clip(clip)
            elif "amb" in cue_type:
                amb_track.add_clip(clip)
            else:
                sfx_track.add_clip(clip)

        return session
