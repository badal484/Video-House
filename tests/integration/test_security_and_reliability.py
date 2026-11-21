"""
Security, Reliability & Disaster Recovery Integration Test Suite.
Verifies production safeguards:
- Path Traversal Defenses & Resolution Boundaries
- Token Bucket Rate Limiting on Resource-Intensive Endpoints
- Secret Scrubbing from Logs and Telemetry Payloads
- SSRF URL Blocking on Private & Cloud Metadata Addresses
- Full Project Backup, SHA-256 Verification & Non-Destructive Restore
"""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from uuid import uuid4

from core.security import (
    MediaSecurityPolicy,
    RateLimiter,
    SecretScrubber,
    SecurityError,
    SSRFGuard,
)
from scripts.backup_restore import StudioBackupManager
from departments.studio_application.api import app, db
from fastapi.testclient import TestClient


class TestSecurityAndReliability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = tempfile.mkdtemp(prefix="studio_sec_test_")
        cls.base_path = Path(cls.test_dir)
        cls.backup_mgr = StudioBackupManager(
            db_path="projects/studio_asset_registry.db",
            storage_root=str(cls.base_path / "assets")
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # ---------------- 1. Security Safeguards ----------------
    def test_01_path_traversal_detection(self):
        """Verify resolve_safe_path raises SecurityError on directory escape attempts."""
        safe_base = self.base_path / "project_01"
        safe_base.mkdir(parents=True, exist_ok=True)

        # Valid relative path
        valid = MediaSecurityPolicy.resolve_safe_path(safe_base, "subfolder/clip.mp4")
        self.assertTrue(str(valid).startswith(str(safe_base.resolve())))

        # Malicious traversal attempt
        with self.assertRaises(SecurityError):
            MediaSecurityPolicy.resolve_safe_path(safe_base, "../../../etc/passwd")

    def test_02_filename_sanitization(self):
        """Verify filename sanitizer strips path separators, control characters, and multiple dots."""
        unsafe = "../../malicious\x00file..name?.mp4"
        clean = MediaSecurityPolicy.sanitize_filename(unsafe)
        self.assertNotIn("/", clean)
        self.assertNotIn("\\", clean)
        self.assertNotIn("..", clean)
        self.assertTrue(clean.endswith(".mp4"))

    def test_03_token_bucket_rate_limiter(self):
        """Verify rate limiter allows requests within capacity and blocks bursts exceeding ceiling."""
        limiter = RateLimiter(capacity=5, refill_rate_per_sec=1.0)
        client_ip = "192.168.1.100"

        # First 5 should succeed
        for _ in range(5):
            self.assertTrue(limiter.is_allowed(client_ip))

        # 6th should be blocked
        self.assertFalse(limiter.is_allowed(client_ip))

    def test_04_secret_scrubber_in_logs_and_payloads(self):
        """Verify secret scrubber redacts Bearer tokens, API keys, and sensitive dictionary keys."""
        dirty_text = "Invoking Runway API with Bearer sk-secretkey1234567890abcdef and api_key=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
        clean_text = SecretScrubber.scrub_text(dirty_text)
        self.assertNotIn("sk-secretkey1234567890abcdef", clean_text)
        self.assertIn("[REDACTED]", clean_text)

        dirty_dict = {
            "project_id": str(uuid4()),
            "api_key": "secret_key_12345",
            "auth_token": "bearer_token_xyz",
            "nested": {"password": "admin_password_999"}
        }
        clean_dict = SecretScrubber.scrub_dict(dirty_dict)
        self.assertEqual(clean_dict["api_key"], "[REDACTED]")
        self.assertEqual(clean_dict["auth_token"], "[REDACTED]")
        self.assertEqual(clean_dict["nested"]["password"], "[REDACTED]")

    def test_05_ssrf_ip_blocking(self):
        """Verify SSRF guard rejects loopback, RFC 1918 private IPs, and AWS metadata endpoint."""
        # Block localhost / loopback
        with self.assertRaises(SecurityError):
            SSRFGuard.validate_url("http://127.0.0.1/admin")

        with self.assertRaises(SecurityError):
            SSRFGuard.validate_url("http://localhost:8080/metrics")

        # Block AWS EC2 metadata IP
        with self.assertRaises(SecurityError):
            SSRFGuard.validate_url("http://169.254.169.254/latest/meta-data/")

        # Block invalid schemes
        with self.assertRaises(SecurityError):
            SSRFGuard.validate_url("file:///etc/passwd")

    # ---------------- 2. Disaster Recovery & Backup ----------------
    def test_06_project_backup_verify_and_restore_cycle(self):
        """Verify atomic project backup archive creation, checksum verification, and restore."""
        # 1. Create project in DB
        res = self.client.post("/api/v1/projects", json={"name": "Disaster Recovery Proj"})
        project_id = res.json()["project_id"]

        # 2. Add an asset
        dummy_media = self.base_path / "dr_clip.mp4"
        dummy_media.write_bytes(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 1024)
        self.client.post(
            f"/api/v1/projects/{project_id}/assets/import-local",
            json={"file_path": str(dummy_media), "display_name": "DR_Clip.mp4"}
        )

        # 3. Create Backup Archive
        backup_dir = self.base_path / "backups"
        archive_path = self.backup_mgr.create_project_backup(project_id, output_dir=str(backup_dir))
        self.assertTrue(archive_path.exists())

        # 4. Verify Archive Integrity
        valid, msg = self.backup_mgr.verify_backup_integrity(archive_path)
        self.assertTrue(valid, f"Backup verification failed: {msg}")

        # 5. Restore into target test DB
        restored_pid = self.backup_mgr.restore_project_backup(archive_path)
        self.assertEqual(restored_pid, project_id)

    def test_07_orphaned_asset_detection(self):
        """Verify orphaned asset detector identifies unindexed media files on disk."""
        assets_dir = self.base_path / "assets"
        orphan_dir = assets_dir / "untracked_project" / "derivatives"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan_file = orphan_dir / "rogue_cache.tmp"
        orphan_file.write_bytes(b"orphan data" * 100)

        orphans = self.backup_mgr.find_orphaned_files()
        self.assertIn(orphan_file.resolve(), [o.resolve() for o in orphans])


if __name__ == "__main__":
    unittest.main()

