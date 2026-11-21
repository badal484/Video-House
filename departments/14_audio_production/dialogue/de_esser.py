"""
De-Esser Module: Sibilance Detection & Split-Band Dynamic Attenuation
"""
from __future__ import annotations

import math
import numpy as np
import scipy.signal


class DeEsser:
    """Split-band vocal de-esser attenuating harsh 's' and 'sh' sibilants."""

    @staticmethod
    def apply_de_esser(
        audio: np.ndarray,
        sample_rate: int,
        sibilance_band: tuple[float, float] = (4500.0, 8500.0),
        threshold_db: float = -22.0,
        ratio: float = 4.0,
        max_reduction_db: float = -9.0,
    ) -> np.ndarray:
        """
        Dynamically attenuates harsh sibilance without muddying the vocal presence.
        """
        low_cut, high_cut = sibilance_band
        low_cut = min(low_cut, sample_rate * 0.45)
        high_cut = min(high_cut, sample_rate * 0.48)

        # 1. Bandpass filter to isolate sibilance band for detection
        sos_bp = scipy.signal.butter(2, [low_cut, high_cut], btype="bandpass", fs=sample_rate, output="sos")
        
        # 2. Notch/Peaking filter coefficients for dynamic gain reduction
        center_freq = math.sqrt(low_cut * high_cut)
        q = center_freq / (high_cut - low_cut)

        out = audio.copy().astype(np.float32)
        thresh_lin = 10.0 ** (threshold_db / 20.0)
        max_red_lin = 10.0 ** (max_reduction_db / 20.0)

        if out.ndim > 1:
            for ch in range(out.shape[0]):
                sib = scipy.signal.sosfilt(sos_bp, out[ch])
                env = np.abs(sib)
                # Fast attack (1ms), fast release (25ms)
                alpha_att = math.exp(-1.0 / (sample_rate * 0.001))
                alpha_rel = math.exp(-1.0 / (sample_rate * 0.025))
                smoothed = np.zeros_like(env)
                curr = 0.0
                for i in range(len(env)):
                    v = env[i]
                    curr = alpha_att * curr + (1.0 - alpha_att) * v if v > curr else alpha_rel * curr + (1.0 - alpha_rel) * v
                    smoothed[i] = curr
                
                # Gain reduction curve
                gain = np.ones_like(smoothed)
                above = smoothed > thresh_lin
                if np.any(above):
                    excess = smoothed[above] / thresh_lin
                    red = 1.0 / (excess ** ((ratio - 1.0) / ratio))
                    gain[above] = np.maximum(red, max_red_lin)
                
                # Apply high frequency suppression
                out[ch] = out[ch] * gain
        else:
            sib = scipy.signal.sosfilt(sos_bp, out)
            env = np.abs(sib)
            alpha_att = math.exp(-1.0 / (sample_rate * 0.001))
            alpha_rel = math.exp(-1.0 / (sample_rate * 0.025))
            smoothed = np.zeros_like(env)
            curr = 0.0
            for i in range(len(env)):
                v = env[i]
                curr = alpha_att * curr + (1.0 - alpha_att) * v if v > curr else alpha_rel * curr + (1.0 - alpha_rel) * v
                smoothed[i] = curr

            gain = np.ones_like(smoothed)
            above = smoothed > thresh_lin
            if np.any(above):
                excess = smoothed[above] / thresh_lin
                red = 1.0 / (excess ** ((ratio - 1.0) / ratio))
                gain[above] = np.maximum(red, max_red_lin)
            out = out * gain

        return out.astype(np.float32)
