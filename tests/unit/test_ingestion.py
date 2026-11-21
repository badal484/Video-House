"""
Comprehensive automated test suite for Part 02: Universal Media Ingestion & Asset Management.
Tests file imports, validation, checksums, metadata extraction, derivatives, security, and SQLite persistence.
Uses small synthetic test assets generated programmatically via FFmpeg, Pillow, and text.
"""
import asyncio
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import uuid4

from PIL import Image

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    DerivativeType,
    MediaType,
    ProcessingStatus
)
from core.media_validator import FormatDetectionResult, MediaValidator
from core.orchestration.job_queue import IngestionJobQueue
from core.security import MediaSecurityPolicy, SecurityError
from core.storage.storage_service import StorageService
from departments.media_ingestion.metadata_extractor import MetadataExtractor
from departments.media_ingestion.derivative_generator import DerivativeGenerator
from departments.media_ingestion.service import MediaIngestionService

class TestUniversalMediaIngestion(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Create temporary directory for test sandbox
        cls.test_dir = Path(tempfile.mkdtemp(prefix="studio_test_ingest_"))
        cls.db_path = cls.test_dir / "test_asset_registry.db"
        cls.storage_dir = cls.test_dir / "assets"
        cls.temp_dir = cls.test_dir / "temp"
        cls.samples_dir = cls.test_dir / "samples"
        cls.samples_dir.mkdir(parents=True, exist_ok=True)

        cls.ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        cls.ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"

        # 1. Generate Synthetic Video Asset (MP4 with H.264 video + AAC audio, 1 sec, 320x240)
        cls.sample_video = cls.samples_dir / "sample_video.mp4"
        subprocess.run([
            cls.ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1.5:size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k",
            str(cls.sample_video)
        ], capture_output=True, check=True)

        # 2. Generate Synthetic Audio Asset (WAV 44.1kHz, 1.0 sec)
        cls.sample_audio = cls.samples_dir / "sample_audio.wav"
        subprocess.run([
            cls.ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1.0",
            "-ar", "44100", "-ac", "2",
            str(cls.sample_audio)
        ], capture_output=True, check=True)

        # 3. Generate Synthetic Image Asset (PNG with Alpha, 200x200)
        cls.sample_image = cls.samples_dir / "sample_image.png"
        img = Image.new("RGBA", (200, 200), (255, 0, 128, 200))
        img.save(cls.sample_image, "PNG")

        # 4. Generate Synthetic Subtitle Asset (SRT)
        cls.sample_srt = cls.samples_dir / "sample_subtitles.srt"
        cls.sample_srt.write_text(
            "1\n00:00:00,100 --> 00:00:01,200\nHello, welcome to Universal Video Studio.\n",
            encoding="utf-8"
        )

        # 5. Generate Synthetic Lottie Animation Asset (JSON)
        cls.sample_lottie = cls.samples_dir / "sample_lottie.json"
        lottie_data = {
            "v": "5.5.2",
            "fr": 30.0,
            "ip": 0.0,
            "op": 60.0,
            "w": 1920,
            "h": 1080,
            "layers": [{"ty": 4, "nm": "Shape Layer 1"}]
        }
        cls.sample_lottie.write_text(json.dumps(lottie_data), encoding="utf-8")

        # 6. Generate Synthetic 3D Model (Wavefront OBJ)
        cls.sample_obj = cls.samples_dir / "sample_cube.obj"
        cls.sample_obj.write_text(
            "v 0.0 0.0 0.0\nv 1.0 0.0 0.0\nv 1.0 1.0 0.0\nf 1 2 3\n",
            encoding="utf-8"
        )

        # 7. Generate Corrupted Media File
        cls.sample_corrupt = cls.samples_dir / "corrupted_media.mov"
        cls.sample_corrupt.write_bytes(b"\x00\x00\x00\x18ftypqt  \x00\x00corruptgarbagebytes!@#$%^&*()")

        # 8. Generate Extension-Spoofed File (Text file renamed to .mp4)
        cls.sample_spoofed = cls.samples_dir / "spoofed_payload.mp4"
        cls.sample_spoofed.write_text("THIS IS NOT A REAL VIDEO FILE. EXTENSION SPOOF TEST.", encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    async def asyncSetUp(self):
        self.db = AssetDatabase(str(self.db_path))
        self.storage = StorageService(str(self.storage_dir), str(self.temp_dir))
        self.job_queue = IngestionJobQueue(self.db, max_concurrent_workers=2)
        await self.job_queue.start()

        self.extractor = MetadataExtractor(self.ffprobe)
        self.generator = DerivativeGenerator(self.storage, self.ffmpeg)
        self.service = MediaIngestionService(
            db=self.db,
            storage=self.storage,
            job_queue=self.job_queue,
            extractor=self.extractor,
            generator=self.generator
        )

        # Create test project
        self.project_id = uuid4()
        self.db.create_project(self.project_id, "Test Ingestion Project", {"fps": 24.0})

    async def asyncTearDown(self):
        await self.job_queue.stop()

    # -------------------------------------------------------------
    # 1. Validation & Content Inspection Tests
    # -------------------------------------------------------------
    def test_magic_signature_validation(self):
        # Valid video
        res_vid = MediaValidator.inspect_file(self.sample_video, self.sample_video.name)
        self.assertTrue(res_vid.is_valid)
        self.assertEqual(res_vid.media_type, MediaType.VIDEO)

        # Valid audio
        res_aud = MediaValidator.inspect_file(self.sample_audio, self.sample_audio.name)
        self.assertTrue(res_aud.is_valid)
        self.assertEqual(res_aud.media_type, MediaType.AUDIO)

        # Valid image
        res_img = MediaValidator.inspect_file(self.sample_image, self.sample_image.name)
        self.assertTrue(res_img.is_valid)
        self.assertEqual(res_img.media_type, MediaType.IMAGE)

        # Valid subtitle
        res_sub = MediaValidator.inspect_file(self.sample_srt, self.sample_srt.name)
        self.assertTrue(res_sub.is_valid)
        self.assertEqual(res_sub.media_type, MediaType.SUBTITLE)

        # Valid Lottie
        res_lot = MediaValidator.inspect_file(self.sample_lottie, self.sample_lottie.name)
        self.assertTrue(res_lot.is_valid)
        self.assertEqual(res_lot.media_type, MediaType.ANIMATION)

        # Valid OBJ
        res_obj = MediaValidator.inspect_file(self.sample_obj, self.sample_obj.name)
        self.assertTrue(res_obj.is_valid)
        self.assertEqual(res_obj.media_type, MediaType.THREE_D)

    def test_spoofed_extension_rejection(self):
        """Verify that a text file renamed to .mp4 is rejected by signature validation."""
        res = MediaValidator.inspect_file(self.sample_spoofed, "spoofed_payload.mp4")
        # Should be classified as plain text document or invalid video, NOT valid video
        self.assertNotEqual(res.media_type, MediaType.VIDEO)

    def test_empty_file_validation(self):
        empty_file = self.samples_dir / "empty.dat"
        empty_file.touch()
        res = MediaValidator.inspect_file(empty_file, "empty.dat")
        self.assertFalse(res.is_valid)
        self.assertIn("0 bytes", res.validation_error or "")

    # -------------------------------------------------------------
    # 2. Local Import & Asynchronous Processing Tests
    # -------------------------------------------------------------
    async def test_import_video_and_derivatives(self):
        """Imports a valid MP4 video and verifies full metadata and derivative generation."""
        asset = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_video,
            display_name="Hero Video Take",
            roles=[AssetRole.SOURCE_FOOTAGE]
        )
        self.assertIsNotNone(asset.asset_id)
        self.assertEqual(asset.media_type, MediaType.VIDEO)
        self.assertEqual(asset.display_name, "Hero Video Take")

        # Wait briefly for background derivative processing
        for _ in range(30):
            await asyncio.sleep(0.2)
            updated = self.db.get_asset(asset.asset_id)
            if updated and updated.processing_status == ProcessingStatus.COMPLETED:
                break

        updated = self.db.get_asset(asset.asset_id)
        self.assertEqual(updated.processing_status, ProcessingStatus.COMPLETED)

        # Verify metadata extraction
        meta = self.db.get_technical_metadata(asset.asset_id)
        self.assertIsNotNone(meta)
        self.assertEqual(meta.width, 320)
        self.assertEqual(meta.height, 240)
        self.assertEqual(meta.video_codec, "h264")
        self.assertEqual(meta.audio_codec, "aac")
        self.assertAlmostEqual(meta.duration_seconds, 1.5, delta=0.2)

        # Verify generated derivatives
        derivs = self.db.get_derivatives(asset.asset_id)
        deriv_types = [d.derivative_type for d in derivs]
        self.assertIn(DerivativeType.THUMBNAIL, deriv_types)
        self.assertIn(DerivativeType.LIGHTWEIGHT_PREVIEW, deriv_types)
        self.assertIn(DerivativeType.EXTRACTED_AUDIO, deriv_types)

        # Verify all derivative files exist on disk
        for d in derivs:
            self.assertTrue(Path(d.storage_path).exists(), f"Derivative {d.derivative_type} missing on disk.")

    async def test_import_audio_and_waveform(self):
        """Imports a WAV audio file and verifies normalized preview and waveform peaks."""
        asset = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_audio,
            roles=[AssetRole.MUSIC]
        )
        for _ in range(30):
            await asyncio.sleep(0.2)
            updated = self.db.get_asset(asset.asset_id)
            if updated and updated.processing_status == ProcessingStatus.COMPLETED:
                break

        updated = self.db.get_asset(asset.asset_id)
        self.assertEqual(updated.processing_status, ProcessingStatus.COMPLETED)

        meta = self.db.get_technical_metadata(asset.asset_id)
        self.assertIsNotNone(meta)
        self.assertEqual(meta.audio_sample_rate, 44100)
        self.assertEqual(meta.audio_channels, 2)

        derivs = self.db.get_derivatives(asset.asset_id)
        deriv_types = [d.derivative_type for d in derivs]
        self.assertIn(DerivativeType.AUDIO_PREVIEW, deriv_types)
        self.assertIn(DerivativeType.AUDIO_WAVEFORM, deriv_types)

        # Verify waveform peak content
        wf_record = next(d for d in derivs if d.derivative_type == DerivativeType.AUDIO_WAVEFORM)
        with open(wf_record.storage_path, "r", encoding="utf-8") as f:
            wf_data = json.load(f)
            self.assertIn("peaks", wf_data)
            self.assertGreater(len(wf_data["peaks"]), 10)

    async def test_import_image_and_thumbnails(self):
        """Imports a PNG image and verifies thumbnail and web preview generation."""
        asset = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_image,
            roles=[AssetRole.REFERENCE_IMAGE]
        )
        for _ in range(20):
            await asyncio.sleep(0.1)
            updated = self.db.get_asset(asset.asset_id)
            if updated and updated.processing_status == ProcessingStatus.COMPLETED:
                break

        meta = self.db.get_technical_metadata(asset.asset_id)
        self.assertIsNotNone(meta)
        self.assertEqual(meta.width, 200)
        self.assertEqual(meta.height, 200)
        self.assertEqual(meta.pixel_format, "RGBA")

        derivs = self.db.get_derivatives(asset.asset_id)
        deriv_types = [d.derivative_type for d in derivs]
        self.assertIn(DerivativeType.IMAGE_THUMBNAIL, deriv_types)
        self.assertIn(DerivativeType.IMAGE_PREVIEW, deriv_types)

    # -------------------------------------------------------------
    # 3. Duplicate Deduplication Tests
    # -------------------------------------------------------------
    async def test_duplicate_file_deduplication(self):
        """Verifies that re-importing the same binary file returns existing asset without duplicating files."""
        asset1 = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_audio,
            display_name="First Import"
        )
        asset2 = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_audio,
            display_name="Second Import Attempt"
        )
        self.assertEqual(asset1.asset_id, asset2.asset_id)
        self.assertEqual(asset1.checksum_sha256, asset2.checksum_sha256)

    # -------------------------------------------------------------
    # 4. Security & Boundary Protection Tests
    # -------------------------------------------------------------
    def test_path_traversal_sanitization(self):
        unsafe_name = "../../etc/passwd"
        clean = MediaSecurityPolicy.sanitize_filename(unsafe_name)
        self.assertNotIn("..", clean)
        self.assertNotIn("/", clean)
        self.assertNotIn("\\", clean)

    def test_path_traversal_resolution_error(self):
        with self.assertRaises(SecurityError):
            MediaSecurityPolicy.resolve_safe_path(self.storage_dir, "../../secret.txt")

    def test_file_size_limit_enforcement(self):
        with self.assertRaises(SecurityError):
            # Exceed 250MB image ceiling
            MediaSecurityPolicy.validate_file_size(300 * 1024 * 1024, "IMAGE")

    # -------------------------------------------------------------
    # 5. Asset Role and Safe Deletion Tests
    # -------------------------------------------------------------
    async def test_role_assignment_and_safe_delete(self):
        asset = await self.service.import_local_file(
            project_id=self.project_id,
            source_path=self.sample_srt,
            roles=[AssetRole.SUBTITLE]
        )
        self.assertIn(AssetRole.SUBTITLE, asset.roles)

        # Add secondary role
        self.db.add_asset_role(asset.asset_id, AssetRole.PROJECT_DOCUMENT)
        updated = self.db.get_asset(asset.asset_id)
        self.assertIn(AssetRole.PROJECT_DOCUMENT, updated.roles)

        # Delete asset
        deleted = self.service.delete_asset(asset.asset_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_asset(asset.asset_id))
        self.assertFalse(Path(asset.storage_path).exists())

    # -------------------------------------------------------------
    # 6. Stream Multipart Upload Test
    # -------------------------------------------------------------
    async def test_stream_upload_ingestion(self):
        raw_png = BytesIO()
        test_img = Image.new("RGB", (150, 150), (0, 200, 100))
        test_img.save(raw_png, "PNG")
        raw_png.seek(0)

        asset = await self.service.import_stream(
            project_id=self.project_id,
            stream=raw_png,
            filename="uploaded_logo.png",
            display_name="Streamed Upload Test"
        )
        self.assertIsNotNone(asset.asset_id)
        self.assertEqual(asset.media_type, MediaType.IMAGE)
        self.assertTrue(Path(asset.storage_path).exists())

if __name__ == "__main__":
    unittest.main()
