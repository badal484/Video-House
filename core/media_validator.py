"""
Media validator and format detection engine.
Uses magic bytes, content introspection, and structural parsing.
Never relies solely on file extensions.
"""
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional, Tuple

from core.assets.database import MediaType

@dataclass
class FormatDetectionResult:
    is_valid: bool
    media_type: MediaType
    detected_format: str
    mime_type: str
    is_metadata_extractable: bool
    is_previewable: bool
    is_downstream_supported: bool
    is_external_reference_only: bool
    validation_error: Optional[str] = None

class MediaValidator:
    """
    Validates files by inspecting magic signatures and binary/text headers.
    Distinguishes importability, previewability, and downstream editing support.
    """

    @classmethod
    def inspect_file(cls, file_path: Path, filename_hint: str) -> FormatDetectionResult:
        if not file_path.exists() or not file_path.is_file():
            return FormatDetectionResult(
                is_valid=False,
                media_type=MediaType.UNKNOWN,
                detected_format="unknown",
                mime_type="application/octet-stream",
                is_metadata_extractable=False,
                is_previewable=False,
                is_downstream_supported=False,
                is_external_reference_only=False,
                validation_error="File does not exist or is not a regular file."
            )

        file_size = file_path.stat().st_size
        if file_size == 0:
            return FormatDetectionResult(
                is_valid=False,
                media_type=MediaType.UNKNOWN,
                detected_format="empty",
                mime_type="application/x-empty",
                is_metadata_extractable=False,
                is_previewable=False,
                is_downstream_supported=False,
                is_external_reference_only=False,
                validation_error="File is empty (0 bytes)."
            )

        # Read first 4096 bytes for header inspection
        with open(file_path, "rb") as f:
            header = f.read(4096)

        ext = Path(filename_hint).suffix.lower().lstrip(".")

        # 1. Video signatures
        # MP4 / MOV (ftyp box at offset 4)
        if len(header) >= 12 and header[4:8] == b"ftyp":
            brand = header[8:12].decode("ascii", errors="ignore")
            fmt = "mov" if brand.startswith("qt") else "mp4"
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.VIDEO,
                detected_format=fmt,
                mime_type=f"video/{fmt}",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )
        
        # MKV / WebM (EBML ID \x1a\x45\xdf\xa3)
        if header.startswith(b"\x1a\x45\xdf\xa3"):
            is_webm = b"webm" in header[:64]
            fmt = "webm" if is_webm else "mkv"
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.VIDEO,
                detected_format=fmt,
                mime_type=f"video/{fmt}",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # AVI (RIFF....AVI )
        if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"AVI ":
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.VIDEO,
                detected_format="avi",
                mime_type="video/x-msvideo",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # MPEG-TS (Sync byte 0x47 every 188 bytes)
        if header.startswith(b"\x47") and len(header) >= 376 and header[188] == 0x47:
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.VIDEO,
                detected_format="ts",
                mime_type="video/mp2t",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # FLV
        if header.startswith(b"FLV\x01"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.VIDEO,
                detected_format="flv",
                mime_type="video/x-flv",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # 2. Audio signatures
        # WAV (RIFF....WAVE)
        if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WAVE":
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="wav",
                mime_type="audio/wav",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # FLAC (fLaC)
        if header.startswith(b"fLaC"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="flac",
                mime_type="audio/flac",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # OGG (OggS)
        if header.startswith(b"OggS"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="ogg",
                mime_type="audio/ogg",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # AIFF (FORM....AIFF / AIFC)
        if header.startswith(b"FORM") and len(header) >= 12 and (header[8:12] == b"AIFF" or header[8:12] == b"AIFC"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="aiff",
                mime_type="audio/aiff",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # MP3 (ID3v2 or MPEG sync word 0xFFFB, 0xFFF3, 0xFFF2)
        if header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="mp3",
                mime_type="audio/mpeg",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # AAC (ADTS frame header 0xFFF1 or 0xFFF9)
        if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xF6) == 0xF0:
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.AUDIO,
                detected_format="aac",
                mime_type="audio/aac",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # 3. Image signatures
        # PNG (\x89PNG\r\n\x1a\n)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="png",
                mime_type="image/png",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # JPEG (\xff\xd8\xff)
        if header.startswith(b"\xff\xd8\xff"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="jpeg",
                mime_type="image/jpeg",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # GIF (GIF87a / GIF89a)
        if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="gif",
                mime_type="image/gif",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # WebP (RIFF....WEBP)
        if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="webp",
                mime_type="image/webp",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # TIFF (II*\x00 or MM\x00*)
        if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="tiff",
                mime_type="image/tiff",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # BMP (BM)
        if header.startswith(b"BM"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="bmp",
                mime_type="image/bmp",
                is_metadata_extractable=True,
                is_previewable=True,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # OpenEXR (\x76\x2f\x31\x01)
        if header.startswith(b"\x76\x2f\x31\x01"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.IMAGE,
                detected_format="exr",
                mime_type="image/x-exr",
                is_metadata_extractable=True,
                is_previewable=False,  # EXR requires tone-mapping for browser preview
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # 4. 3D & Animation assets
        # Blender file (BLENDER)
        if header.startswith(b"BLENDER"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.THREE_D,
                detected_format="blend",
                mime_type="application/x-blender",
                is_metadata_extractable=True,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # Binary glTF (glTF)
        if header.startswith(b"glTF"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.THREE_D,
                detected_format="glb",
                mime_type="model/gltf-binary",
                is_metadata_extractable=True,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # Binary USD (PXR-USDC)
        if header.startswith(b"PXR-USDC"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.THREE_D,
                detected_format="usdc",
                mime_type="model/vnd.usdc",
                is_metadata_extractable=True,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # FBX (Kaydara FBX Binary)
        if header.startswith(b"Kaydara FBX Binary"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.THREE_D,
                detected_format="fbx",
                mime_type="application/octet-stream",
                is_metadata_extractable=True,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # Rive animation (RIVE)
        if header.startswith(b"RIVE"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.ANIMATION,
                detected_format="riv",
                mime_type="application/octet-stream",
                is_metadata_extractable=False,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # TrueType / OpenType font
        if header.startswith(b"\x00\x01\x00\x00") or header.startswith(b"OTTO") or header.startswith(b"true"):
            return FormatDetectionResult(
                is_valid=True,
                media_type=MediaType.PRODUCTION_DOCUMENT,
                detected_format="font",
                mime_type="font/otf",
                is_metadata_extractable=False,
                is_previewable=False,
                is_downstream_supported=True,
                is_external_reference_only=False
            )

        # 5. Text-based format parsing (UTF-8 inspection)
        try:
            text_sample = header.decode("utf-8", errors="ignore").strip()
            
            # SVG (XML with <svg)
            if "<svg" in text_sample.lower():
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.IMAGE,
                    detected_format="svg",
                    mime_type="image/svg+xml",
                    is_metadata_extractable=True,
                    is_previewable=True,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # WebVTT subtitle
            if text_sample.startswith("WEBVTT"):
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.SUBTITLE,
                    detected_format="vtt",
                    mime_type="text/vtt",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # Advanced SubStation Alpha (ASS / SSA)
            if "[Script Info]" in text_sample:
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.SUBTITLE,
                    detected_format="ass",
                    mime_type="text/x-ssa",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # SRT Subtitle (starts with number and timecode line "-->")
            lines = [l.strip() for l in text_sample.splitlines() if l.strip()]
            if len(lines) >= 2 and lines[0].isdigit() and "-->" in lines[1]:
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.SUBTITLE,
                    detected_format="srt",
                    mime_type="application/x-subrip",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # Wavefront OBJ 3D model
            if ext == "obj" and any(l.startswith(("v ", "vn ", "vt ", "f ")) for l in lines[:20]):
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.THREE_D,
                    detected_format="obj",
                    mime_type="model/obj",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # USDA (Text OpenUSD)
            if text_sample.startswith("#usda"):
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.THREE_D,
                    detected_format="usda",
                    mime_type="model/vnd.usda",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # Color LUT (.cube)
            if "LUT_3D_SIZE" in text_sample or "LUT_1D_SIZE" in text_sample or text_sample.startswith("TITLE"):
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.PRODUCTION_DOCUMENT,
                    detected_format="lut",
                    mime_type="application/x-lut",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

            # JSON documents (Lottie vs glTF vs generic)
            if text_sample.startswith("{"):
                try:
                    with open(file_path, "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                    # Check Lottie
                    if isinstance(jdata, dict) and "v" in jdata and "fr" in jdata and "ip" in jdata and "op" in jdata:
                        return FormatDetectionResult(
                            is_valid=True,
                            media_type=MediaType.ANIMATION,
                            detected_format="lottie",
                            mime_type="application/json",
                            is_metadata_extractable=True,
                            is_previewable=True,
                            is_downstream_supported=True,
                            is_external_reference_only=False
                        )
                    # Check glTF JSON
                    if isinstance(jdata, dict) and "asset" in jdata and "version" in jdata["asset"]:
                        return FormatDetectionResult(
                            is_valid=True,
                            media_type=MediaType.THREE_D,
                            detected_format="gltf",
                            mime_type="model/gltf+json",
                            is_metadata_extractable=True,
                            is_previewable=False,
                            is_downstream_supported=True,
                            is_external_reference_only=False
                        )
                    return FormatDetectionResult(
                        is_valid=True,
                        media_type=MediaType.PRODUCTION_DOCUMENT,
                        detected_format="json",
                        mime_type="application/json",
                        is_metadata_extractable=True,
                        is_previewable=False,
                        is_downstream_supported=True,
                        is_external_reference_only=False
                    )
                except Exception:
                    pass

            # Plain text / script document
            if ext in ["txt", "md", "fountain", "fdx"]:
                return FormatDetectionResult(
                    is_valid=True,
                    media_type=MediaType.PRODUCTION_DOCUMENT,
                    detected_format=ext,
                    mime_type="text/plain",
                    is_metadata_extractable=True,
                    is_previewable=False,
                    is_downstream_supported=True,
                    is_external_reference_only=False
                )

        except Exception:
            pass

        # 6. Fallback: Extension hint check with warning
        known_exts = {
            "mxf": (MediaType.VIDEO, "video/mxf", True, False, True),
            "stl": (MediaType.THREE_D, "model/stl", True, False, True),
            "usdz": (MediaType.THREE_D, "model/vnd.usdz+zip", True, False, True),
            "hdr": (MediaType.IMAGE, "image/vnd.radiance", True, False, True),
            "fountain": (MediaType.PRODUCTION_DOCUMENT, "text/plain", True, False, True),
            "csv": (MediaType.PRODUCTION_DOCUMENT, "text/csv", True, False, True)
        }
        if ext in known_exts:
            mtype, mime, can_meta, can_prev, can_down = known_exts[ext]
            return FormatDetectionResult(
                is_valid=True,
                media_type=mtype,
                detected_format=ext,
                mime_type=mime,
                is_metadata_extractable=can_meta,
                is_previewable=can_prev,
                is_downstream_supported=can_down,
                is_external_reference_only=True,
                validation_error=f"Identified primarily by extension .{ext}; verify stream compatibility downstream."
            )

        # Unrecognized / Unsupported
        return FormatDetectionResult(
            is_valid=False,
            media_type=MediaType.UNKNOWN,
            detected_format=ext if ext else "unknown",
            mime_type="application/octet-stream",
            is_metadata_extractable=False,
            is_previewable=False,
            is_downstream_supported=False,
            is_external_reference_only=False,
            validation_error=f"Unrecognized or unsupported file format (extension: .{ext})."
        )
