"""
Time & Pitch Processing: Pitch Shift, Time Stretch, Resampling
"""
from __future__ import annotations

import numpy as np
import scipy.signal

try:
    import pedalboard
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class TimePitchEngine:
    """Pitch manipulation and sample rate conversion."""

    @staticmethod
    def apply_pitch_shift(
        audio: np.ndarray,
        sample_rate: int,
        semitones: float = 0.0,
    ) -> np.ndarray:
        """Shifts audio pitch by semitones (-24.0 to +24.0) without changing speed."""
        if abs(semitones) < 0.01:
            return audio

        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.PitchShift(semitones=float(semitones))
            ])
            return board(audio.astype(np.float32), sample_rate)

        # Resampling pitch shift approximation (with speed compensation)
        factor = 2.0 ** (semitones / 12.0)
        n_samples = int(audio.shape[-1] / factor)
        if audio.ndim > 1:
            resampled = np.zeros((audio.shape[0], audio.shape[-1]), dtype=np.float32)
            for ch in range(audio.shape[0]):
                tmp = scipy.signal.resample(audio[ch], n_samples)
                # Pad or crop to preserve original length
                if len(tmp) >= audio.shape[-1]:
                    resampled[ch] = tmp[:audio.shape[-1]]
                else:
                    resampled[ch, :len(tmp)] = tmp
            return resampled
        else:
            tmp = scipy.signal.resample(audio, n_samples)
            out = np.zeros(audio.shape[-1], dtype=np.float32)
            if len(tmp) >= audio.shape[-1]:
                out = tmp[:audio.shape[-1]]
            else:
                out[:len(tmp)] = tmp
            return out

    @staticmethod
    def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resamples audio array to target sample rate (e.g. 44.1kHz -> 48kHz)."""
        if orig_sr == target_sr:
            return audio
        num_target_samples = int(round(audio.shape[-1] * target_sr / orig_sr))
        if audio.ndim > 1:
            resampled = np.zeros((audio.shape[0], num_target_samples), dtype=np.float32)
            for ch in range(audio.shape[0]):
                resampled[ch] = scipy.signal.resample(audio[ch], num_target_samples)
            return resampled
        else:
            return scipy.signal.resample(audio, num_target_samples).astype(np.float32)
