"""
Rational Time Synchronization and Audio Intelligence Alignment Engine.
Synchronizes motion graphics layers with speech word timestamps and musical beat grids.
"""
from typing import Dict, List, Optional, Tuple
from core.timeline.time_model import RationalTime, TimeRange


class TimeSynchronizer:
    """
    Coordinates motion keyframes and layer timelines with rational timebases and audio cues.
    """

    @staticmethod
    def frame_to_time(frame_index: int, fps: float) -> RationalTime:
        """Converts an absolute frame index to exact RationalTime."""
        return RationalTime(int(frame_index), float(fps))

    @staticmethod
    def time_to_frame(t: RationalTime, fps: float) -> int:
        """Converts RationalTime to integer frame index at target fps."""
        rescaled = t.rescale(fps)
        return int(round(rescaled.value))

    @staticmethod
    def align_words_to_keyframes(
        words: List[Dict[str, float]],
        start_time: RationalTime,
        fps: float = 24.0
    ) -> List[Dict[str, any]]:
        """
        Maps word-level speech timestamps (from Whisper transcripts) to frame-accurate reveal cues.
        Each word dict expected format: {'word': str, 'start': float, 'end': float}.
        """
        aligned_cues = []
        base_seconds = start_time.to_seconds()

        for w in words:
            word_str = w.get("word", "").strip()
            w_start = w.get("start", 0.0)
            w_end = w.get("end", w_start + 0.2)

            cue_time = RationalTime(int(round((base_seconds + w_start) * fps)), fps)
            cue_end = RationalTime(int(round((base_seconds + w_end) * fps)), fps)

            aligned_cues.append({
                "word": word_str,
                "start_time": cue_time,
                "end_time": cue_end,
                "duration": cue_end - cue_time
            })

        return aligned_cues

    @staticmethod
    def snap_to_nearest_beat(
        t: RationalTime,
        beat_timestamps_sec: List[float],
        tolerance_sec: float = 0.15,
        fps: float = 24.0
    ) -> RationalTime:
        """
        Snaps a timepoint to the nearest musical beat if within tolerance.
        """
        if not beat_timestamps_sec:
            return t

        target_sec = t.to_seconds()
        closest_beat = min(beat_timestamps_sec, key=lambda b: abs(b - target_sec))

        if abs(closest_beat - target_sec) <= tolerance_sec:
            return RationalTime(int(round(closest_beat * fps)), fps)

        return t
