"""
Dynamics Processing Module: Compressor, Limiter, Expander, Noise Gate
"""
from __future__ import annotations

import math
import numpy as np

try:
    import pedalboard
    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class DynamicsEngine:
    """Dynamic range control processor."""

    @staticmethod
    def apply_compressor(
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -20.0,
        ratio: float = 4.0,
        attack_ms: float = 10.0,
        release_ms: float = 100.0,
        makeup_gain_db: float = 0.0,
    ) -> np.ndarray:
        """Applies dynamic range compression."""
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.Compressor(
                    threshold_db=float(threshold_db),
                    ratio=float(ratio),
                    attack_ms=float(attack_ms),
                    release_ms=float(release_ms),
                )
            ])
            processed = board(audio.astype(np.float32), sample_rate)
            if abs(makeup_gain_db) > 0.01:
                processed = processed * (10.0 ** (makeup_gain_db / 20.0))
            return processed

        # Pure NumPy dynamic compressor fallback
        out = audio.copy().astype(np.float32)
        gain_mult = 10.0 ** (makeup_gain_db / 20.0)
        
        # Envelope detection
        abs_audio = np.abs(out)
        alpha_att = math.exp(-1.0 / (sample_rate * (attack_ms / 1000.0)))
        alpha_rel = math.exp(-1.0 / (sample_rate * (release_ms / 1000.0)))
        
        envelope = np.zeros_like(abs_audio)
        env = 0.0
        # For multi-channel, use max across channels
        if out.ndim > 1:
            mono_env = np.max(abs_audio, axis=0)
            smoothed_env = np.zeros_like(mono_env)
            for i in range(len(mono_env)):
                val = mono_env[i]
                if val > env:
                    env = alpha_att * env + (1.0 - alpha_att) * val
                else:
                    env = alpha_rel * env + (1.0 - alpha_rel) * val
                smoothed_env[i] = env
            
            # Gain curve calculation
            env_db = 20.0 * np.log10(np.maximum(smoothed_env, 1e-6))
            gain_red_db = np.zeros_like(env_db)
            above = env_db > threshold_db
            gain_red_db[above] = (threshold_db + (env_db[above] - threshold_db) / ratio) - env_db[above]
            linear_gain = 10.0 ** (gain_red_db / 20.0) * gain_mult
            return (out * linear_gain).astype(np.float32)
        else:
            for i in range(len(abs_audio)):
                val = abs_audio[i]
                if val > env:
                    env = alpha_att * env + (1.0 - alpha_att) * val
                else:
                    env = alpha_rel * env + (1.0 - alpha_rel) * val
                envelope[i] = env
            env_db = 20.0 * np.log10(np.maximum(envelope, 1e-6))
            gain_red_db = np.zeros_like(env_db)
            above = env_db > threshold_db
            gain_red_db[above] = (threshold_db + (env_db[above] - threshold_db) / ratio) - env_db[above]
            linear_gain = 10.0 ** (gain_red_db / 20.0) * gain_mult
            return (out * linear_gain).astype(np.float32)

    @staticmethod
    def apply_limiter(
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -1.0,
        release_ms: float = 50.0,
    ) -> np.ndarray:
        """Brickwall peak limiter ensuring ceiling is never breached."""
        ceiling_linear = 10.0 ** (threshold_db / 20.0)
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.Limiter(
                    threshold_db=float(threshold_db),
                    release_ms=float(release_ms),
                )
            ])
            proc = board(audio.astype(np.float32), sample_rate)
            # Enforce ceiling since Pedalboard Limiter clips at 0 dBFS (1.0)
            peak = np.max(np.abs(proc))
            if peak > ceiling_linear:
                proc = proc * (ceiling_linear / (peak + 1e-7))
            return proc.astype(np.float32)

        # NumPy peak ceiling limiter
        peak = np.max(np.abs(audio))
        if peak > ceiling_linear:
            scale = ceiling_linear / (peak + 1e-7)
            return (audio * scale).astype(np.float32)
        return audio.astype(np.float32)

    @staticmethod
    def apply_noise_gate(
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -45.0,
        attack_ms: float = 5.0,
        release_ms: float = 100.0,
    ) -> np.ndarray:
        """Noise gate attenuating signals below threshold."""
        if HAS_PEDALBOARD:
            board = pedalboard.Pedalboard([
                pedalboard.NoiseGate(
                    threshold_db=float(threshold_db),
                    attack_ms=float(attack_ms),
                    release_ms=float(release_ms),
                )
            ])
            return board(audio.astype(np.float32), sample_rate)

        thresh_lin = 10.0 ** (threshold_db / 20.0)
        out = audio.copy().astype(np.float32)
        if out.ndim > 1:
            mag = np.max(np.abs(out), axis=0)
            gate = (mag >= thresh_lin).astype(np.float32)
            # Smooth gate transition
            gate = np.convolve(gate, np.ones(int(sample_rate * 0.01)) / int(sample_rate * 0.01), mode='same')
            return (out * gate).astype(np.float32)
        else:
            mag = np.abs(out)
            gate = (mag >= thresh_lin).astype(np.float32)
            gate = np.convolve(gate, np.ones(int(sample_rate * 0.01)) / int(sample_rate * 0.01), mode='same')
            return (out * gate).astype(np.float32)
