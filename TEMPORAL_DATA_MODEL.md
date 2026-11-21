# Temporal Data Model & Timecode Representation

**Document Version:** 1.0.0  
**Status:** Approved & Implemented  
**Core Module:** `core/assets/intelligence_models.py`  

---

## 1. Prime Directive: Zero Floating-Point Drift

In digital video post-production, floating-point timestamp arithmetic ($t_1 + \Delta t$) accumulates rounding errors across multi-hour timelines, leading to audio desynchronization and off-by-one frame cuts (e.g. slicing through an audio transient or capturing a flash frame).

To ensure complete editorial integrity:
1. Every temporal duration is stored in a dual representation: rational floating-point seconds (`start_seconds`, `end_seconds`) AND exact integer frame numbers (`start_frame`, `end_frame`).
2. Downstream timeline representations map directly to **OpenTimelineIO (OTIO)** rational time structures:
   $$\text{RationalTime}(\text{value}, \text{rate})$$
3. All timecode conversions enforce standard SMPTE formatting: `HH:MM:SS:FF`.

---

## 2. Canonical Data Models

Implemented in `core/assets/intelligence_models.py`:

### `TimecodeRange`
```python
@dataclass
class TimecodeRange:
    start_time: str           # SMPTE string e.g. "00:00:01:12"
    end_time: str             # SMPTE string e.g. "00:00:04:06"
    start_seconds: float      # Rational seconds e.g. 1.500
    end_seconds: float        # Rational seconds e.g. 4.250
    start_frame: int          # Exact integer frame e.g. 36
    end_frame: int            # Exact integer frame e.g. 102
    fps: float                # Base framerate e.g. 24.0

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
        ...
```

### `EvidenceRecord`
Encapsulates reproducible provenance for any detection or claim:
```python
@dataclass
class EvidenceRecord:
    evidence_id: UUID = field(default_factory=uuid4)
    provider: str = "local"
    model: str = "deterministic"
    source_metric: str = ""
    raw_measurement: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: str = field(default_factory=utc_now_iso)
```

---

## 3. Enumerated Categorical Enums

To prevent string misspelling and enable type checking, the temporal model defines standard enums:

1. **`ShotScale`**:
   `EXTREME_WIDE`, `WIDE`, `MEDIUM_WIDE`, `MEDIUM`, `MEDIUM_CLOSE_UP`, `CLOSE_UP`, `EXTREME_CLOSE_UP`, `OVER_THE_SHOULDER`, `POINT_OF_VIEW`, `INSERT_SHOT`, `ESTABLISHING`, `UNKNOWN`.

2. **`CameraAngle`**:
   `EYE_LEVEL`, `LOW_ANGLE`, `HIGH_ANGLE`, `DUTCH_TILT`, `OVERHEAD_BIRD_EYE`, `GROUND_LEVEL`, `UNKNOWN`.

3. **`CameraMotionType`**:
   `STATIC`, `PAN_LEFT`, `PAN_RIGHT`, `TILT_UP`, `TILT_DOWN`, `ZOOM_IN`, `ZOOM_OUT`, `ROLL`, `TRACKING`, `HANDHELD_JITTER`, `UNKNOWN`.

4. **`TransitionType`**:
   `HARD_CUT`, `CROSS_DISSOLVE`, `DISSOLVE`, `FADE_IN`, `FADE_OUT`, `WIPE`, `WHIP_PAN`, `MATCH_CUT`, `J_CUT`, `L_CUT`.

5. **`AudioEventType`**:
   `SPEECH`, `MUSIC`, `FOLEY`, `SOUND_EFFECT`, `AMBIENCE`, `SILENCE`, `LAUGHTER`, `APPLAUSE`, `UNKNOWN`.
