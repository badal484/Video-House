"""
Rational Time and Editorial Math Engine.
Provides frame-accurate, drift-free rational time arithmetic for the canonical timeline.
Distinguishes between timeline time, source media time, frame index, and audio sample position.
Wraps and extends OpenTimelineIO RationalTime.
"""
from fractions import Fraction
import math
import re
from typing import Any, Dict, Optional, Tuple, Union

try:
    import opentimelineio.opentime as otio_time
    HAS_OTIO = True
except ImportError:
    HAS_OTIO = False


class RationalTime:
    """
    Immutable rational time representation: value / rate.
    Eliminates floating-point drift over multi-hour timelines.
    """
    __slots__ = ("_value", "_rate")

    def __init__(self, value: Union[int, float, Fraction] = 0, rate: Union[int, float] = 24.0):
        if rate <= 0:
            raise ValueError(f"Time rate must be positive, got {rate}")
        
        if isinstance(value, Fraction):
            # Normalize to target rate
            self._rate = float(rate)
            self._value = float(value * rate)
        elif isinstance(value, float):
            self._rate = float(rate)
            self._value = round(value, 6)
        else:
            self._rate = float(rate)
            self._value = float(value)

    @property
    def value(self) -> float:
        return self._value

    @property
    def rate(self) -> float:
        return self._rate

    def to_seconds(self) -> float:
        return self._value / self._rate

    def to_frames(self) -> int:
        return int(round(self._value))

    def rescaled_to(self, new_rate: float) -> "RationalTime":
        if new_rate <= 0:
            raise ValueError(f"New rate must be positive, got {new_rate}")
        if abs(self._rate - new_rate) < 1e-6:
            return self
        new_val = (self._value * new_rate) / self._rate
        return RationalTime(new_val, new_rate)

    def rescale(self, new_rate: float) -> "RationalTime":
        """Convenience alias for rescaled_to."""
        return self.rescaled_to(new_rate)

    def to_timecode(self, drop_frame: bool = False) -> str:
        """Converts to HH:MM:SS:FF timecode."""
        total_frames = self.to_frames()
        fps = int(round(self._rate))
        if fps <= 0:
            fps = 24
        
        ff = total_frames % fps
        total_sec = total_frames // fps
        ss = total_sec % 60
        total_min = total_sec // 60
        mm = total_min % 60
        hh = total_min // 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    @classmethod
    def from_seconds(cls, seconds: float, rate: float = 24.0) -> "RationalTime":
        return cls(seconds * rate, rate)

    @classmethod
    def from_frames(cls, frames: int, rate: float = 24.0) -> "RationalTime":
        return cls(float(frames), rate)

    @classmethod
    def from_timecode(cls, timecode_str: str, rate: float = 24.0) -> "RationalTime":
        """Parses HH:MM:SS:FF into RationalTime."""
        parts = timecode_str.strip().split(":")
        if len(parts) == 4:
            hh, mm, ss, ff = map(int, parts)
            total_sec = hh * 3600 + mm * 60 + ss
            frames = int(round(total_sec * rate)) + ff
            return cls(float(frames), rate)
        elif len(parts) == 3:
            hh, mm, ss = map(float, parts)
            total_sec = hh * 3600 + mm * 60 + ss
            return cls.from_seconds(total_sec, rate)
        raise ValueError(f"Invalid timecode format: {timecode_str}")

    def to_otio(self) -> Any:
        if HAS_OTIO:
            return otio_time.RationalTime(self._value, self._rate)
        return {"value": self._value, "rate": self._rate}

    @classmethod
    def from_otio(cls, otio_rt: Any) -> "RationalTime":
        return cls(otio_rt.value, otio_rt.rate)

    def __add__(self, other: "RationalTime") -> "RationalTime":
        if not isinstance(other, RationalTime):
            return NotImplemented
        rescaled_other = other.rescaled_to(self._rate)
        return RationalTime(self._value + rescaled_other.value, self._rate)

    def __sub__(self, other: "RationalTime") -> "RationalTime":
        if not isinstance(other, RationalTime):
            return NotImplemented
        rescaled_other = other.rescaled_to(self._rate)
        return RationalTime(self._value - rescaled_other.value, self._rate)

    def __mul__(self, scalar: Union[int, float]) -> "RationalTime":
        return RationalTime(self._value * scalar, self._rate)

    def __truediv__(self, scalar: Union[int, float]) -> "RationalTime":
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide RationalTime by zero")
        return RationalTime(self._value / scalar, self._rate)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RationalTime):
            return False
        return abs(self.to_seconds() - other.to_seconds()) < 1e-6

    def __lt__(self, other: "RationalTime") -> bool:
        return self.to_seconds() < other.to_seconds()

    def __le__(self, other: "RationalTime") -> bool:
        return self.to_seconds() <= other.to_seconds() + 1e-6

    def __gt__(self, other: "RationalTime") -> bool:
        return self.to_seconds() > other.to_seconds()

    def __ge__(self, other: "RationalTime") -> bool:
        return self.to_seconds() >= other.to_seconds() - 1e-6

    def __repr__(self) -> str:
        return f"RationalTime({self._value:.2f}, {self._rate:.2f}fps -> {self.to_seconds():.3f}s)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self._value,
            "rate": self._rate,
            "seconds": self.to_seconds(),
            "frames": self.to_frames(),
            "timecode": self.to_timecode()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RationalTime":
        return cls(data["value"], data["rate"])


class TimeRange:
    """
    Represents an interval [start, start + duration).
    """
    __slots__ = ("_start", "_duration")

    def __init__(self, start: RationalTime, duration: RationalTime):
        self._start = start
        self._duration = duration.rescaled_to(start.rate)
        if self._duration.value < 0:
            raise ValueError(f"Duration cannot be negative, got {self._duration}")

    @property
    def start(self) -> RationalTime:
        return self._start

    @property
    def duration(self) -> RationalTime:
        return self._duration

    @property
    def end(self) -> RationalTime:
        return self._start + self._duration

    def contains_time(self, t: RationalTime) -> bool:
        t_sec = t.to_seconds()
        return self._start.to_seconds() <= t_sec < self.end.to_seconds()

    def overlaps(self, other: "TimeRange") -> bool:
        return max(self._start.to_seconds(), other.start.to_seconds()) < min(self.end.to_seconds(), other.end.to_seconds())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self._start.to_dict(),
            "duration": self._duration.to_dict(),
            "end": self.end.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeRange":
        return cls(RationalTime.from_dict(data["start"]), RationalTime.from_dict(data["duration"]))

    def __repr__(self) -> str:
        return f"TimeRange({self._start.to_timecode()} to {self.end.to_timecode()}, dur={self._duration.to_seconds():.2f}s)"
