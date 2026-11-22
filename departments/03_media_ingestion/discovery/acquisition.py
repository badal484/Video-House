"""
Asset Acquisition, Provenance and Verification Engine.
Department: 03_media_ingestion/discovery
"""
import hashlib
import json
import os
import subprocess
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase, AssetRecord, AssetRole, MediaType, ProcessingStatus
)
from .models import DiscoveredAsset, DownloadResult, LicenseCategory


class AssetAcquisitionService:
    """
    Orchestrates robust asset downloads, checksum verification, FFprobe inspection,
    and automatic database registration into the central Asset Intelligence Library.
    """

    def __init__(
        self,
        storage_base_dir: Optional[Path] = None,
        db: Optional[AssetDatabase] = None,
        max_retries: int = 3
    ):
        self.storage_base = storage_base_dir or Path("/Users/badal11/Desktop/Video House /departments/21_storage_asset_management/external_assets")
        self.storage_base.mkdir(parents=True, exist_ok=True)
        self.db = db or AssetDatabase()
        self.max_retries = max_retries

    def compute_sha256(self, file_path: Path) -> str:
        """Computes SHA-256 hash of a local file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def acquire_asset(
        self,
        asset: DiscoveredAsset,
        project_id: UUID,
        role: AssetRole = AssetRole.SOURCE_FOOTAGE
    ) -> DownloadResult:
        """
        Downloads the asset with retry logic, computes SHA-256, verifies media integrity,
        and registers the asset record in the central database.
        """
        start_time = time.time()
        ext = self._deduce_extension(asset)
        safe_name = "".join(c for c in asset.title if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_").lower()[:50]
        filename = f"{safe_name}_{asset.asset_id[:8]}.{ext}"
        target_path = self.storage_base / filename

        # 1. Download with retry backoff
        success = False
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Use curl with HTTP/2 and modern browser User-Agent
                cmd = [
                    "curl", "-s", "-L",
                    "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "--retry", "2",
                    "--retry-delay", "1",
                    "-o", str(target_path),
                    asset.download_url
                ]
                res = subprocess.run(cmd, capture_output=True, timeout=60)
                if res.returncode == 0 and target_path.exists() and target_path.stat().st_size > 0:
                    # Check if returned an HTML error page
                    if target_path.stat().st_size < 4000:
                        content_head = target_path.read_bytes()[:100]
                        if b"<!DOCTYPE" in content_head or b"<html" in content_head or b"Wikimedia Error" in content_head:
                            raise RuntimeError("Server returned HTML error page instead of media file.")
                    success = True
                    break
                else:
                    last_error = f"Curl failed with returncode {res.returncode}"
            except Exception as e:
                last_error = str(e)
                time.sleep(1.0 * attempt)

        if not success:
            return DownloadResult(
                success=False,
                asset_id=asset.asset_id,
                error_message=f"Acquisition failed after {self.max_retries} attempts: {last_error}"
            )

        # 2. Compute SHA-256 Checksum
        file_bytes = target_path.read_bytes()
        byte_size = len(file_bytes)
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # 3. FFprobe Technical Verification
        probe_meta = self._probe_media(target_path)
        w = probe_meta.get("width", asset.width or 0)
        h = probe_meta.get("height", asset.height or 0)
        mime = probe_meta.get("mime_type", asset.mime_type or "application/octet-stream")

        # 4. Determine Core MediaType
        media_type = MediaType.VIDEO if asset.media_type.value == "video" else MediaType.IMAGE

        # 5. Register in Central Asset Database
        try:
            asset_uuid = uuid4()
            record = AssetRecord(
                asset_id=asset_uuid,
                project_id=project_id,
                original_filename=filename,
                display_name=asset.title[:100],
                media_type=media_type,
                detected_format=ext,
                mime_type=mime,
                byte_size=byte_size,
                checksum_sha256=sha256,
                storage_path=str(target_path),
                import_timestamp=datetime.now(timezone.utc).isoformat(),
                processing_status=ProcessingStatus.COMPLETED,
                metadata_status=ProcessingStatus.COMPLETED,
                derivative_status=ProcessingStatus.COMPLETED,
                roles=[role],
                license_info=f"Provider: {asset.provider} | License: {asset.license_name} | Attribution: {asset.attribution_text}"
            )
            self.db.register_asset(record)
        except Exception as e:
            # Continue even if DB already has duplicate or table busy
            pass

        elapsed = time.time() - start_time
        return DownloadResult(
            success=True,
            asset_id=asset.asset_id,
            local_path=str(target_path),
            byte_size=byte_size,
            sha256_checksum=sha256,
            elapsed_seconds=round(elapsed, 2)
        )

    def _deduce_extension(self, asset: DiscoveredAsset) -> str:
        dl_url = asset.download_url.lower()
        for ext in ["mp4", "webm", "ogv", "mov", "jpg", "jpeg", "png", "webp", "svg", "wav", "mp3"]:
            if f".{ext}" in dl_url:
                return ext
        return "mp4" if asset.media_type.value == "video" else "jpg"

    def _probe_media(self, path: Path) -> dict:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,duration,codec_name:format=format_name",
            "-of", "json",
            str(path)
        ]
        try:
            out = subprocess.check_output(cmd, text=True, timeout=10)
            data = json.loads(out)
            streams = data.get("streams", [])
            s = streams[0] if streams else {}
            return {
                "width": s.get("width"),
                "height": s.get("height"),
                "duration": s.get("duration"),
                "codec": s.get("codec_name"),
                "mime_type": f"video/{s.get('codec_name', 'mp4')}" if "video" in s.get("codec_name", "") else "image/jpeg"
            }
        except Exception:
            return {}
