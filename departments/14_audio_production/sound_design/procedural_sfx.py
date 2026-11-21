"""
Procedural Sound Synthesis: Cinematic Impacts, Whooshes, Risers, Ambient Drones
"""
from __future__ import annotations

import math
import numpy as np
import scipy.signal

from ..dsp.effects import EffectsEngine


class ProceduralSFXEngine:
    """Procedural synthesis of cinematic sound effects without external audio dependencies."""

    @staticmethod
    def generate_cinematic_impact(
        duration_sec: float = 2.5,
        sample_rate: int = 48000,
        sub_freq_start: float = 120.0,
        sub_freq_end: float = 28.0,
    ) -> np.ndarray:
        """
        Synthesizes a deep sub-bass cinematic impact with shaped noise transient and reverb.
        Returns stereo float32 array (2, N).
        """
        num_samples = int(sample_rate * duration_sec)
        t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

        # 1. Pitch-dropping sub-oscillator
        freq_decay = np.exp(-3.5 * t)
        inst_freq = sub_freq_end + (sub_freq_start - sub_freq_end) * freq_decay
        phase = 2.0 * math.pi * np.cumsum(inst_freq) / sample_rate
        sub_boom = np.sin(phase) * np.exp(-1.5 * t)

        # 2. Transient noise crack (50ms burst)
        noise = np.random.randn(num_samples)
        transient_env = np.exp(-40.0 * t)
        crack = noise * transient_env * 0.4

        # 3. Sum and stereo imaging
        composite = (sub_boom * 0.75 + crack).astype(np.float32)
        stereo = np.zeros((2, num_samples), dtype=np.float32)
        stereo[0] = composite
        stereo[1] = composite

        # 4. Add spatial decay
        return EffectsEngine.apply_reverb(stereo, sample_rate, room_size=0.7, wet_level=0.35, dry_level=0.85)

    @staticmethod
    def generate_whoosh_transition(
        duration_sec: float = 1.5,
        sample_rate: int = 48000,
        start_pan: float = -0.85,
        end_pan: float = 0.85,
    ) -> np.ndarray:
        """
        Synthesizes a swept-frequency whoosh transition moving across the stereo field.
        Returns stereo float32 array (2, N).
        """
        num_samples = int(sample_rate * duration_sec)
        t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

        # White noise base
        noise = np.random.randn(num_samples).astype(np.float32)
        # Symmetrical volume envelope (bell curve)
        env = np.sin(math.pi * (t / duration_sec)) ** 2.0

        # Dynamic swept bandpass filter using time-varying convolution / frequency shaping
        # Center frequency sweeps up to 3000 Hz at apex and drops to 300 Hz
        center_freq = 300.0 + 2800.0 * np.sin(math.pi * (t / duration_sec))
        # Filter noise in blocks
        block_size = 512
        num_blocks = num_samples // block_size
        filtered_mono = np.zeros(num_samples, dtype=np.float32)

        for b in range(num_blocks):
            idx = b * block_size
            cf = center_freq[idx]
            bw = max(cf * 0.6, 100.0)
            low = max(20.0, cf - bw / 2.0)
            high = min(sample_rate * 0.45, cf + bw / 2.0)
            sos = scipy.signal.butter(2, [low, high], btype="bandpass", fs=sample_rate, output="sos")
            chunk = noise[idx:idx + block_size]
            filtered_mono[idx:idx + block_size] = scipy.signal.sosfilt(sos, chunk)

        shaped = filtered_mono * env * 0.8

        # Pan automation across time
        pan_curve = np.linspace(start_pan, end_pan, num_samples)
        stereo = np.zeros((2, num_samples), dtype=np.float32)
        for i in range(num_samples):
            angle = (pan_curve[i] + 1.0) * (math.pi / 4.0)
            stereo[0, i] = shaped[i] * math.cos(angle)
            stereo[1, i] = shaped[i] * math.sin(angle)

        return EffectsEngine.apply_reverb(stereo, sample_rate, room_size=0.5, wet_level=0.25, dry_level=0.9)

    @staticmethod
    def generate_tension_riser(
        duration_sec: float = 4.0,
        sample_rate: int = 48000,
        start_freq: float = 90.0,
        end_freq: float = 1600.0,
    ) -> np.ndarray:
        """
        Synthesizes an exponential pitch tension riser build-up.
        Returns stereo float32 array (2, N).
        """
        num_samples = int(sample_rate * duration_sec)
        t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

        # Exponential frequency curve
        k = math.log(end_freq / start_freq) / duration_sec
        inst_freq = start_freq * np.exp(k * t)
        phase = 2.0 * math.pi * np.cumsum(inst_freq) / sample_rate

        # Rich multi-harmonic tone (Sawtooth approximation)
        tone = np.sin(phase) + 0.5 * np.sin(2.0 * phase) + 0.25 * np.sin(3.0 * phase)
        # Volume swells from -18 dB to 0 dB
        amp_env = np.linspace(0.12, 1.0, num_samples) ** 1.8
        riser = (tone * amp_env * 0.35).astype(np.float32)

        # Stereo chorus widener
        stereo = np.zeros((2, num_samples), dtype=np.float32)
        stereo[0] = riser
        # Slight time offset on Right channel for stereo width
        offset = int(sample_rate * 0.015)
        stereo[1, offset:] = riser[:-offset]
        stereo[1, :offset] = riser[:offset]

        return EffectsEngine.apply_reverb(stereo, sample_rate, room_size=0.6, wet_level=0.3, dry_level=0.8)

    @staticmethod
    def generate_ambient_drone(
        duration_sec: float = 6.0,
        sample_rate: int = 48000,
        root_hz: float = 55.0,
    ) -> np.ndarray:
        """
        Synthesizes a meditative, cinematic low-frequency ambient drone bed.
        Returns stereo float32 array (2, N).
        """
        num_samples = int(sample_rate * duration_sec)
        t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

        # Sub fundamental + 5th (root * 1.5) + Octave
        h1 = np.sin(2.0 * math.pi * root_hz * t)
        h2 = 0.5 * np.sin(2.0 * math.pi * (root_hz * 1.5) * t)
        h3 = 0.25 * np.sin(2.0 * math.pi * (root_hz * 2.0) * t)

        # LFO slow pulse
        lfo_left = 0.8 + 0.2 * np.sin(2.0 * math.pi * 0.15 * t)
        lfo_right = 0.8 + 0.2 * np.cos(2.0 * math.pi * 0.18 * t)

        drone_mono = (h1 + h2 + h3) * 0.3
        stereo = np.zeros((2, num_samples), dtype=np.float32)
        stereo[0] = (drone_mono * lfo_left).astype(np.float32)
        stereo[1] = (drone_mono * lfo_right).astype(np.float32)

        return EffectsEngine.apply_reverb(stereo, sample_rate, room_size=0.8, wet_level=0.45, dry_level=0.7)
