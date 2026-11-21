"""
Parametric Equalizer & Filtering Module
Supports Spotify Pedalboard native C++ and SciPy Biquad / Butterworth fallbacks.
"""
from __future__ import annotations

import math
from typing import Optional, Union
import numpy as np
import scipy.signal

try:
    import pedalboard
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class EqualizerEngine:
    """Parametric Equalizer executing multi-band frequency shaping."""

    @staticmethod
    def apply_highpass(audio: np.ndarray, sample_rate: int, cutoff_hz: float = 80.0, order: int = 2) -> np.ndarray:
        """Applies high-pass filter (Butterworth) to remove rumble / DC offset."""
        if cutoff_hz <= 0:
            return audio
        cutoff_hz = min(cutoff_hz, sample_rate * 0.49)
        
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([pedalboard.HighpassFilter(cutoff_frequency_hz=float(cutoff_hz))])
            # Pedalboard expects (channels, samples) or (samples,)
            return board(audio.astype(np.float32), sample_rate)
        
        # SciPy fallback
        sos = scipy.signal.butter(order, cutoff_hz, btype="highpass", fs=sample_rate, output="sos")
        if audio.ndim == 1:
            return scipy.signal.sosfilt(sos, audio).astype(np.float32)
        else:
            filtered = np.zeros_like(audio, dtype=np.float32)
            for ch in range(audio.shape[0]):
                filtered[ch] = scipy.signal.sosfilt(sos, audio[ch])
            return filtered

    @staticmethod
    def apply_lowpass(audio: np.ndarray, sample_rate: int, cutoff_hz: float = 16000.0, order: int = 2) -> np.ndarray:
        """Applies low-pass filter (Butterworth) to remove ultrasonic hiss."""
        cutoff_hz = min(max(cutoff_hz, 20.0), sample_rate * 0.49)
        
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([pedalboard.LowpassFilter(cutoff_frequency_hz=float(cutoff_hz))])
            return board(audio.astype(np.float32), sample_rate)
        
        sos = scipy.signal.butter(order, cutoff_hz, btype="lowpass", fs=sample_rate, output="sos")
        if audio.ndim == 1:
            return scipy.signal.sosfilt(sos, audio).astype(np.float32)
        else:
            filtered = np.zeros_like(audio, dtype=np.float32)
            for ch in range(audio.shape[0]):
                filtered[ch] = scipy.signal.sosfilt(sos, audio[ch])
            return filtered

    @staticmethod
    def apply_peak(audio: np.ndarray, sample_rate: int, center_hz: float, gain_db: float, q: float = 1.0) -> np.ndarray:
        """Applies parametric peaking bell filter."""
        if abs(gain_db) < 0.05:
            return audio
        center_hz = min(max(center_hz, 20.0), sample_rate * 0.49)
        q = max(q, 0.1)

        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([pedalboard.PeakFilter(cutoff_frequency_hz=float(center_hz), gain_db=float(gain_db), q=float(q))])
            return board(audio.astype(np.float32), sample_rate)
        
        # Robert Bristow-Johnson Peaking EQ Biquad calculation
        A = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * math.pi * center_hz / sample_rate
        alpha = math.sin(w0) / (2.0 * q)
        b0 = 1.0 + alpha * A
        b1 = -2.0 * math.cos(w0)
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * math.cos(w0)
        a2 = 1.0 - alpha / A

        b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)

        if audio.ndim == 1:
            return scipy.signal.lfilter(b, a, audio).astype(np.float32)
        else:
            filtered = np.zeros_like(audio, dtype=np.float32)
            for ch in range(audio.shape[0]):
                filtered[ch] = scipy.signal.lfilter(b, a, audio[ch])
            return filtered

    @staticmethod
    def apply_notch(audio: np.ndarray, sample_rate: int, notch_hz: float, q: float = 30.0) -> np.ndarray:
        """Applies deep notch filter (e.g. for 50Hz/60Hz mains hum)."""
        notch_hz = min(max(notch_hz, 10.0), sample_rate * 0.49)
        b, a = scipy.signal.iirnotch(notch_hz, q, fs=sample_rate)
        if audio.ndim == 1:
            return scipy.signal.lfilter(b, a, audio).astype(np.float32)
        else:
            filtered = np.zeros_like(audio, dtype=np.float32)
            for ch in range(audio.shape[0]):
                filtered[ch] = scipy.signal.lfilter(b, a, audio[ch])
            return filtered

    @classmethod
    def apply_parametric_channel_strip(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        hpf_hz: float = 80.0,
        lpf_hz: float = 16000.0,
        low_shelf_hz: float = 200.0,
        low_shelf_db: float = 0.0,
        mid_hz: float = 1000.0,
        mid_db: float = 0.0,
        mid_q: float = 1.0,
        high_shelf_hz: float = 8000.0,
        high_shelf_db: float = 0.0,
    ) -> np.ndarray:
        """Complete 5-band studio channel strip equalizer."""
        out = audio.copy().astype(np.float32)
        if hpf_hz > 10.0:
            out = cls.apply_highpass(out, sample_rate, cutoff_hz=hpf_hz)
        if lpf_hz < sample_rate * 0.48:
            out = cls.apply_lowpass(out, sample_rate, cutoff_hz=lpf_hz)
        if abs(low_shelf_db) >= 0.1:
            if HAS_PEDALBOARD:
                board = pedalboard.Pedalboard([pedalboard.LowShelfFilter(cutoff_frequency_hz=float(low_shelf_hz), gain_db=float(low_shelf_db))])
                out = board(out, sample_rate)
            else:
                out = cls.apply_peak(out, sample_rate, center_hz=low_shelf_hz, gain_db=low_shelf_db, q=0.7)
        if abs(mid_db) >= 0.1:
            out = cls.apply_peak(out, sample_rate, center_hz=mid_hz, gain_db=mid_db, q=mid_q)
        if abs(high_shelf_db) >= 0.1:
            if HAS_PEDALBOARD:
                board = pedalboard.Pedalboard([pedalboard.HighShelfFilter(cutoff_frequency_hz=float(high_shelf_hz), gain_db=float(high_shelf_db))])
                out = board(out, sample_rate)
            else:
                out = cls.apply_peak(out, sample_rate, center_hz=high_shelf_hz, gain_db=high_shelf_db, q=0.7)
        return out
