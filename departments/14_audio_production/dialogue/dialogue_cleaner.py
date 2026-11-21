"""
Dialogue Cleaner & Restoration Engine: Hum Removal, Rumble Filtering, Spectral Noise Suppression
"""
from __future__ import annotations

import math
from typing import Optional, Tuple
import numpy as np
import scipy.signal

from ..dsp.equalizer import EqualizerEngine


class DialogueCleaner:
    """Dialogue restoration engine for cleaning noisy vocal takes."""

    @staticmethod
    def remove_mains_hum(
        audio: np.ndarray,
        sample_rate: int,
        mains_freq: float = 50.0,
        num_harmonics: int = 4,
        q: float = 35.0,
    ) -> np.ndarray:
        """
        Removes 50Hz (EU/Asia) or 60Hz (US) electrical hum and its harmonic overtones.
        """
        out = audio.copy().astype(np.float32)
        nyquist = sample_rate * 0.49
        for i in range(1, num_harmonics + 1):
            freq = mains_freq * i
            if freq < nyquist:
                out = EqualizerEngine.apply_notch(out, sample_rate, notch_hz=freq, q=q)
        return out

    @staticmethod
    def apply_rumble_filter(
        audio: np.ndarray,
        sample_rate: int,
        cutoff_hz: float = 80.0,
    ) -> np.ndarray:
        """Attenuates low-frequency microphone handling rumble and plosive wind bursts."""
        return EqualizerEngine.apply_highpass(audio, sample_rate, cutoff_hz=cutoff_hz, order=3)

    @staticmethod
    def spectral_denoise(
        audio: np.ndarray,
        sample_rate: int,
        noise_profile: Optional[np.ndarray] = None,
        oversubtraction: float = 1.6,
        spectral_floor: float = 0.03,
        n_fft: int = 2048,
        hop_length: int = 512,
    ) -> np.ndarray:
        """
        Spectral subtraction noise suppression.
        If noise_profile is None, estimates noise from lowest-energy frames (pauses).
        """
        is_stereo = (audio.ndim > 1 and audio.shape[0] == 2)
        mono = np.mean(audio, axis=0) if is_stereo else audio

        # STFT
        window = scipy.signal.windows.hann(n_fft)
        f, t, Zxx = scipy.signal.stft(mono, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
        magnitude = np.abs(Zxx)
        phase = np.angle(Zxx)

        # Estimate noise spectrum
        if noise_profile is not None and len(noise_profile) > 0:
            _, _, N_stft = scipy.signal.stft(noise_profile, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
            noise_mag_mean = np.mean(np.abs(N_stft), axis=-1, keepdims=True)
        else:
            # Automatic pause detection: take bottom 15% lowest energy frames
            frame_energy = np.sum(magnitude ** 2, axis=0)
            threshold = np.percentile(frame_energy, 15)
            pause_frames = magnitude[:, frame_energy <= threshold]
            if pause_frames.shape[-1] > 2:
                noise_mag_mean = np.mean(pause_frames, axis=-1, keepdims=True)
            else:
                noise_mag_mean = np.mean(magnitude[:, :max(3, magnitude.shape[-1] // 10)], axis=-1, keepdims=True)

        # Spectral subtraction
        power = magnitude ** 2
        noise_power = noise_mag_mean ** 2
        sub_power = power - oversubtraction * noise_power
        # Apply spectral floor to prevent musical noise chirp artifacts
        clean_power = np.maximum(sub_power, spectral_floor * power)
        clean_mag = np.sqrt(clean_power)

        # Reconstruct with original phase
        Zxx_clean = clean_mag * np.exp(1j * phase)
        _, clean_mono = scipy.signal.istft(Zxx_clean, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
        
        # Match original length
        clean_mono = clean_mono[:audio.shape[-1]].astype(np.float32)

        if is_stereo:
            # Apply spectral gain mask to original channels
            gain_mask = np.clip(clean_mag / (magnitude + 1e-8), 0.0, 1.0)
            # Reconstruct both channels
            clean_stereo = np.zeros_like(audio, dtype=np.float32)
            for ch in range(2):
                _, _, ch_Zxx = scipy.signal.stft(audio[ch], fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
                ch_clean_Zxx = ch_Zxx * gain_mask
                _, ch_clean = scipy.signal.istft(ch_clean_Zxx, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
                clean_stereo[ch] = ch_clean[:audio.shape[-1]]
            return clean_stereo
        return clean_mono

    @classmethod
    def clean_dialogue(
        cls,
        audio: np.ndarray,
        sample_rate: int,
        mains_freq: float = 50.0,
        remove_hum: bool = True,
        remove_rumble: bool = True,
        denoise: bool = True,
    ) -> np.ndarray:
        """Runs complete dialogue cleanup pipeline."""
        out = audio.copy().astype(np.float32)
        if remove_rumble:
            out = cls.apply_rumble_filter(out, sample_rate, cutoff_hz=80.0)
        if remove_hum:
            out = cls.remove_mains_hum(out, sample_rate, mains_freq=mains_freq)
        if denoise:
            out = cls.spectral_denoise(out, sample_rate)
        return out
