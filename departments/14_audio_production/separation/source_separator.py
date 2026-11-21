"""
Audio Source Separation Engine: 4-Stem Decomposition (Vocals, Drums, Bass, Other)
"""
from __future__ import annotations

import math
from typing import Dict
import numpy as np
import scipy.signal
import scipy.ndimage


class SourceSeparator:
    """Decomposes composite audio into isolated stems (Vocals, Drums, Bass, Other)."""

    @classmethod
    def separate_stems_local_hpss(cls, audio: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """
        Fast, deterministic local source separation using Harmonic-Percussive Spectrogram Decomposition.
        Extracts:
          - 'vocals': Harmonic speech/singing band (200Hz - 6000Hz harmonic)
          - 'drums': Broadband vertical transient bursts
          - 'bass': Low frequency harmonic energy (< 150Hz)
          - 'other': Ambient residual / pads
        """
        is_stereo = (audio.ndim > 1 and audio.shape[0] == 2)
        mono = np.mean(audio, axis=0) if is_stereo else audio

        n_fft = 2048
        hop_length = 512
        window = scipy.signal.windows.hann(n_fft)
        f, t, Zxx = scipy.signal.stft(mono, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
        mag = np.abs(Zxx)
        phase = np.angle(Zxx)

        # 1. Median filtering across time (Harmonic) and frequency (Percussive)
        # Time kernel = 31 frames (~300ms), Freq kernel = 31 bins (~700Hz)
        k_time = 31
        k_freq = 31
        
        # Fast 2D median filtering via scipy.ndimage
        harm_mag = scipy.ndimage.median_filter(mag, size=(1, k_time))
        perc_mag = scipy.ndimage.median_filter(mag, size=(k_freq, 1))

        # Soft Wiener-like masks
        eps = 1e-10
        total_p = (harm_mag ** 2) + (perc_mag ** 2) + eps
        mask_harm = (harm_mag ** 2) / total_p
        mask_perc = (perc_mag ** 2) / total_p

        # 2. Bass Separation: Low-frequency harmonic portion (< 150 Hz)
        bass_bin = int(150.0 / (sample_rate / n_fft))
        mask_bass = np.zeros_like(mask_harm)
        mask_bass[:bass_bin, :] = mask_harm[:bass_bin, :]
        mask_vocal = mask_harm.copy()
        mask_vocal[:bass_bin, :] = 0.0

        # High cut on vocals (> 7000 Hz into 'other')
        high_bin = int(7000.0 / (sample_rate / n_fft))
        mask_other = np.zeros_like(mask_harm)
        if high_bin < mask_harm.shape[0]:
            mask_other[high_bin:, :] = mask_harm[high_bin:, :]
            mask_vocal[high_bin:, :] = 0.0

        # 3. Invert STFT for each stem
        stems = {}
        masks = {
            "vocals": mask_vocal,
            "drums": mask_perc,
            "bass": mask_bass,
            "other": mask_other,
        }

        total_samples = audio.shape[-1]
        for name, m in masks.items():
            Z_stem = (mag * m) * np.exp(1j * phase)
            _, stem_mono = scipy.signal.istft(Z_stem, fs=sample_rate, window=window, nperseg=n_fft, noverlap=n_fft - hop_length)
            stem_mono = stem_mono[:total_samples].astype(np.float32)

            if is_stereo:
                # Reconstruct stereo channel
                stereo_stem = np.zeros((2, total_samples), dtype=np.float32)
                stereo_stem[0] = stem_mono
                stereo_stem[1] = stem_mono
                stems[name] = stereo_stem
            else:
                stems[name] = stem_mono

        return stems

    @classmethod
    def separate(cls, audio: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """Entry point for stem separation, falling back smoothly to local HPSS."""
        return cls.separate_stems_local_hpss(audio, sample_rate)
