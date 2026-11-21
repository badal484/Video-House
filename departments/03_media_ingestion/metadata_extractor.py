"""
Universal Media Metadata Extraction Engine.
Integrates FFprobe, Pillow, and specialized structural parsers.
Preserves professional parameters: VFR, timecode, color space, HDR, and channel layouts.
"""
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, Optional
from uuid import UUID

from PIL import Image

from core.assets.database import MediaType, TechnicalMetadata
from core.security import MediaSecurityPolicy

class MetadataExtractor:
    def __init__(self, ffprobe_path: Optional[str] = None):
        self.ffprobe_path = ffprobe_path or shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"

    def extract(self, file_path: Path, asset_id: UUID, media_type: MediaType) -> TechnicalMetadata:
        """
        Extracts comprehensive technical metadata tailored to the media type.
        """
        if media_type in (MediaType.VIDEO, MediaType.AUDIO):
            return self._extract_av_metadata(file_path, asset_id)
        elif media_type == MediaType.IMAGE:
            return self._extract_image_metadata(file_path, asset_id)
        elif media_type == MediaType.THREE_D:
            return self._extract_3d_metadata(file_path, asset_id)
        elif media_type == MediaType.ANIMATION:
            return self._extract_animation_metadata(file_path, asset_id)
        elif media_type == MediaType.SUBTITLE:
            return self._extract_subtitle_metadata(file_path, asset_id)
        else:
            return self._extract_generic_metadata(file_path, asset_id)

    def _extract_av_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        """Invokes ffprobe to extract frame-accurate audio and video metadata."""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            "-show_error",
            str(file_path)
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=MediaSecurityPolicy.SUBPROCESS_TIMEOUT_PROBE_SEC
            )
            data = json.loads(res.stdout) if res.stdout else {}
        except Exception as e:
            return TechnicalMetadata(
                asset_id=asset_id,
                raw_probe={"error": str(e)}
            )

        format_info = data.get("format", {})
        streams = data.get("streams", [])
        
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        width = video_stream.get("width") if video_stream else None
        height = video_stream.get("height") if video_stream else None
        
        # Duration
        dur_str = (
            (video_stream and video_stream.get("duration"))
            or (audio_stream and audio_stream.get("duration"))
            or format_info.get("duration")
        )
        duration_sec = float(dur_str) if dur_str and dur_str != "N/A" else None

        # Frame rate parsing (e.g. "24/1" -> 24.0, "24000/1001" -> 23.976)
        fps = None
        avg_fps = None
        is_vfr = False
        if video_stream:
            r_fr = video_stream.get("r_frame_rate", "0/0")
            avg_fr = video_stream.get("avg_frame_rate", "0/0")
            
            def parse_rate(rate_str: str) -> Optional[float]:
                if "/" in rate_str:
                    num, den = rate_str.split("/")
                    n, d = float(num), float(den)
                    return round(n / d, 3) if d != 0 else None
                return float(rate_str) if rate_str else None

            fps = parse_rate(r_fr)
            avg_fps = parse_rate(avg_fr)
            if fps and avg_fps and abs(fps - avg_fps) > 0.05:
                is_vfr = True

        # Codecs
        video_codec = video_stream.get("codec_name") if video_stream else None
        audio_codec = audio_stream.get("codec_name") if audio_stream else None

        # Pixel format and bit depth
        pix_fmt = video_stream.get("pix_fmt") if video_stream else None
        bit_depth = None
        if video_stream:
            raw_depth = video_stream.get("bits_per_raw_sample")
            if raw_depth and raw_depth != "N/A":
                bit_depth = int(raw_depth)
            elif pix_fmt:
                if "12" in pix_fmt:
                    bit_depth = 12
                elif "10" in pix_fmt:
                    bit_depth = 10
                else:
                    bit_depth = 8

        # Aspect ratio
        dar = video_stream.get("display_aspect_ratio") if video_stream else None
        if not dar and width and height:
            gcd = math.gcd(width, height)
            dar = f"{width//gcd}:{height//gcd}"

        # Color and HDR
        color_primaries = video_stream.get("color_primaries") if video_stream else None
        color_transfer = video_stream.get("color_transfer") if video_stream else None
        color_space = video_stream.get("color_space") if video_stream else None
        
        is_hdr = False
        if color_transfer in ["smpte2084", "arib-std-b67"] or color_primaries == "bt2020":
            is_hdr = True

        # Rotation
        rotation = 0
        if video_stream:
            tags = video_stream.get("tags", {})
            if "rotate" in tags:
                try:
                    rotation = int(tags["rotate"])
                except ValueError:
                    pass
            for sd in video_stream.get("side_data_list", []):
                if "rotation" in sd:
                    rotation = int(sd["rotation"])

        # Timecode
        timecode = None
        if video_stream:
            timecode = video_stream.get("tags", {}).get("timecode")
        if not timecode:
            timecode = format_info.get("tags", {}).get("timecode")

        # Audio properties
        audio_sample_rate = int(audio_stream["sample_rate"]) if audio_stream and "sample_rate" in audio_stream else None
        audio_channels = int(audio_stream["channels"]) if audio_stream and "channels" in audio_stream else None
        audio_channel_layout = audio_stream.get("channel_layout") if audio_stream else None

        # Bitrate
        bitrate_bps = None
        bitrate_str = format_info.get("bit_rate") or (video_stream and video_stream.get("bit_rate"))
        if bitrate_str and bitrate_str != "N/A":
            bitrate_bps = int(bitrate_str)

        return TechnicalMetadata(
            asset_id=asset_id,
            width=width,
            height=height,
            duration_seconds=duration_sec,
            frame_rate=fps,
            avg_frame_rate=avg_fps,
            is_vfr=is_vfr,
            video_codec=video_codec,
            audio_codec=audio_codec,
            pixel_format=pix_fmt,
            bit_depth=bit_depth,
            aspect_ratio=dar,
            color_primaries=color_primaries,
            color_transfer=color_transfer,
            color_space=color_space,
            is_hdr=is_hdr,
            rotation=rotation,
            timecode=timecode,
            audio_sample_rate=audio_sample_rate,
            audio_channels=audio_channels,
            audio_channel_layout=audio_channel_layout,
            stream_count=len(streams),
            bitrate_bps=bitrate_bps,
            raw_probe=data
        )

    def _extract_image_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        """Extracts resolution, color mode, alpha channel, and bit depth using Pillow."""
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                mode = img.mode
                is_animated = getattr(img, "n_frames", 1) > 1
                has_alpha = mode in ("RGBA", "LA", "PA") or ("transparency" in img.info)
                
                bit_depth = 8
                if mode in ("I;16", "I;16L", "I;16B"):
                    bit_depth = 16
                elif mode in ("F", "RGBA32F"):
                    bit_depth = 32

                gcd = math.gcd(w, h)
                dar = f"{w//gcd}:{h//gcd}"

                return TechnicalMetadata(
                    asset_id=asset_id,
                    width=w,
                    height=h,
                    aspect_ratio=dar,
                    pixel_format=mode,
                    bit_depth=bit_depth,
                    stream_count=getattr(img, "n_frames", 1),
                    raw_probe={
                        "format": img.format,
                        "mode": mode,
                        "has_alpha": has_alpha,
                        "is_animated": is_animated,
                        "info": {k: str(v) for k, v in img.info.items() if k not in ("icc_profile", "exif")}
                    }
                )
        except Exception as e:
            return TechnicalMetadata(asset_id=asset_id, raw_probe={"error": str(e)})

    def _extract_3d_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        """Parses OBJ / GLTF / USDA structural properties."""
        ext = file_path.suffix.lower().lstrip(".")
        probe_info: Dict[str, Any] = {"format": ext}
        try:
            if ext == "obj":
                v_count = 0
                f_count = 0
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("v "):
                            v_count += 1
                        elif line.startswith("f "):
                            f_count += 1
                probe_info.update({"vertex_count": v_count, "face_count": f_count})
            elif ext == "gltf":
                with open(file_path, "r", encoding="utf-8") as f:
                    gdata = json.load(f)
                probe_info.update({
                    "generator": gdata.get("asset", {}).get("generator"),
                    "version": gdata.get("asset", {}).get("version"),
                    "scene_count": len(gdata.get("scenes", [])),
                    "node_count": len(gdata.get("nodes", [])),
                    "mesh_count": len(gdata.get("meshes", [])),
                    "material_count": len(gdata.get("materials", []))
                })
        except Exception as e:
            probe_info["error"] = str(e)

        return TechnicalMetadata(asset_id=asset_id, raw_probe=probe_info)

    def _extract_animation_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        """Extracts Lottie JSON timing and canvas properties."""
        probe_info: Dict[str, Any] = {}
        width = None
        height = None
        duration = None
        fps = None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ldata = json.load(f)
            if isinstance(ldata, dict):
                width = ldata.get("w")
                height = ldata.get("h")
                fps = float(ldata.get("fr", 24))
                ip = float(ldata.get("ip", 0))
                op = float(ldata.get("op", 0))
                total_frames = max(0, op - ip)
                duration = round(total_frames / fps, 3) if fps > 0 else None
                probe_info = {
                    "lottie_version": ldata.get("v"),
                    "frame_rate": fps,
                    "in_point": ip,
                    "out_point": op,
                    "total_frames": total_frames,
                    "layers_count": len(ldata.get("layers", []))
                }
        except Exception as e:
            probe_info["error"] = str(e)

        return TechnicalMetadata(
            asset_id=asset_id,
            width=width,
            height=height,
            duration_seconds=duration,
            frame_rate=fps,
            raw_probe=probe_info
        )

    def _extract_subtitle_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        """Extracts cue count and duration from SRT/VTT/ASS."""
        cue_count = 0
        first_tc = None
        last_tc = None
        timecode_re = re.compile(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})')
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = timecode_re.search(line)
                    if match:
                        cue_count += 1
                        if not first_tc:
                            first_tc = match.group(1)
                        last_tc = match.group(2)
        except Exception:
            pass

        return TechnicalMetadata(
            asset_id=asset_id,
            timecode=first_tc,
            raw_probe={
                "cue_count": cue_count,
                "first_timecode": first_tc,
                "last_timecode": last_tc
            }
        )

    def _extract_generic_metadata(self, file_path: Path, asset_id: UUID) -> TechnicalMetadata:
        return TechnicalMetadata(
            asset_id=asset_id,
            raw_probe={"file_size": file_path.stat().st_size}
        )

