"""
Temporal and Multimodal Intelligence Data Models.
Establishes canonical representations for shots, scenes, transcripts,
audio events, object tracking, camera motion, OCR, and reference profiles.
Every observation preserves sub-second timestamps, confidence, and verifiable evidence.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ShotScale(str, Enum):
    EXTREME_WIDE = "EXTREME_WIDE"
    WIDE = "WIDE"
    MEDIUM_WIDE = "MEDIUM_WIDE"
    MEDIUM = "MEDIUM"
    MEDIUM_CLOSE_UP = "MEDIUM_CLOSE_UP"
    CLOSE_UP = "CLOSE_UP"
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"
    OVER_THE_SHOULDER = "OVER_THE_SHOULDER"
    POINT_OF_VIEW = "POINT_OF_VIEW"
    INSERT_SHOT = "INSERT_SHOT"
    ESTABLISHING = "ESTABLISHING"
    UNKNOWN = "UNKNOWN"

class CameraAngle(str, Enum):
    EYE_LEVEL = "EYE_LEVEL"
    LOW_ANGLE = "LOW_ANGLE"
    HIGH_ANGLE = "HIGH_ANGLE"
    DUTCH_ANGLE = "DUTCH_ANGLE"
    BIRDS_EYE = "BIRDS_EYE"
    WORMS_EYE = "WORMS_EYE"
    UNKNOWN = "UNKNOWN"

class CameraMotionType(str, Enum):
    STATIC = "STATIC"
    PAN_LEFT = "PAN_LEFT"
    PAN_RIGHT = "PAN_RIGHT"
    TILT_UP = "TILT_UP"
    TILT_DOWN = "TILT_DOWN"
    ZOOM_IN = "ZOOM_IN"
    ZOOM_OUT = "ZOOM_OUT"
    DOLLY_IN = "DOLLY_IN"
    DOLLY_OUT = "DOLLY_OUT"
    TRACKING = "TRACKING"
    HANDHELD_JITTER = "HANDHELD_JITTER"
    UNKNOWN = "UNKNOWN"

class TransitionType(str, Enum):
    HARD_CUT = "HARD_CUT"
    DISSOLVE = "DISSOLVE"
    FADE_TO_BLACK = "FADE_TO_BLACK"
    FADE_FROM_BLACK = "FADE_FROM_BLACK"
    WIPE = "WIPE"
    UNKNOWN = "UNKNOWN"

class AudioEventType(str, Enum):
    SPEECH = "SPEECH"
    MUSIC = "MUSIC"
    SOUND_EFFECT = "SOUND_EFFECT"
    AMBIENCE = "AMBIENCE"
    SILENCE = "SILENCE"
    APPLAUSE = "APPLAUSE"
    LAUGHTER = "LAUGHTER"
    FOLEY = "FOLEY"
    UNKNOWN = "UNKNOWN"

class AnalysisProfile(str, Enum):
    FAST_OVERVIEW = "FAST_OVERVIEW"
    STANDARD = "STANDARD"
    DETAILED = "DETAILED"
    REFERENCE_ANALYSIS = "REFERENCE_ANALYSIS"

@dataclass
class TimecodeRange:
    start_time: str
    end_time: str
    start_seconds: float
    end_seconds: float
    start_frame: int
    end_frame: int
    fps: float

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)

    @property
    def duration_frames(self) -> int:
        return max(0, self.end_frame - self.start_frame)

    @classmethod
    def from_seconds(cls, start_sec: float, end_sec: float, fps: float = 24.0) -> "TimecodeRange":
        start_frame = int(round(start_sec * fps))
        end_frame = int(round(end_sec * fps))
        
        def sec_to_tc(sec: float) -> str:
            hrs = int(sec // 3600)
            mins = int((sec % 3600) // 60)
            secs = int(sec % 60)
            frames = int(round((sec - int(sec)) * fps))
            return f"{hrs:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

        return cls(
            start_time=sec_to_tc(start_sec),
            end_time=sec_to_tc(end_sec),
            start_seconds=round(start_sec, 3),
            end_seconds=round(end_sec, 3),
            start_frame=start_frame,
            end_frame=end_frame,
            fps=fps
        )

@dataclass
class EvidenceRecord:
    evidence_id: UUID = field(default_factory=uuid4)
    provider: str = "local"
    model: str = "deterministic"
    source_metric: str = ""
    raw_measurement: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: str = field(default_factory=utc_now_iso)

@dataclass
class ShotRecord:
    shot_id: UUID
    asset_id: UUID
    shot_number: int
    timecode_range: TimecodeRange
    transition_in: TransitionType = TransitionType.HARD_CUT
    transition_out: TransitionType = TransitionType.HARD_CUT
    shot_scale: ShotScale = ShotScale.UNKNOWN
    camera_angle: CameraAngle = CameraAngle.UNKNOWN
    camera_motion: CameraMotionType = CameraMotionType.STATIC
    summary: str = ""
    visual_features: Dict[str, Any] = field(default_factory=dict)
    evidence: Optional[EvidenceRecord] = None
    confidence: float = 1.0

@dataclass
class SceneRecord:
    scene_id: UUID
    asset_id: UUID
    scene_number: int
    timecode_range: TimecodeRange
    shot_ids: List[UUID] = field(default_factory=list)
    narrative_summary: str = ""
    setting: str = ""
    lighting_style: str = ""
    dominant_mood: str = ""
    evidence: Optional[EvidenceRecord] = None
    confidence: float = 1.0

@dataclass
class TranscriptWord:
    word: str
    start_seconds: float
    end_seconds: float
    confidence: float = 1.0

@dataclass
class TranscriptSegment:
    segment_id: UUID
    asset_id: UUID
    speaker_id: str
    text: str
    timecode_range: TimecodeRange
    language: str = "en"
    words: List[TranscriptWord] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class AudioEventRecord:
    event_id: UUID
    asset_id: UUID
    event_type: AudioEventType
    description: str
    timecode_range: TimecodeRange
    confidence: float = 1.0
    spectral_energy: Optional[float] = None
    evidence: Optional[EvidenceRecord] = None

@dataclass
class MusicSegmentRecord:
    segment_id: UUID
    asset_id: UUID
    timecode_range: TimecodeRange
    tempo_bpm: float
    beat_timestamps: List[float] = field(default_factory=list)
    key_signature: Optional[str] = None
    rhythmic_energy: float = 0.5
    mood: str = "neutral"
    has_vocals: bool = False
    confidence: float = 1.0

@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

@dataclass
class DetectedObjectRecord:
    detection_id: UUID
    asset_id: UUID
    track_id: int
    label: str
    timestamp_seconds: float
    frame_number: int
    box: BoundingBox
    confidence: float = 1.0

@dataclass
class CameraMovementRecord:
    movement_id: UUID
    asset_id: UUID
    timecode_range: TimecodeRange
    motion_type: CameraMotionType
    magnitude: float
    direction_vector: List[float] = field(default_factory=lambda: [0.0, 0.0])
    confidence: float = 1.0
    evidence: Optional[EvidenceRecord] = None

@dataclass
class OCRObservation:
    ocr_id: UUID
    asset_id: UUID
    text: str
    timestamp_seconds: float
    frame_number: int
    box: BoundingBox
    confidence: float = 1.0
    text_category: str = "GENERAL"  # TITLE, SUBTITLE, LOWER_THIRD, SIGNAGE

@dataclass
class ReferenceProfile:
    profile_id: UUID
    asset_id: UUID
    name: str
    created_at: str
    visual_style: Dict[str, Any]       # palette, contrast, lighting, aspect
    editing_style: Dict[str, Any]      # average_shot_length, cut_frequency, pacing, transitions
    motion_graphics: Dict[str, Any]    # typography, placement, animation_style
    audio_style: Dict[str, Any]        # music_bpm, sound_design_density, dialogue_balance
    narrative_arc: Dict[str, Any]      # opening_hook, progression, climax, resolution
    key_moments: List[Dict[str, Any]]

