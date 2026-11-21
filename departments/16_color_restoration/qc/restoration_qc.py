"""
Restoration Quality Control & Objective Metrics for Department 16.
Validates duration, frame rate, audio synchronization, and calculates PSNR/SSIM against ground truth.
"""
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from ..core.models import QualityReviewState


class RestorationQualityController:
    """
    Audits restoration results for technical fidelity and synchronization.
    """

    @staticmethod
    def calculate_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculates Peak Signal-to-Noise Ratio (PSNR) in dB."""
        mse = np.mean(np.square(img1.astype(np.float32) - img2.astype(np.float32)))
        if mse == 0:
            return 100.0 # Identical
        return float(10.0 * np.log10(1.0 / mse))

    @staticmethod
    def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculates Structural Similarity Index (SSIM) approximation on luminance."""
        i1 = np.clip(img1[:, :, :3], 0.0, 1.0).astype(np.float32)
        i2 = np.clip(img2[:, :, :3], 0.0, 1.0).astype(np.float32)

        y1 = 0.2126 * i1[:, :, 0] + 0.7152 * i1[:, :, 1] + 0.0722 * i1[:, :, 2]
        y2 = 0.2126 * i2[:, :, 0] + 0.7152 * i2[:, :, 1] + 0.0722 * i2[:, :, 2]

        mu1 = cv2.GaussianBlur(y1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(y2, (11, 11), 1.5)

        mu1_sq = mu1 * mu1
        mu2_sq = mu2 * mu2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(y1 * y1, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(y2 * y2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(y1 * y2, (11, 11), 1.5) - mu1_mu2

        c1 = (0.01 * 1.0) ** 2
        c2 = (0.03 * 1.0) ** 2

        ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        return float(np.mean(ssim_map))

    @classmethod
    def audit_restoration_run(
        cls,
        orig_duration: float,
        restored_duration: float,
        orig_frame_count: int,
        restored_frame_count: int,
        audio_synced: bool = True,
        sample_orig_frame: Optional[np.ndarray] = None,
        sample_restored_frame: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Validates container timing and fidelity preservation.
        """
        issues: List[str] = []
        review_state = QualityReviewState.PASSED

        # Timing check within 50ms tolerance
        duration_diff = abs(orig_duration - restored_duration)
        if duration_diff > 0.05:
            issues.append(f"Duration mismatch: original {orig_duration:.3f}s, restored {restored_duration:.3f}s (delta: {duration_diff:.3f}s).")
            review_state = QualityReviewState.FAILED

        if orig_frame_count != restored_frame_count:
            issues.append(f"Frame count mismatch: original {orig_frame_count}, restored {restored_frame_count}.")
            review_state = QualityReviewState.WARNING

        if not audio_synced:
            issues.append("Audio stream synchronization drift detected post-restoration.")
            review_state = QualityReviewState.FAILED

        metrics = {}
        if sample_orig_frame is not None and sample_restored_frame is not None:
            # Resize if resolutions differ (e.g. upscaled)
            if sample_orig_frame.shape[:2] != sample_restored_frame.shape[:2]:
                ref = cv2.resize(sample_orig_frame, (sample_restored_frame.shape[1], sample_restored_frame.shape[0]))
            else:
                ref = sample_orig_frame

            metrics["psnr_db"] = round(cls.calculate_psnr(ref, sample_restored_frame), 2)
            metrics["ssim"] = round(cls.calculate_ssim(ref, sample_restored_frame), 4)

        return {
            "review_state": review_state,
            "duration_delta_s": round(duration_diff, 4),
            "frame_count_match": (orig_frame_count == restored_frame_count),
            "audio_synced": audio_synced,
            "metrics": metrics,
            "issues": issues
        }
