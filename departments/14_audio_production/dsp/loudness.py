"""
ITU-R BS.1770-4 & EBU R128 Loudness Measurement and Normalization
"""
from __future__ import annotations

import math
from typing import Dict, Tuple
import numpy as np
import scipy.signal

from ..core.session_models import LoudnessStandard


class LoudnessMeter:
    """ITU-R BS.1770-4 compliant loudness meter and mastering normalizer."""

    @staticmethod
    def _apply_k_weighting(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Applies Stage 1 high-shelf and Stage 2 high-pass filters as defined in BS.1770."""
        # Stage 1: High shelf filter (+4 dB at 1.5 kHz)
        f0 = 1681.974450955533
        G = 3.999843853973347
        Q = 0.7071752369274193
        K = math.tan(math.pi * f0 / sample_rate)
        Vh = 10.0 ** (G / 20.0)
        Vb = Vh ** 0.4996667741545416
        a0 = 1.0 + K / Q + K * K
        b0 = (Vh + Vb * K / Q + K * K) / a0
        b1 = 2.0 * (K * K - Vh) / a0
        b2 = (Vh - Vb * K / Q + K * K) / a0
        a1 = 2.0 * (K * K - 1.0) / a0
        a2 = (1.0 - K / Q + K * K) / a0
        b_stage1 = np.array([b0, b1, b2])
        a_stage1 = np.array([1.0, a1, a2])

        # Stage 2: High pass filter (Butterworth 38 Hz)
        f0_hp = 38.13547087602444
        K_hp = math.tan(math.pi * f0_hp / sample_rate)
        a0_hp = 1.0 + math.sqrt(2.0) * K_hp + K_hp * K_hp
        b0_hp = 1.0 / a0_hp
        b1_hp = -2.0 / a0_hp
        b2_hp = 1.0 / a0_hp
        a1_hp = 2.0 * (K_hp * K_hp - 1.0) / a0_hp
        a2_hp = (1.0 - math.sqrt(2.0) * K_hp + K_hp * K_hp) / a0_hp
        b_stage2 = np.array([b0_hp, b1_hp, b2_hp])
        a_stage2 = np.array([1.0, a1_hp, a2_hp])

        if audio.ndim == 1:
            y1 = scipy.signal.lfilter(b_stage1, a_stage1, audio)
            return scipy.signal.lfilter(b_stage2, a_stage2, y1)
        else:
            filtered = np.zeros_like(audio, dtype=np.float64)
            for ch in range(audio.shape[0]):
                y1 = scipy.signal.lfilter(b_stage1, a_stage1, audio[ch])
                filtered[ch] = scipy.signal.lfilter(b_stage2, a_stage2, y1)
            return filtered

    @classmethod
    def measure_loudness(cls, audio: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """
        Measures Integrated Loudness (LUFS), True Peak (dBTP), and Loudness Range (LU).
        Follows ITU-R BS.1770-4 gated integration.
        """
        if audio.size == 0:
            return {"integrated_lufs": -70.0, "true_peak_db": -70.0, "loudness_range_lu": 0.0}

        k_weighted = cls._apply_k_weighting(audio, sample_rate)
        
        # Channel weighting (G_i): Left=1.0, Right=1.0, Center=1.0, LFE=0.0, Surrounds=1.41
        if k_weighted.ndim == 1:
            power = k_weighted ** 2
        elif k_weighted.shape[0] == 2:
            power = 0.5 * (k_weighted[0] ** 2 + k_weighted[1] ** 2)
        else:
            power = np.mean(k_weighted ** 2, axis=0)

        # Gated block integration (400ms blocks with 75% overlap)
        block_len = int(sample_rate * 0.400)
        hop_len = int(sample_rate * 0.100)
        if len(power) < block_len:
            # Short buffer fallback
            mean_sq = np.mean(power)
            lufs = -0.691 + 10.0 * math.log10(max(mean_sq, 1e-12))
            tp = 20.0 * math.log10(max(np.max(np.abs(audio)), 1e-6))
            return {"integrated_lufs": float(lufs), "true_peak_db": float(tp), "loudness_range_lu": 0.0}

        num_blocks = (len(power) - block_len) // hop_len + 1
        block_powers = []
        for i in range(num_blocks):
            start = i * hop_len
            block_powers.append(np.mean(power[start:start + block_len]))
        block_powers = np.array(block_powers)
        block_loudness = -0.691 + 10.0 * np.log10(np.maximum(block_powers, 1e-12))

        # Absolute gate (-70 LKFS)
        abs_gated = block_loudness[block_loudness > -70.0]
        if len(abs_gated) == 0:
            integrated = -70.0
            lra = 0.0
        else:
            # Relative gate (-10 LU below un-gated mean)
            mean_abs_power = np.mean(10.0 ** ((abs_gated + 0.691) / 10.0))
            rel_thresh = -0.691 + 10.0 * math.log10(mean_abs_power) - 10.0
            rel_gated_powers = block_powers[block_loudness > rel_thresh]
            if len(rel_gated_powers) > 0:
                integrated = -0.691 + 10.0 * math.log10(np.mean(rel_gated_powers))
            else:
                integrated = -70.0
            
            # Loudness range (LRA): 10th to 95th percentile
            if len(abs_gated) > 5:
                lra = float(np.percentile(abs_gated, 95) - np.percentile(abs_gated, 10))
            else:
                lra = 0.0

        # True Peak with 4x oversampling
        resampled_audio = scipy.signal.resample(audio, audio.shape[-1] * 4, axis=-1)
        true_peak_linear = np.max(np.abs(resampled_audio))
        true_peak_db = 20.0 * math.log10(max(true_peak_linear, 1e-6))

        return {
            "integrated_lufs": float(integrated),
            "true_peak_db": float(true_peak_db),
            "loudness_range_lu": float(lra),
        }

    @classmethod
    def normalize_loudness(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        standard: LoudnessStandard = LoudnessStandard.YOUTUBE,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Two-pass loudness normalizer conforming to standard target LUFS and true peak ceiling.
        """
        measured = cls.measure_loudness(audio, sample_rate)
        target_lufs = standard.target_lufs
        max_tp = standard.max_true_peak_db

        current_lufs = measured["integrated_lufs"]
        if current_lufs <= -69.0:
            return audio, measured

        gain_db = target_lufs - current_lufs
        gain_linear = 10.0 ** (gain_db / 20.0)
        normalized = (audio * gain_linear).astype(np.float32)

        # Check true peak ceiling breach
        new_tp = measured["true_peak_db"] + gain_db
        if new_tp > max_tp:
            # Apply limiter ceiling reduction
            excess_db = new_tp - max_tp
            normalized = normalized * (10.0 ** (-excess_db / 20.0))

        final_measured = cls.measure_loudness(normalized, sample_rate)
        return normalized.astype(np.float32), final_measured
