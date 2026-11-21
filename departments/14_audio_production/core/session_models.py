"""
Canonical Audio Session and Multitrack Data Models
Department 14: 14_audio_production
"""
from __future__ import annotations

import math
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.timeline.time_model import RationalTime, TimeRange


class AudioTrackType(str, Enum):
    DIALOGUE = "DIALOGUE"
    VOICE_OVER = "VOICE_OVER"
    NARRATION = "NARRATION"
    MUSIC = "MUSIC"
    SOUND_EFFECTS = "SOUND_EFFECTS"
    FOLEY = "FOLEY"
    AMBIENCE = "AMBIENCE"
    ROOM_TONE = "ROOM_TONE"
    BUS = "BUS"
    MASTER_BUS = "MASTER_BUS"


class ChannelLayout(str, Enum):
    MONO = "MONO"
    STEREO = "STEREO"
    SURROUND_5_1 = "SURROUND_5_1"


class FadeCurve(str, Enum):
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"
    LOGARITHMIC = "LOGARITHMIC"
    S_CURVE = "S_CURVE"
    EQUAL_POWER = "EQUAL_POWER"


class LoudnessStandard(str, Enum):
    YOUTUBE = "YOUTUBE"
    SPOTIFY = "SPOTIFY"
    APPLE_PODCASTS = "APPLE_PODCASTS"
    EBU_R128 = "EBU_R128"
    ATSC_A85 = "ATSC_A85"
    FILM_THEATRICAL = "FILM_THEATRICAL"

    @property
    def target_lufs(self) -> float:
        targets = {
            LoudnessStandard.YOUTUBE: -14.0,
            LoudnessStandard.SPOTIFY: -14.0,
            LoudnessStandard.APPLE_PODCASTS: -16.0,
            LoudnessStandard.EBU_R128: -23.0,
            LoudnessStandard.ATSC_A85: -24.0,
            LoudnessStandard.FILM_THEATRICAL: -24.0,
        }
        return targets[self]

    @property
    def max_true_peak_db(self) -> float:
        peaks = {
            LoudnessStandard.YOUTUBE: -1.0,
            LoudnessStandard.SPOTIFY: -1.0,
            LoudnessStandard.APPLE_PODCASTS: -1.0,
            LoudnessStandard.EBU_R128: -1.0,
            LoudnessStandard.ATSC_A85: -2.0,
            LoudnessStandard.FILM_THEATRICAL: -2.0,
        }
        return peaks[self]


class AutomationPoint(BaseModel):
    time_sec: float
    value: float
    curve: FadeCurve = FadeCurve.LINEAR


class AutomationLane(BaseModel):
    lane_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parameter: str  # gain_db, pan, cutoff_hz, reverb_wet, etc.
    points: List[AutomationPoint] = Field(default_factory=list)

    def evaluate(self, time_sec: float, default_value: float = 0.0) -> float:
        """Evaluates automated value at a given timestamp using interpolation."""
        if not self.points:
            return default_value
        
        # Sort points by timestamp
        pts = sorted(self.points, key=lambda p: p.time_sec)
        if time_sec <= pts[0].time_sec:
            return pts[0].value
        if time_sec >= pts[-1].time_sec:
            return pts[-1].value
        
        # Interpolate between surrounding points
        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            if p0.time_sec <= time_sec <= p1.time_sec:
                span = p1.time_sec - p0.time_sec
                if span <= 1e-6:
                    return p1.value
                t_norm = (time_sec - p0.time_sec) / span
                
                # Apply curve shaping
                if p0.curve == FadeCurve.LINEAR:
                    return p0.value + t_norm * (p1.value - p0.value)
                elif p0.curve == FadeCurve.EQUAL_POWER:
                    return p0.value * math.cos(t_norm * math.pi / 2.0) + p1.value * math.sin(t_norm * math.pi / 2.0)
                elif p0.curve == FadeCurve.EXPONENTIAL:
                    return p0.value + (t_norm ** 2.0) * (p1.value - p0.value)
                elif p0.curve == FadeCurve.LOGARITHMIC:
                    return p0.value + math.sqrt(t_norm) * (p1.value - p0.value)
                elif p0.curve == FadeCurve.S_CURVE:
                    s_t = (1.0 - math.cos(t_norm * math.pi)) / 2.0
                    return p0.value + s_t * (p1.value - p0.value)
                return p0.value + t_norm * (p1.value - p0.value)
        return default_value


