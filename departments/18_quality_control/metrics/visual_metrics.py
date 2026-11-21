"""
Visual Quality Assessor for Department 18.
Computes reference-based fidelity metrics (PSNR, SSIM, and simulated VMAF)
when pristine original reference frames exist.
"""
from __future__ import annotations

import math
from typing import Dict, Optional
import numpy as np


class VisualQualityAssessor:
    """Evaluates reference-based objective perceptual metrics."""

    @classmethod
    def calculate_psnr(cls, ref_frame: np.ndarray, enc_frame: np.ndarray) -> float:
        """Calculates Peak Signal-to-Noise Ratio (PSNR) between reference and encoded frames."""
        mse = np.mean((ref_frame.astype(np.float64) - enc_frame.astype(np.float64)) ** 2)
        if mse == 0:
            return 100.0  # Identical frames
        max_pixel = 255.0
        return round(float(20 * math.log10(max_pixel / math.sqrt(mse))), 2)

    @classmethod
    def calculate_ssim(cls, ref_frame: np.ndarray, enc_frame: np.ndarray) -> float:
        """Calculates simplified Structural Similarity Index (SSIM)."""
        ref = ref_frame.astype(np.float64)
        enc = enc_frame.astype(np.float64)

        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        mu1 = np.mean(ref)
        mu2 = np.mean(enc)
        sigma1_sq = np.var(ref)
        sigma2_sq = np.var(enc)
        sigma12 = np.mean((ref - mu1) * (enc - mu2))

        numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
        denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)
        return round(float(numerator / denominator), 4)

    @classmethod
    def evaluate_vmaf_score(
        cls,
        psnr_db: float,
        ssim: float,
        is_hdr: bool = False,
    ) -> float:
        """
        Estimates VMAF v1 score from underlying perceptual components
        (correlation model with Netflix VMAF dataset).
        """
        # Linear regression approximation for VMAF from SSIM and PSNR
        base_vmaf = 50.0 + (ssim * 35.0) + (min(50.0, psnr_db) * 0.3)
        if is_hdr:
            base_vmaf -= 2.0  # HDR model penalty for highlight rolloff
        return round(min(100.0, max(0.0, base_vmaf)), 2)
