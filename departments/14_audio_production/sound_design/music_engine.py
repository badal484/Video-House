"""
Music Production Engine: Beat Grid Detection & Dialogue Sidechain Ducking
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
import numpy as np
import scipy.signal


class MusicEngine:
    """Music synchronization, beat detection, and automated dialogue ducking."""

    @staticmethod
    def detect_tempo_and_beat_grid(audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Estimates musical tempo (BPM) and computes beat timestamps for editorial snapping.
        """
        mono = np.mean(audio, axis=0) if audio.ndim > 1 else audio
        if len(mono) < sample_rate:
            return {"bpm": 120.0, "beat_times_sec": []}

        # 1. Onset envelope via half-wave rectified spectral flux
        hop_len = int(sample_rate * 0.01)  # 10ms hops
        n_fft = 1024
        window = scipy.signal.windows.hann(n_fft)
        _, _, Zxx = scipy.signal.stft(mono, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_len)
        mag = np.abs(Zxx)
        diff = np.diff(mag, axis=1)
        onset_env = np.sum(np.maximum(0.0, diff), axis=0)

        # 2. Autocorrelation of onset envelope for periodicity (tempo)
        ac = np.correlate(onset_env, onset_env, mode="full")[len(onset_env) - 1:]
        # Search range: 60 BPM to 180 BPM
        min_lag = int(60.0 / (180.0 * (hop_len / sample_rate)))
        max_lag = int(60.0 / (60.0 * (hop_len / sample_rate)))
        min_lag = max(1, min_lag)
        max_lag = min(len(ac) - 1, max_lag)

        if max_lag > min_lag:
            peak_lag = min_lag + np.argmax(ac[min_lag:max_lag])
            seconds_per_beat = peak_lag * (hop_len / sample_rate)
            bpm = 60.0 / max(seconds_per_beat, 0.2)
        else:
            bpm = 120.0
            seconds_per_beat = 0.5

        # 3. Generate beat grid timestamps across audio duration
        duration_sec = len(mono) / sample_rate
        beat_times = []
        curr = 0.0
        while curr < duration_sec:
            beat_times.append(round(curr, 4))
            curr += seconds_per_beat

        return {
            "bpm": round(bpm, 1),
            "seconds_per_beat": round(seconds_per_beat, 4),
            "beat_times_sec": beat_times,
        }

    @staticmethod
    def compute_dialogue_ducking_envelope(
        dialogue_audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -24.0,
        duck_depth_db: float = -14.0,
        attack_ms: float = 120.0,
        release_ms: float = 750.0,
    ) -> np.ndarray:
        """
        Computes a smooth gain attenuation envelope (in linear multiplier [0.0, 1.0])
        that ducks background music when dialogue energy exceeds threshold_db.
        """
        mono_diag = np.mean(dialogue_audio, axis=0) if dialogue_audio.ndim > 1 else dialogue_audio
        abs_diag = np.abs(mono_diag)
        thresh_lin = 10.0 ** (threshold_db / 20.0)
        duck_mult = 10.0 ** (duck_depth_db / 20.0)

        # Fast attack, smooth cinematic release
        alpha_att = math.exp(-1.0 / (sample_rate * (attack_ms / 1000.0)))
        alpha_rel = math.exp(-1.0 / (sample_rate * (release_ms / 1000.0)))

        envelope = np.ones(len(abs_diag), dtype=np.float32)
        current_duck = 1.0
        # Instant state: whether voice is currently detected
        for i in range(len(abs_diag)):
            target = duck_mult if abs_diag[i] >= thresh_lin else 1.0
            if target < current_duck:
                current_duck = alpha_att * current_duck + (1.0 - alpha_att) * target
            else:
                current_duck = alpha_rel * current_duck + (1.0 - alpha_rel) * target
            envelope[i] = current_duck

        return envelope

    @classmethod
    def apply_sidechain_ducking(
        cls,
        music_audio: np.ndarray,
        dialogue_audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -24.0,
        duck_depth_db: float = -14.0,
    ) -> np.ndarray:
        """Applies dynamic sidechain ducking to music based on dialogue speech activity."""
        duck_env = cls.compute_dialogue_ducking_envelope(
            dialogue_audio=dialogue_audio,
            sample_rate=sample_rate,
            threshold_db=threshold_db,
            duck_depth_db=duck_depth_db,
        )
        
        # Match lengths
        min_len = min(music_audio.shape[-1], len(duck_env))
        out = music_audio.copy()
        if out.ndim > 1:
            out[:, :min_len] = out[:, :min_len] * duck_env[:min_len]
        else:
            out[:min_len] = out[:min_len] * duck_env[:min_len]
        return out.astype(np.float32)
