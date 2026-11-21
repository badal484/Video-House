"""
Media Quality Control & Generation Verification
Department 15: 15_ai_generation
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple
import numpy as np

from ..core.generation_models import ValidationStatus


class MediaValidator:
    """Validates raw generated media prior to timeline ingestion."""

    @staticmethod
    def validate_video_file(file_path: str, expected_duration_sec: Optional[float] = None) -> Tuple[ValidationStatus, Dict[str, Any]]:
        """
        Inspects video container integrity, black frames, and freeze frames.
        """
        diag: Dict[str, Any] = {"file_path": file_path}

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            diag["error"] = "File does not exist or has 0 bytes."
            return ValidationStatus.FAILED, diag

        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                diag["error"] = "OpenCV could not open video stream."
                return ValidationStatus.FAILED, diag

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            diag["resolution"] = [width, height]
            diag["fps"] = fps
            diag["frame_count"] = total_frames
            diag["duration_sec"] = total_frames / fps if fps > 0 else 0.0

            if total_frames <= 0 or width <= 0 or height <= 0:
                cap.release()
                diag["error"] = "Invalid frame count or resolution."
                return ValidationStatus.FAILED, diag

            # Inspect up to 10 sample frames for black or freeze frames
            step = max(1, total_frames // 10)
            sample_frames = []
            for idx in range(0, total_frames, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    sample_frames.append(frame)

            cap.release()

            if not sample_frames:
                diag["error"] = "Could not decode any sample frames."
                return ValidationStatus.FAILED, diag

            # Black frame check
            mean_luma = [float(np.mean(f)) for f in sample_frames]
            diag["mean_luma"] = mean_luma
            if all(m < 2.0 for m in mean_luma):  # Almost pure black
                diag["warning"] = "Entire video sequence appears to be black frames."
                return ValidationStatus.WARNING, diag

            # Freeze frame check
            if len(sample_frames) >= 2:
                diffs = [float(np.mean(np.abs(sample_frames[i].astype(float) - sample_frames[i - 1].astype(float)))) for i in range(1, len(sample_frames))]
                diag["mean_frame_diff"] = diffs
                if all(d < 0.1 for d in diffs):
                    diag["warning"] = "Video appears frozen across all sample frames."
                    return ValidationStatus.WARNING, diag

            return ValidationStatus.PASSED, diag

        except Exception as e:
            diag["exception"] = str(e)
            return ValidationStatus.WARNING, diag

    @staticmethod
    def validate_image_file(file_path: str, min_res: Tuple[int, int] = (64, 64)) -> Tuple[ValidationStatus, Dict[str, Any]]:
        """
        Verifies image dimensions, decodability, and non-empty content.
        """
        diag: Dict[str, Any] = {"file_path": file_path}

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            diag["error"] = "Image file does not exist or has 0 bytes."
            return ValidationStatus.FAILED, diag

        try:
            import cv2
            img = cv2.imread(file_path)
            if img is None:
                diag["error"] = "OpenCV failed to decode image."
                return ValidationStatus.FAILED, diag

            h, w = img.shape[:2]
            diag["resolution"] = [w, h]

            if w < min_res[0] or h < min_res[1]:
                diag["error"] = f"Image resolution {w}x{h} below minimum {min_res[0]}x{min_res[1]}."
                return ValidationStatus.FAILED, diag

            # Check for pure solid color frame
            std_dev = float(np.std(img))
            diag["std_dev"] = std_dev
            if std_dev < 1.0:
                diag["warning"] = "Image has near-zero variance (blank solid color)."
                return ValidationStatus.WARNING, diag

            return ValidationStatus.PASSED, diag

        except Exception as e:
            diag["exception"] = str(e)
            return ValidationStatus.WARNING, diag

    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[ValidationStatus, Dict[str, Any]]:
        """
        Inspects audio sample rate, channels, clipping, and digital silence.
        """
        diag: Dict[str, Any] = {"file_path": file_path}

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            diag["error"] = "Audio file does not exist or has 0 bytes."
            return ValidationStatus.FAILED, diag

        try:
            import scipy.io.wavfile
            sr, data = scipy.io.wavfile.read(file_path)
            diag["sample_rate"] = sr
            diag["channels"] = data.shape[1] if data.ndim > 1 else 1
            diag["duration_sec"] = len(data) / sr

            # Convert to float [-1.0, 1.0]
            if data.dtype == np.int16:
                float_audio = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                float_audio = data.astype(np.float32) / 2147483648.0
            else:
                float_audio = data.astype(np.float32)

            peak = float(np.max(np.abs(float_audio)))
            rms = float(np.sqrt(np.mean(float_audio ** 2)))
            diag["peak_linear"] = peak
            diag["rms"] = rms

            if rms < 1e-6:
                diag["warning"] = "Audio file contains digital silence (RMS < 1e-6)."
                return ValidationStatus.WARNING, diag

            if peak >= 0.999:
                diag["warning"] = "Audio reaches 0 dBFS ceiling; potential clipping detected."
                return ValidationStatus.WARNING, diag

            return ValidationStatus.PASSED, diag

        except Exception as e:
            diag["exception"] = str(e)
            return ValidationStatus.WARNING, diag
