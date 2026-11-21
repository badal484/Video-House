"""
Audio Effects: Algorithmic Reverb, Delay, Chorus, Stereo Panning
"""
from __future__ import annotations

import math
import numpy as np
import scipy.signal

try:
    import pedalboard
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class EffectsEngine:
    """Time-based and spatial audio effects engine."""

    @staticmethod
    def apply_reverb(
        audio: np.ndarray,
        sample_rate: int,
        room_size: float = 0.5,
        damping: float = 0.5,
        wet_level: float = 0.33,
        dry_level: float = 0.7,
        width: float = 1.0,
    ) -> np.ndarray:
        """Applies algorithmic reverberation."""
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.Reverb(
                    room_size=float(room_size),
                    damping=float(damping),
                    wet_level=float(wet_level),
                    dry_level=float(dry_level),
                    width=float(width),
                )
            ])
            return board(audio.astype(np.float32), sample_rate)

        # Freeverb / Feedback Delay Network simulation fallback
        out = audio.copy().astype(np.float32)
        delay_times = [int(sample_rate * t) for t in [0.029, 0.037, 0.041, 0.043]]
        decay = 0.6 * room_size
        rev_accum = np.zeros_like(out)
        for dt in delay_times:
            if dt < out.shape[-1]:
                b = np.zeros(dt + 1)
                b[dt] = decay
                a = np.array([1.0, -decay * (1.0 - damping)])
                if out.ndim > 1:
                    for ch in range(out.shape[0]):
                        rev_accum[ch] += scipy.signal.lfilter(b, a, out[ch])
                else:
                    rev_accum += scipy.signal.lfilter(b, a, out)
        return (dry_level * out + wet_level * (rev_accum / len(delay_times))).astype(np.float32)

    @staticmethod
    def apply_delay(
        audio: np.ndarray,
        sample_rate: int,
        delay_seconds: float = 0.25,
        feedback: float = 0.35,
        mix: float = 0.4,
    ) -> np.ndarray:
        """Applies feedback delay line."""
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.Delay(
                    delay_seconds=float(delay_seconds),
                    feedback=float(feedback),
                    mix=float(mix),
                )
            ])
            return board(audio.astype(np.float32), sample_rate)

        delay_samples = int(sample_rate * delay_seconds)
        if delay_samples <= 0 or delay_samples >= audio.shape[-1]:
            return audio

        out = audio.copy().astype(np.float32)
        b = np.zeros(delay_samples + 1)
        b[delay_samples] = 1.0
        a = np.zeros(delay_samples + 1)
        a[0] = 1.0
        a[delay_samples] = -feedback

        if out.ndim > 1:
            delayed = np.zeros_like(out)
            for ch in range(out.shape[0]):
                delayed[ch] = scipy.signal.lfilter(b, a, out[ch])
            return ((1.0 - mix) * out + mix * delayed).astype(np.float32)
        else:
            delayed = scipy.signal.lfilter(b, a, out)
            return ((1.0 - mix) * out + mix * delayed).astype(np.float32)

    @staticmethod
    def apply_pan(audio: np.ndarray, pan: float = 0.0) -> np.ndarray:
        """
        Applies constant-power stereo panning.
        pan in [-1.0 (Hard Left), +1.0 (Hard Right)]. Center is 0.0.
        """
        pan = max(-1.0, min(1.0, pan))
        # Constant-power panning law
        angle = (pan + 1.0) * (math.pi / 4.0)  # 0 to pi/2
        gain_left = math.cos(angle)
        gain_right = math.sin(angle)

        if audio.ndim == 1:
            # Mono to stereo
            stereo = np.zeros((2, len(audio)), dtype=np.float32)
            stereo[0] = audio * gain_left
            stereo[1] = audio * gain_right
            return stereo
        elif audio.shape[0] == 2:
            stereo = np.zeros_like(audio, dtype=np.float32)
            stereo[0] = audio[0] * gain_left * math.sqrt(2.0)
            stereo[1] = audio[1] * gain_right * math.sqrt(2.0)
            return stereo
        return audio
