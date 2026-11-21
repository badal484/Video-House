"""
Derivative Generation Engine for Universal Media Ingestion.
Generates thumbnails, contact sheets, web previews, editing proxies, extracted WAV audio, and waveform peak data.
Preserves original media integrity without modification.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

from PIL import Image

from core.assets.database import (
    AssetRecord,
    DerivativeRecord,
    DerivativeType,
    MediaType,
    ProcessingStatus,
    TechnicalMetadata
)
from core.security import MediaSecurityPolicy
from core.storage.storage_service import StorageService

class DerivativeGenerator:
    def __init__(self, storage_service: StorageService, ffmpeg_path: Optional[str] = None):
        self.storage = storage_service
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

    def generate_derivatives(
        self, asset: AssetRecord, metadata: TechnicalMetadata
    ) -> List[DerivativeRecord]:
        """
        Dispatches derivative generation appropriate for the asset media type.
        """
        if asset.media_type == MediaType.VIDEO:
            return self._generate_video_derivatives(asset, metadata)
        elif asset.media_type == MediaType.AUDIO:
            return self._generate_audio_derivatives(asset, metadata)
        elif asset.media_type == MediaType.IMAGE:
            return self._generate_image_derivatives(asset, metadata)
        else:
            return []

    def _generate_video_derivatives(
        self, asset: AssetRecord, metadata: TechnicalMetadata
    ) -> List[DerivativeRecord]:
        results: List[DerivativeRecord] = []
        source_path = Path(asset.storage_path)
        out_dir = self.storage.get_derivatives_dir(asset.project_id, asset.asset_id)
        previews_dir = self.storage.get_previews_dir(asset.project_id, asset.asset_id)

        dur = metadata.duration_seconds or 1.0
        seek_sec = max(0.1, min(dur * 0.1, 5.0))  # Sample at 10% or max 5s in

        # 1. Video Thumbnail (JPEG)
        thumb_path = previews_dir / "thumbnail.jpg"
        cmd_thumb = [
            self.ffmpeg_path, "-y",
            "-ss", str(seek_sec),
            "-i", str(source_path),
            "-vframes", "1",
            "-vf", "scale=640:-1",
            "-q:v", "2",
            str(thumb_path)
        ]
        if self._run_ffmpeg(cmd_thumb) and thumb_path.exists():
            results.append(DerivativeRecord(
                derivative_id=uuid4(),
                asset_id=asset.asset_id,
                derivative_type=DerivativeType.THUMBNAIL,
                storage_path=str(thumb_path),
                byte_size=thumb_path.stat().st_size,
                mime_type="image/jpeg",
                generation_params={"seek_seconds": seek_sec, "scale": "640:-1"},
                created_at=utc_now_iso()
            ))

        # 2. Contact Sheet (3x3 grid)
        if dur >= 3.0:
            contact_path = previews_dir / "contact_sheet.jpg"
            # Extract 9 frames across the duration
            interval = max(1, int((dur * (metadata.frame_rate or 24)) // 9))
            cmd_contact = [
                self.ffmpeg_path, "-y",
                "-i", str(source_path),
                "-vf", f"select='not(mod(n\\,{interval}))',scale=320:180,tile=3x3",
                "-frames:v", "1",
                "-q:v", "3",
                str(contact_path)
            ]
            if self._run_ffmpeg(cmd_contact) and contact_path.exists():
                results.append(DerivativeRecord(
                    derivative_id=uuid4(),
                    asset_id=asset.asset_id,
                    derivative_type=DerivativeType.CONTACT_SHEET,
                    storage_path=str(contact_path),
                    byte_size=contact_path.stat().st_size,
                    mime_type="image/jpeg",
                    generation_params={"grid": "3x3", "frame_interval": interval},
                    created_at=utc_now_iso()
                ))

        # 3. Lightweight Streaming Preview (720p H.264 MP4)
        preview_mp4_path = previews_dir / "preview_720p.mp4"
        cmd_preview = [
            self.ffmpeg_path, "-y",
            "-i", str(source_path),
            "-vf", "scale=-2:720",
            "-c:v", "h264_videotoolbox" if "darwin" in os.sys.platform else "libx264",
            "-b:v", "2500k",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(preview_mp4_path)
        ]
        # Fallback to libx264 if videotoolbox fails
        if not self._run_ffmpeg(cmd_preview):
            cmd_preview[6] = "libx264"
            cmd_preview.insert(7, "-crf")
            cmd_preview.insert(8, "23")
            self._run_ffmpeg(cmd_preview)

        if preview_mp4_path.exists():
            results.append(DerivativeRecord(
                derivative_id=uuid4(),
                asset_id=asset.asset_id,
                derivative_type=DerivativeType.LIGHTWEIGHT_PREVIEW,
                storage_path=str(preview_mp4_path),
                byte_size=preview_mp4_path.stat().st_size,
                mime_type="video/mp4",
                generation_params={"target_height": 720, "codec": "h264"},
                created_at=utc_now_iso()
            ))

        # 4. Extracted Audio Track (24-bit 48kHz WAV) for AI & mixing
        if metadata.audio_codec:
            audio_wav_path = out_dir / "extracted_audio_48k.wav"
            cmd_audio = [
                self.ffmpeg_path, "-y",
                "-i", str(source_path),
                "-vn",
                "-acodec", "pcm_s24le",
                "-ar", "48000",
                str(audio_wav_path)
            ]
            if self._run_ffmpeg(cmd_audio) and audio_wav_path.exists():
                results.append(DerivativeRecord(
                    derivative_id=uuid4(),
                    asset_id=asset.asset_id,
                    derivative_type=DerivativeType.EXTRACTED_AUDIO,
                    storage_path=str(audio_wav_path),
                    byte_size=audio_wav_path.stat().st_size,
                    mime_type="audio/wav",
                    generation_params={"sample_rate": 48000, "bit_depth": 24},
                    created_at=utc_now_iso()
                ))

        # 5. Editing Proxy (720p ProRes Proxy)
        proxy_path = out_dir / "proxy_prores.mov"
        cmd_proxy = [
            self.ffmpeg_path, "-y",
            "-i", str(source_path),
            "-c:v", "prores_ks",
            "-profile:v", "0",  # ProRes Proxy profile
            "-vf", "scale=-2:720",
            "-c:a", "pcm_s16le",
            str(proxy_path)
        ]
        if self._run_ffmpeg(cmd_proxy) and proxy_path.exists():
            results.append(DerivativeRecord(
                derivative_id=uuid4(),
                asset_id=asset.asset_id,
                derivative_type=DerivativeType.PROXY_VIDEO,
                storage_path=str(proxy_path),
                byte_size=proxy_path.stat().st_size,
                mime_type="video/quicktime",
                generation_params={"profile": "prores_proxy", "scale": "-2:720"},
                created_at=utc_now_iso()
            ))

        return results

    def _generate_audio_derivatives(
        self, asset: AssetRecord, metadata: TechnicalMetadata
    ) -> List[DerivativeRecord]:
        results: List[DerivativeRecord] = []
        source_path = Path(asset.storage_path)
        previews_dir = self.storage.get_previews_dir(asset.project_id, asset.asset_id)

        # 1. Normalized Audio Preview (128k AAC MP4/M4A)
        preview_audio_path = previews_dir / "preview_normalized.m4a"
        cmd_prev_audio = [
            self.ffmpeg_path, "-y",
            "-i", str(source_path),
            "-filter_complex", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a", "aac",
            "-b:a", "128k",
            str(preview_audio_path)
        ]
        if self._run_ffmpeg(cmd_prev_audio) and preview_audio_path.exists():
            results.append(DerivativeRecord(
                derivative_id=uuid4(),
                asset_id=asset.asset_id,
                derivative_type=DerivativeType.AUDIO_PREVIEW,
                storage_path=str(preview_audio_path),
                byte_size=preview_audio_path.stat().st_size,
                mime_type="audio/mp4",
                generation_params={"loudnorm_target": -14, "codec": "aac"},
                created_at=utc_now_iso()
            ))

        # 2. Waveform Peak Data (JSON array of 500 normalized floats)
        waveform_path = previews_dir / "waveform.json"
        waveform_data = self._compute_waveform_peaks(source_path, num_points=500)
        if waveform_data:
            with open(waveform_path, "w", encoding="utf-8") as wf:
                json.dump({"peaks": waveform_data, "points": len(waveform_data)}, wf)
            results.append(DerivativeRecord(
                derivative_id=uuid4(),
                asset_id=asset.asset_id,
                derivative_type=DerivativeType.AUDIO_WAVEFORM,
                storage_path=str(waveform_path),
                byte_size=waveform_path.stat().st_size,
                mime_type="application/json",
                generation_params={"points": len(waveform_data)},
                created_at=utc_now_iso()
            ))

        return results

    def _generate_image_derivatives(
        self, asset: AssetRecord, metadata: TechnicalMetadata
    ) -> List[DerivativeRecord]:
        results: List[DerivativeRecord] = []
        source_path = Path(asset.storage_path)
        previews_dir = self.storage.get_previews_dir(asset.project_id, asset.asset_id)

        try:
            with Image.open(source_path) as img:
                orig_w, orig_h = img.size
                
                # 1. Image Thumbnail (320px width)
                thumb_path = previews_dir / "thumbnail.webp"
                thumb_img = img.copy()
                thumb_img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                thumb_img.save(thumb_path, "WEBP", quality=85)
                
                results.append(DerivativeRecord(
                    derivative_id=uuid4(),
                    asset_id=asset.asset_id,
                    derivative_type=DerivativeType.IMAGE_THUMBNAIL,
                    storage_path=str(thumb_path),
                    byte_size=thumb_path.stat().st_size,
                    mime_type="image/webp",
                    generation_params={"max_dimension": 320, "format": "webp"},
                    created_at=utc_now_iso()
                ))

                # 2. Web Preview (1920px max dimension)
                preview_path = previews_dir / "preview_1920.webp"
                if orig_w > 1920 or orig_h > 1920:
                    prev_img = img.copy()
                    prev_img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                    prev_img.save(preview_path, "WEBP", quality=90)
                else:
                    img.save(preview_path, "WEBP", quality=90)

                results.append(DerivativeRecord(
                    derivative_id=uuid4(),
                    asset_id=asset.asset_id,
                    derivative_type=DerivativeType.IMAGE_PREVIEW,
                    storage_path=str(preview_path),
                    byte_size=preview_path.stat().st_size,
                    mime_type="image/webp",
                    generation_params={"max_dimension": 1920, "format": "webp"},
                    created_at=utc_now_iso()
                ))

        except Exception:
            pass

        return results

    def _compute_waveform_peaks(self, audio_path: Path, num_points: int = 500) -> Optional[List[float]]:
        """
        Extracts lightweight downsampled peak amplitudes using FFmpeg raw PCM stream.
        """
        cmd = [
            self.ffmpeg_path, "-v", "quiet",
            "-i", str(audio_path),
            "-ac", "1",
            "-ar", "8000",
            "-f", "s16le",
            "-"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=15)
            if res.returncode != 0 or not res.stdout:
                return None

            raw_bytes = res.stdout
            total_samples = len(raw_bytes) // 2
            if total_samples == 0:
                return None

            import struct
            chunk_size = max(1, total_samples // num_points)
            peaks = []

            for i in range(0, total_samples, chunk_size):
                end = min(total_samples, i + chunk_size)
                max_val = 0
                for s_idx in range(i, end):
                    val = abs(struct.unpack_from("<h", raw_bytes, s_idx * 2)[0])
                    if val > max_val:
                        max_val = val
                peaks.append(round(max_val / 32768.0, 3))
                if len(peaks) >= num_points:
                    break

            return peaks
        except Exception:
            return None

    def _run_ffmpeg(self, cmd: List[str]) -> bool:
        """Executes FFmpeg with process timeout and returncode verification."""
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=MediaSecurityPolicy.SUBPROCESS_TIMEOUT_RENDER_SEC
            )
            return res.returncode == 0
        except Exception:
            return False
