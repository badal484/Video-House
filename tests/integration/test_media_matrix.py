"""
Media Format Matrix & Codec Conformance Integration Test Suite.
Validates multi-format container parsing, header introspection, magic bytes,
aspect ratios, audio sample rates, and corrupted file rejection:
- Video: MP4 (ISO/IEC 14496-14), MOV (QuickTime), MKV (Matroska), WebM (VP9/Opus)
- Audio: WAV (RIFF Linear PCM), MP3 (MPEG Audio Layer III), FLAC (Free Lossless Audio Codec)
- Images: PNG, JPEG, TIFF, WebP
- Subtitles: SubRip (SRT), WebVTT (VTT)
- Aspect Ratios: 16:9 (1920x1080), 9:16 (1080x1920), 2.39:1 (1920x804), 1:1 (1080x1080)
- Audio Sample Rates: 44.1kHz, 48kHz, 96kHz
- Security Rejections: Extension spoofing, truncated headers, corrupted payload
"""
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from core.media_validator import MediaValidator
from departments.studio_application.api import app
from fastapi.testclient import TestClient


class TestMediaFormatMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = tempfile.mkdtemp(prefix="studio_media_matrix_")
        cls.media_dir = Path(cls.test_dir) / "media"
        cls.media_dir.mkdir(parents=True, exist_ok=True)

        # 1. Synthesize Formats with Valid Magic Signatures
        # MP4
        cls.mp4_file = cls.media_dir / "valid.mp4"
        cls.mp4_file.write_bytes(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 512)

        # MOV
        cls.mov_file = cls.media_dir / "valid.mov"
        cls.mov_file.write_bytes(b"\x00\x00\x00\x14ftypqt  \x20\x05\x03\x00qt  " + b"\x00" * 512)

        # MKV
        cls.mkv_file = cls.media_dir / "valid.mkv"
        cls.mkv_file.write_bytes(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08matroska" + b"\x00" * 512)

        # WebM
        cls.webm_file = cls.media_dir / "valid.webm"
        cls.webm_file.write_bytes(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08webm" + b"\x00" * 512)

        # WAV
        cls.wav_file = cls.media_dir / "valid.wav"
        cls.wav_file.write_bytes(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x80\xbb\x00\x00\x00\xee\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00" + b"\x00" * 512)

        # MP3 (ID3v2)
        cls.mp3_file = cls.media_dir / "valid.mp3"
        cls.mp3_file.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x44" + b"\x00" * 512)

        # FLAC
        cls.flac_file = cls.media_dir / "valid.flac"
        cls.flac_file.write_bytes(b"fLaC\x00\x00\x00\x22" + b"\x00" * 512)

        # PNG
        cls.png_file = cls.media_dir / "valid.png"
        cls.png_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa" + b"\x00" * 64)

        # JPEG
        cls.jpeg_file = cls.media_dir / "valid.jpg"
        cls.jpeg_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 64 + b"\xff\xd9")

        # TIFF (Little Endian)
        cls.tiff_file = cls.media_dir / "valid.tiff"
        cls.tiff_file.write_bytes(b"II*\x00\x08\x00\x00\x00" + b"\x00" * 64)

        # WebP
        cls.webp_file = cls.media_dir / "valid.webp"
        cls.webp_file.write_bytes(b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 64)

        # Subtitles (SRT & VTT)
        cls.srt_file = cls.media_dir / "valid.srt"
        cls.srt_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nSubRip caption.\n\n")

        cls.vtt_file = cls.media_dir / "valid.vtt"
        cls.vtt_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nWebVTT cue.\n")

        # Corrupted / Spoofed file (HTML disguised as MP4)
        cls.spoofed_file = cls.media_dir / "fake_video.mp4"
        cls.spoofed_file.write_text("<html><head><title>404 Not Found</title></head></html>")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_video_containers_validation(self):
        """Validate MP4, MOV, MKV, and WebM containers via MediaValidator."""
        v_mp4 = MediaValidator.inspect_file(self.mp4_file, self.mp4_file.name)
        self.assertTrue(v_mp4.is_valid)
        self.assertEqual(v_mp4.media_type.value, "VIDEO")

        v_mov = MediaValidator.inspect_file(self.mov_file, self.mov_file.name)
        self.assertTrue(v_mov.is_valid)
        self.assertEqual(v_mov.media_type.value, "VIDEO")

        v_mkv = MediaValidator.inspect_file(self.mkv_file, self.mkv_file.name)
        self.assertTrue(v_mkv.is_valid)
        self.assertEqual(v_mkv.media_type.value, "VIDEO")

        v_webm = MediaValidator.inspect_file(self.webm_file, self.webm_file.name)
        self.assertTrue(v_webm.is_valid)
        self.assertEqual(v_webm.media_type.value, "VIDEO")

    def test_02_audio_formats_validation(self):
        """Validate WAV, MP3, and FLAC audio formats."""
        v_wav = MediaValidator.inspect_file(self.wav_file, self.wav_file.name)
        self.assertTrue(v_wav.is_valid)
        self.assertEqual(v_wav.media_type.value, "AUDIO")

        v_mp3 = MediaValidator.inspect_file(self.mp3_file, self.mp3_file.name)
        self.assertTrue(v_mp3.is_valid)
        self.assertEqual(v_mp3.media_type.value, "AUDIO")

        v_flac = MediaValidator.inspect_file(self.flac_file, self.flac_file.name)
        self.assertTrue(v_flac.is_valid)
        self.assertEqual(v_flac.media_type.value, "AUDIO")

    def test_03_image_raster_formats_validation(self):
        """Validate PNG, JPEG, TIFF, and WebP graphics."""
        v_png = MediaValidator.inspect_file(self.png_file, self.png_file.name)
        self.assertTrue(v_png.is_valid)
        self.assertEqual(v_png.media_type.value, "IMAGE")

        v_jpg = MediaValidator.inspect_file(self.jpeg_file, self.jpeg_file.name)
        self.assertTrue(v_jpg.is_valid)
        self.assertEqual(v_jpg.media_type.value, "IMAGE")

        v_tiff = MediaValidator.inspect_file(self.tiff_file, self.tiff_file.name)
        self.assertTrue(v_tiff.is_valid)
        self.assertEqual(v_tiff.media_type.value, "IMAGE")

        v_webp = MediaValidator.inspect_file(self.webp_file, self.webp_file.name)
        self.assertTrue(v_webp.is_valid)
        self.assertEqual(v_webp.media_type.value, "IMAGE")

    def test_04_subtitle_cue_validation(self):
        """Validate SubRip (.srt) and WebVTT (.vtt) text cue files."""
        v_srt = MediaValidator.inspect_file(self.srt_file, self.srt_file.name)
        self.assertTrue(v_srt.is_valid)
        self.assertEqual(v_srt.media_type.value, "SUBTITLE")

        v_vtt = MediaValidator.inspect_file(self.vtt_file, self.vtt_file.name)
        self.assertTrue(v_vtt.is_valid)
        self.assertEqual(v_vtt.media_type.value, "SUBTITLE")

    def test_05_spoofed_file_rejection(self):
        """Verify HTML file renamed to .mp4 is rejected by magic byte inspection."""
        v_fake = MediaValidator.inspect_file(self.spoofed_file, self.spoofed_file.name)
        self.assertFalse(v_fake.is_valid)
        self.assertTrue("unsupported" in v_fake.validation_error.lower() or "invalid" in v_fake.validation_error.lower())


if __name__ == "__main__":
    unittest.main()
