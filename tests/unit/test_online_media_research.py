"""
Unit Tests for YouTube & Online Media Research, Audio Extraction, and Reference Intelligence.
Department: 03_media_ingestion/online_media & 04_media_intelligence
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import UUID, uuid4

from core.assets.database import AssetDatabase, AssetRole, MediaType
from core.assets.intelligence_models import ReferenceProfile
from departments.media_ingestion.online_media.models import (
    AudioAnalysisReport,
    AudioExtractionRequest,
    MediaImportProgress,
    MediaImportRequest,
    MediaPermissionTier,
    OnlineMediaSearchQuery,
    OnlineVideoMetadata,
    PermissionDeclaration,
)
from departments.media_ingestion.online_media.youtube_research_service import (
    YouTubeResearchService,
)
from departments.media_ingestion.online_media.audio_extraction_service import (
    AudioExtractionService,
)
from departments.media_ingestion.online_media.online_acquisition_service import (
    OnlineMediaAcquisitionService,
)
from departments.media_intelligence.reference_analyzer import (
    ReferenceAnalysisService,
)


class TestOnlineMediaResearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="studio_online_media_test_")
        cls.db_path = os.path.join(cls.temp_dir, "test_online_assets.db")
        cls.db = AssetDatabase(cls.db_path)
        cls.storage_dir = Path(cls.temp_dir) / "media_storage"
        cls.storage_dir.mkdir(parents=True, exist_ok=True)
        cls.project_id = uuid4()
        cls.db.create_project(cls.project_id, "Online Media Test Project")

        cls.research_service = YouTubeResearchService()
        cls.audio_service = AudioExtractionService()
        cls.acquisition_service = OnlineMediaAcquisitionService(
            storage_base_dir=cls.storage_dir, db=cls.db
        )

        # Create a synthetic 2-second test video with audio using lavfi
        cls.synth_video = Path(cls.temp_dir) / "synth_test_video.mp4"
        cmd = [
            "/opt/homebrew/bin/ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-c:a", "aac",
            str(cls.synth_video)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_youtube_url_validation(self):
        """Verifies validation and ID extraction across standard, short, embed, and invalid YouTube URLs."""
        valid_urls = [
            ("https://www.youtube.com/watch?v=9ZnbvL8CVyA", "9ZnbvL8CVyA"),
            ("http://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/9ZnbvL8CVyA", "9ZnbvL8CVyA"),
            ("https://www.youtube.com/shorts/bfWnPtdeY4s", "bfWnPtdeY4s"),
            ("https://www.youtube.com/embed/9ZnbvL8CVyA", "9ZnbvL8CVyA"),
        ]
        for url, expected_id in valid_urls:
            is_valid, vid_id = self.research_service.validate_youtube_url(url)
            self.assertTrue(is_valid, f"Failed on valid URL: {url}")
            self.assertEqual(vid_id, expected_id)

        invalid_urls = [
            "https://vimeo.com/12345678",
            "https://example.com/video.mp4",
            "not_a_url",
            "",
            "https://youtube.com/watch?v=short",  # Less than 11 chars
        ]
        for url in invalid_urls:
            is_valid, vid_id = self.research_service.validate_youtube_url(url)
            self.assertFalse(is_valid, f"Should be invalid: {url}")

    def test_02_oembed_metadata_retrieval(self):
        """Verifies retrieval of official YouTube oEmbed metadata and embed HTML."""
        url = "https://www.youtube.com/watch?v=9ZnbvL8CVyA"
        data = self.research_service.get_oembed_metadata(url)
        if data:  # If internet connectivity active
            self.assertIn("title", data)
            self.assertIn("author_name", data)
            self.assertIn("html", data)
            self.assertIn("iframe", data["html"])

    def test_03_video_metadata_structural_inspection(self):
        """Verifies full structural metadata extraction without downloading media."""
        url = "https://www.youtube.com/watch?v=9ZnbvL8CVyA"
        meta = self.research_service.get_video_metadata(url)
        self.assertIsInstance(meta, OnlineVideoMetadata)
        self.assertEqual(meta.video_id, "9ZnbvL8CVyA")
        self.assertGreater(len(meta.title), 0)
        self.assertEqual(meta.permission_tier, MediaPermissionTier.REFERENCE_ONLY)
        self.assertFalse(meta.is_download_permitted)
        self.assertTrue(meta.is_embeddable)

    def test_04_audio_extraction_and_acoustic_analysis(self):
        """Verifies extracting audio to WAV, computing EBU R128 LUFS, peak dBFS, and 100 waveform peaks."""
        out_wav = Path(self.temp_dir) / "extracted_synth.wav"
        extracted = self.audio_service.extract_audio(
            self.synth_video, out_wav, output_format="wav", sample_rate=48000, channels=2
        )
        self.assertTrue(extracted.exists())

        report = self.audio_service.analyze_audio(extracted, num_waveform_bins=100)
        self.assertIsInstance(report, AudioAnalysisReport)
        self.assertAlmostEqual(report.duration_seconds, 2.0, places=1)
        self.assertEqual(report.sample_rate, 48000)
        self.assertEqual(report.channels, 2)
        self.assertEqual(len(report.waveform_peaks), 100)
        self.assertLess(report.integrated_lufs, 0.0)  # Standard negative LUFS
        self.assertLessEqual(report.peak_dbfs, 0.0)

    def test_05_reference_only_import_blocks_download(self):
        """Verifies that REFERENCE_ONLY declaration registers metadata without downloading stream."""
        req = MediaImportRequest(
            url="https://www.youtube.com/watch?v=9ZnbvL8CVyA",
            media_type="video",
            permission_declaration=PermissionDeclaration.REFERENCE_ONLY,
            destination_role="REFERENCE_VIDEO",
            project_id=str(self.project_id)
        )
        res = self.acquisition_service.import_online_media(req, project_id=self.project_id)
        self.assertEqual(res.status, "completed")
        self.assertEqual(res.permission_tier, MediaPermissionTier.REFERENCE_ONLY)
        self.assertEqual(res.downloaded_bytes, 0)
        self.assertIsNotNone(res.asset_id)

        # Asset should exist in DB
        asset = self.db.get_asset(UUID(res.asset_id))
        self.assertIsNotNone(asset)
        self.assertIn(AssetRole.REFERENCE_VIDEO, asset.roles)

    def test_06_local_file_import_with_sha256(self):
        """Verifies importing user-provided local file, SHA-256 calculation, and central registration."""
        record = self.acquisition_service.import_local_media_file(
            local_path=self.synth_video,
            project_id=self.project_id,
            display_name="User Authorized Footage",
            permission_declaration=PermissionDeclaration.USER_OWNED,
            role=AssetRole.SOURCE_FOOTAGE
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.display_name, "User Authorized Footage")
        self.assertEqual(len(record.checksum_sha256), 64)
        self.assertIn(AssetRole.SOURCE_FOOTAGE, record.roles)

    def test_07_reference_deconstruction_and_inspired_production_spec(self):
        """Verifies reference video analysis, pacing extraction, and AI Director inspired production plan."""
        analyzer = ReferenceAnalysisService()
        ref_id = uuid4()
        profile = analyzer.generate_reference_profile(
            self.synth_video, ref_id, name="Cinematic Underwater Reference"
        )
        self.assertIsInstance(profile, ReferenceProfile)
        self.assertIn("dominant_palette_hex", profile.visual_style)
        self.assertIn("average_shot_length_sec", profile.editing_style)

        # Generate inspired production plan
        plan = ReferenceAnalysisService.generate_inspired_production_spec(
            profile, target_topic="ऑक्टोपस के तीन दिल", target_duration_sec=50.0
        )
        self.assertEqual(plan["target_topic"], "ऑक्टोपस के तीन दिल")
        self.assertIn("originality_hygiene", plan)
        self.assertGreaterEqual(len(plan["planned_scene_structure"]), 4)
        self.assertEqual(plan["planned_scene_structure"][0]["intent"], "hook")

    def test_08_cross_reference_comparison(self):
        """Verifies comparison of multiple reference profiles."""
        analyzer = ReferenceAnalysisService()
        p1 = analyzer.generate_reference_profile(self.synth_video, uuid4(), name="Ref Doc A")
        p2 = analyzer.generate_reference_profile(self.synth_video, uuid4(), name="Ref Doc B")

        comp = ReferenceAnalysisService.compare_multiple_references([p1, p2])
        self.assertEqual(len(comp["compared_profiles"]), 2)
        self.assertIn("mean_asl_sec", comp)
        self.assertIn("editing_recommendation", comp)


if __name__ == "__main__":
    unittest.main()

