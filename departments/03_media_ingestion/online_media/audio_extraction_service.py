"""
Dedicated Audio Extraction, Processing, and Acoustic Analysis Engine.
Department: 03_media_ingestion/online_media & 14_audio_production
Provides multi-format audio extraction, EBU R128 loudness analysis,
waveform envelope generation, and acoustic spectral decomposition.
"""
import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import wave

import numpy as np

from .models import AudioAnalysisReport, AudioExtractionRequest

logger = logging.getLogger("studio.online_media.audio_extraction")


class AudioExtractionService:
    """
    Orchestrates extraction of audio tracks from video files, format conversion,
    waveform envelope sampling, and loudness/quality evaluation.
    """

    def __init__(self, ffmpeg_bin: str = "/opt/homebrew/bin/ffmpeg", ffprobe_bin: str = "/opt/homebrew/bin/ffprobe"):
        self.ffmpeg = ffmpeg_bin
        self.ffprobe = ffprobe_bin

    def extract_audio(
        self,
        input_video_path: Path,
        output_path: Path,
        output_format: str = "wav",
        sample_rate: int = 48000,
        channels: int = 2
    ) -> Path:
        """
        Extracts audio from video file to target format (WAV, FLAC, MP3, AAC).
        """
        input_video_path = input_video_path.resolve()
        if not input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_video_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        codec_map = {
            "wav": ["-acodec", "pcm_s16le"],
            "flac": ["-acodec", "flac"],
            "mp3": ["-acodec", "libmp3lame", "-b:a", "320k"],
            "aac": ["-acodec", "aac", "-b:a", "256k"],
            "m4a": ["-acodec", "aac", "-b:a", "256k"],
        }
        codec_args = codec_map.get(output_format.lower(), ["-acodec", "pcm_s16le"])

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", str(input_video_path),
            "-vn",
            *codec_args,
            "-ar", str(sample_rate),
            "-ac", str(channels),
            str(output_path)
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr}")

        return output_path

    def analyze_audio(self, audio_path: Path, num_waveform_bins: int = 100) -> AudioAnalysisReport:
        """
        Performs comprehensive acoustic analysis:
        EBU R128 integrated loudness, True Peak dBFS, Dynamic Range,
        normalized waveform envelope, and speech vs music energy breakdown.
        """
        audio_path = audio_path.resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 1. Inspect metadata via FFprobe
        duration, sample_rate, channels = self._get_audio_metadata(audio_path)

        # 2. Measure EBU R128 Loudness via FFmpeg ebur128 filter
        lufs, true_peak, lra = self._measure_ebur128(audio_path)

        # 3. Generate Waveform Peaks & Frequency Energy Breakdown
        peaks, speech_ratio, music_ratio, bpm = self._compute_waveform_and_spectral(
            audio_path, num_bins=num_waveform_bins, sample_rate=sample_rate
        )

        return AudioAnalysisReport(
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            channels=channels,
            integrated_lufs=round(lufs, 1),
            peak_dbfs=round(true_peak, 1),
            dynamic_range_db=round(lra, 1),
            waveform_peaks=peaks,
            speech_energy_ratio=round(speech_ratio, 3),
            music_energy_ratio=round(music_ratio, 3),
            estimated_bpm=round(bpm, 1) if bpm else None,
            stem_separation_notes=(
                "Energy ratio is an indicative spectral balance metric and does not perfectly isolate original studio stems."
            )
        )

    def _get_audio_metadata(self, audio_path: Path) -> Tuple[float, int, int]:
        cmd = [
            self.ffprobe,
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = 0.0
        sample_rate = 48000
        channels = 2
        if res.returncode == 0 and res.stdout:
            try:
                data = json.loads(res.stdout)
                streams = data.get("streams", [])
                if streams:
                    s = streams[0]
                    sample_rate = int(s.get("sample_rate", 48000))
                    channels = int(s.get("channels", 2))
                    duration = float(s.get("duration") or data.get("format", {}).get("duration", 0.0))
                else:
                    duration = float(data.get("format", {}).get("duration", 0.0))
            except Exception:
                pass
        return duration, sample_rate, channels

    def _measure_ebur128(self, audio_path: Path) -> Tuple[float, float, float]:
        """
        Runs standard EBU R128 measurement. Defaults to -24.0 LUFS, -1.0 dBFS, 8.0 LU if unmeasured.
        """
        cmd = [
            self.ffmpeg,
            "-nostats",
            "-i", str(audio_path),
            "-filter_complex", "ebur128=peak=true",
            "-f", "null",
            "-"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = res.stderr

        lufs = -24.0
        true_peak = -1.0
        lra = 8.0

        i_match = re.search(r"Integrated loudness:\s+I:\s+([-\d\.]+)\s+LUFS", stderr)
        if i_match:
            try:
                lufs = float(i_match.group(1))
            except ValueError:
                pass

        peak_match = re.search(r"True peak:\s+Peak:\s+([-\d\.]+)\s+dBFS", stderr) or re.search(r"Sample peak:\s+Peak:\s+([-\d\.]+)\s+dBFS", stderr)
        if peak_match:
            try:
                true_peak = float(peak_match.group(1))
            except ValueError:
                pass

        lra_match = re.search(r"Loudness range:\s+LRA:\s+([-\d\.]+)\s+LU", stderr)
        if lra_match:
            try:
                lra = float(lra_match.group(1))
            except ValueError:
                pass

        return lufs, true_peak, lra

    def _compute_waveform_and_spectral(
        self, audio_path: Path, num_bins: int = 100, sample_rate: int = 48000
    ) -> Tuple[List[float], float, float, Optional[float]]:
        """
        Extracts temporary mono WAV if needed and computes waveform envelope and spectral metrics.
        """
        # If already uncompressed 16-bit WAV
        temp_wav: Optional[Path] = None
        target_wav = audio_path
        if audio_path.suffix.lower() != ".wav":
            temp_wav = audio_path.parent / f"_temp_analysis_{audio_path.stem}.wav"
            cmd = [
                self.ffmpeg, "-y", "-i", str(audio_path),
                "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", str(temp_wav)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            target_wav = temp_wav
            sample_rate = 16000

        peaks = [0.0] * num_bins
        speech_ratio = 0.4
        music_ratio = 0.5
        bpm = 120.0

        try:
            with wave.open(str(target_wav), "rb") as wf:
                n_frames = wf.getnframes()
                sr = wf.getframerate()
                n_channels = wf.getnchannels()
                raw_bytes = wf.readframes(min(n_frames, sr * 60))  # Analyze up to 60 seconds

                if raw_bytes:
                    data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
                    if n_channels > 1:
                        data = data[::n_channels]  # Take left channel

                    # Waveform Peaks
                    total_samples = len(data)
                    bin_size = max(1, total_samples // num_bins)
                    computed_peaks = []
                    for i in range(num_bins):
                        chunk = data[i * bin_size : (i + 1) * bin_size]
                        if len(chunk) > 0:
                            pk = float(np.max(np.abs(chunk)) / 32768.0)
                            computed_peaks.append(round(min(1.0, pk), 3))
                        else:
                            computed_peaks.append(0.0)
                    peaks = computed_peaks

                    # Spectral Energy Analysis
                    fft_vals = np.abs(np.fft.rfft(data[:min(len(data), 65536)]))
                    freqs = np.fft.rfftfreq(min(len(data), 65536), d=1.0 / sr)
                    total_energy = float(np.sum(fft_vals**2)) + 1e-9

                    # Speech band: 300 Hz - 3400 Hz
                    speech_mask = (freqs >= 300) & (freqs <= 3400)
                    speech_energy = float(np.sum(fft_vals[speech_mask]**2))
                    speech_ratio = min(1.0, max(0.0, speech_energy / total_energy))

                    # Music band: 40 Hz - 250 Hz (bass/percussion) + 3.5 kHz - 12 kHz (harmonics)
                    music_mask = ((freqs >= 40) & (freqs <= 250)) | ((freqs >= 3500) & (freqs <= 12000))
                    music_energy = float(np.sum(fft_vals[music_mask]**2))
                    music_ratio = min(1.0, max(0.0, music_energy / total_energy))

                    # Simple pulse tempo estimate
                    envelope = np.abs(data)
                    # Downsample envelope to 50 Hz
                    ds_factor = max(1, sr // 50)
                    ds_env = np.mean(envelope[:len(envelope) - (len(envelope) % ds_factor)].reshape(-1, ds_factor), axis=1)
                    ds_env -= np.mean(ds_env)
                    autocorr = np.correlate(ds_env, ds_env, mode='full')
                    autocorr = autocorr[len(autocorr)//2:]
                    # Search range: 60 BPM (50 samples at 50Hz) to 160 BPM (18 samples at 50Hz)
                    min_lag = int(50.0 * 60.0 / 160.0)
                    max_lag = int(50.0 * 60.0 / 60.0)
                    if len(autocorr) > max_lag:
                        lag = min_lag + np.argmax(autocorr[min_lag:max_lag])
                        if lag > 0:
                            bpm = round((50.0 / lag) * 60.0, 1)
        except Exception as e:
            logger.warning(f"Audio analysis fallback triggered: {e}")
        finally:
            if temp_wav and temp_wav.exists():
                try:
                    temp_wav.unlink()
                except Exception:
                    pass

        return peaks, speech_ratio, music_ratio, bpm