class AudioEffectConfig(BaseModel):
    effect_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    effect_type: str  # parametric_eq, compressor, limiter, reverb, delay, de_esser, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class AudioClip(BaseModel):
    clip_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    track_id: str
    asset_id: Optional[str] = None
    name: str = "Audio Clip"
    file_path: Optional[str] = None
    start_time_sec: float = 0.0
    duration_sec: float = 0.0
    source_in_sec: float = 0.0
    source_out_sec: Optional[float] = None
    gain_db: float = 0.0
    pan: float = 0.0  # -1.0 (L) to +1.0 (R)
    fade_in_sec: float = 0.0
    fade_out_sec: float = 0.0
    crossfade_sec: float = 0.0
    fade_curve: FadeCurve = FadeCurve.EQUAL_POWER
    pitch_semitones: float = 0.0
    playback_rate: float = 1.0
    time_stretch_ratio: float = 1.0
    muted: bool = False
    effects: List[AudioEffectConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def end_time_sec(self) -> float:
        return self.start_time_sec + self.duration_sec

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioClip:
        return cls(**data)


class AudioTrack(BaseModel):
    track_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    name: str
    track_type: AudioTrackType = AudioTrackType.DIALOGUE
    gain_db: float = 0.0
    pan: float = 0.0
    muted: bool = False
    soloed: bool = False
    clips: List[AudioClip] = Field(default_factory=list)
    automation_lanes: List[AutomationLane] = Field(default_factory=list)
    fx_chain: List[AudioEffectConfig] = Field(default_factory=list)
    send_targets: List[str] = Field(default_factory=list)
    bus_id: Optional[str] = None
    color: str = "#4A90E2"

    def add_clip(self, clip: AudioClip) -> AudioClip:
        clip.track_id = self.track_id
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start_time_sec)
        return clip

    def find_clip(self, clip_id: str) -> Optional[AudioClip]:
        for c in self.clips:
            if c.clip_id == clip_id:
                return c
        return None

    def split_clip(self, clip_id: str, split_time_sec: float) -> Optional[List[AudioClip]]:
        """Splits an audio clip into two non-destructive child clips at split_time_sec."""
        target = self.find_clip(clip_id)
        if not target:
            return None
        if not (target.start_time_sec < split_time_sec < target.end_time_sec):
            return None

        dur1 = split_time_sec - target.start_time_sec
        dur2 = target.duration_sec - dur1

        # Clip A: trimmed end
        clip_a = target.model_copy(deep=True)
        clip_a.duration_sec = dur1
        clip_a.fade_out_sec = 0.0

        # Clip B: trimmed start
        clip_b = target.model_copy(deep=True)
        clip_b.clip_id = str(uuid.uuid4())
        clip_b.start_time_sec = split_time_sec
        clip_b.source_in_sec = target.source_in_sec + dur1
        clip_b.duration_sec = dur2
        clip_b.fade_in_sec = 0.0

        # Replace in track
        self.clips = [c for c in self.clips if c.clip_id != clip_id]
        self.clips.extend([clip_a, clip_b])
        self.clips.sort(key=lambda c: c.start_time_sec)
        return [clip_a, clip_b]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioTrack:
        return cls(**data)


class AudioBus(BaseModel):
    bus_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Sub-Mix Bus"
    gain_db: float = 0.0
    pan: float = 0.0
    fx_chain: List[AudioEffectConfig] = Field(default_factory=list)
    muted: bool = False


class AudioMarker(BaseModel):
    marker_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_sec: float
    label: str
    color: str = "#FFCC00"


class AudioSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    name: str = "Multitrack Audio Session"
    sample_rate: int = 48000
    channel_layout: ChannelLayout = ChannelLayout.STEREO
    tempo_bpm: float = 120.0
    tracks: List[AudioTrack] = Field(default_factory=list)
    buses: List[AudioBus] = Field(default_factory=list)
    master_bus: AudioBus = Field(default_factory=lambda: AudioBus(name="Master Bus"))
    markers: List[AudioMarker] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_track(self, name: str, track_type: AudioTrackType, gain_db: float = 0.0, pan: float = 0.0) -> AudioTrack:
        trk = AudioTrack(
            session_id=self.session_id,
            name=name,
            track_type=track_type,
            gain_db=gain_db,
            pan=pan,
        )
        self.tracks.append(trk)
        return trk

    def get_track(self, track_id: str) -> Optional[AudioTrack]:
        for t in self.tracks:
            if t.track_id == track_id:
                return t
        return None

    def get_or_create_bus(self, name: str) -> AudioBus:
        for b in self.buses:
            if b.name.lower() == name.lower():
                return b
        new_bus = AudioBus(name=name)
        self.buses.append(new_bus)
        return new_bus

    def total_duration_sec(self) -> float:
        max_dur = 0.0
        for trk in self.tracks:
            for clip in trk.clips:
                if clip.end_time_sec > max_dur:
                    max_dur = clip.end_time_sec
        return max_dur

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AudioSession:
        return cls(**data)
