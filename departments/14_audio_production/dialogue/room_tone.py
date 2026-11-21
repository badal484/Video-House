"""
Room Tone Extraction & Seamless Ambience Loop Generator
"""
from __future__ import annotations

import math
from typing import Optional, Tuple
import numpy as np


class RoomToneGenerator:
    """Extracts room tone from pause intervals and generates continuous seamless ambient beds."""

    @staticmethod
    def extract_quietest_segment(
        audio: np.ndarray,
        sample_rate: int,
        segment_len_sec: float = 0.5,
    ) -> np.ndarray:
        """Finds and extracts the lowest RMS energy segment from dialogue to serve as clean room tone."""
        seg_samples = int(sample_rate * segment_len_sec)
        total_samples = audio.shape[-1]
        if total_samples <= seg_samples:
            return audio.copy()

        # Step through in 50ms hops
        hop = int(sample_rate * 0.05)
        num_hops = (total_samples - seg_samples) // hop
        min_rms = float("inf")
        best_start = 0

        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        for h in range(num_hops):
            start = h * hop
            chunk = mono[start:start + seg_samples]
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms < min_rms:
                min_rms = rms
                best_start = start

        if audio.ndim > 1:
            return audio[:, best_start:best_start + seg_samples].copy()
        return audio[best_start:best_start + seg_samples].copy()

    @staticmethod
    def loop_room_tone(
        sample: np.ndarray,
        target_duration_sec: float,
        sample_rate: int,
        crossfade_sec: float = 0.1,
    ) -> np.ndarray:
        """
        Loops room tone sample using equal-power crossfades to produce an imperceptible continuous bed.
        """
        target_len = int(sample_rate * target_duration_sec)
        xfade_len = min(int(sample_rate * crossfade_sec), sample.shape[-1] // 3)
        if xfade_len <= 0:
            xfade_len = 100

        # Create equal-power crossfade curves
        t = np.linspace(0.0, math.pi / 2.0, xfade_len)
        fade_out = np.cos(t).astype(np.float32)
        fade_in = np.sin(t).astype(np.float32)

        sample_len = sample.shape[-1]
        channels = sample.shape[0] if sample.ndim > 1 else 1

        is_stereo = (sample.ndim > 1)
        out_len = target_len + sample_len
        if is_stereo:
            out = np.zeros((channels, out_len), dtype=np.float32)
        else:
            out = np.zeros(out_len, dtype=np.float32)

        curr_pos = 0
        while curr_pos < target_len:
            if curr_pos == 0:
                if is_stereo:
                    out[:, :sample_len] += sample
                else:
                    out[:sample_len] += sample
                curr_pos += sample_len - xfade_len
            else:
                # Crossfade previous tail with next head
                if is_stereo:
                    # Fade previous tail
                    out[:, curr_pos:curr_pos + xfade_len] *= fade_out
                    # Add new head with fade in
                    out[:, curr_pos:curr_pos + xfade_len] += sample[:, :xfade_len] * fade_in
                    # Add remaining body
                    rem = sample_len - xfade_len
                    out[:, curr_pos + xfade_len:curr_pos + sample_len] += sample[:, xfade_len:]
                else:
                    out[curr_pos:curr_pos + xfade_len] *= fade_out
                    out[curr_pos:curr_pos + xfade_len] += sample[:xfade_len] * fade_in
                    out[curr_pos + xfade_len:curr_pos + sample_len] += sample[xfade_len:]
                curr_pos += sample_len - xfade_len

        if is_stereo:
            return out[:, :target_len].copy()
        return out[:target_len].copy()
