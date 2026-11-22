"""
Online Media Acquisition, Permission Enforcement, and Asset Ingestion Engine.
Department: 03_media_ingestion/online_media
Handles authorized video and audio downloads, local file imports,
SHA-256 integrity verification, thumbnail generation, and database registration.
"""
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from core.assets.database import (
    AssetDatabase,
    AssetRecord,
    AssetRole,
    MediaType,
    ProcessingStatus,
)
from .models import (
    MediaImportProgress,
    MediaImportRequest,
    MediaPermissionTier,
    OnlineVideoMetadata,
    PermissionDeclaration,
)
from .youtube_research_service import YouTubeResearchService

logger = logging.getLogger("studio.online_media.acquisition")


class OnlineMediaAcquisitionService:
    """
    Orchestrates authorized media imports, permission gating,
    media downloading, cryptographic integrity checks, and asset library registration.
    """

    def __init__(
        self,
        storage_base_dir: Optional[Path] = None,
        db: Optional[AssetDatabase] = None,
        yt_dlp_binary: str = "/Library/Frameworks/Python.framework/Versions/3.13/bin/yt-dlp",
        ffmpeg_binary: str = "/opt/homebrew/bin/ffmpeg",
        ffprobe_binary: str = "/opt/homebrew/bin/ffprobe",
    ):
        self.storage_base = storage_base_dir or Path("/Users/badal11/Desktop/Video House /departments/21_storage_asset_management/external_assets")
        self.storage_base.mkdir(parents=True, exist_ok=True)
        self.db = db or AssetDatabase()
        self.yt_dlp = yt_dlp_binary
        self.ffmpeg = ffmpeg_binary
        self.ffprobe = ffprobe_binary
        self.research_service = YouTubeResearchService(yt_dlp_binary=self.yt_dlp)
        self.active_jobs: Dict[str, MediaImportProgress] = {}

    def import_online_media(
        self, request: MediaImportRequest, project_id: Optional[UUID] = None
    ) -> MediaImportProgress:
        """
        Executes media import workflow with permission verification.
        If permission is REFERENCE_ONLY, creates a reference metadata asset without downloading streams.
        If permission is AUTHORIZED (user-owned, creator-authorized, CC, public domain), downloads and ingests media.
        """
        job_id = f"job_{uuid4().hex[:12]}"
        project_uuid = project_id or (UUID(request.project_id) if request.project_id else uuid4())

        # Validate URL
        is_yt, video_id = self.research_service.validate_youtube_url(request.url)
        if not is_yt:
            # Check if valid HTTP URL or local file
            if not request.url.startswith("http://") and not request.url.startswith("https://") and not Path(request.url).exists():
                return MediaImportProgress(
                    status="failed",
                    error_message=f"Invalid media URL or file path: {request.url}"
                )

        # 1. Fetch Metadata
        metadata: Optional[OnlineVideoMetadata] = None
        if is_yt and video_id:
            try:
                metadata = self.research_service.get_video_metadata(request.url)
            except Exception as e:
                logger.warning(f"Could not retrieve online metadata: {e}")

        title = metadata.title if metadata else (Path(request.url).stem if Path(request.url).exists() else "Online Media Asset")
        author = metadata.author if metadata else "Unknown"

        # 2. Permission Tier Evaluation
        perm_tier = self._map_permission_tier(request.permission_declaration)

        # 3. Reference-Only Check: Do NOT scrape or download protected media if not authorized
        if request.permission_declaration == PermissionDeclaration.REFERENCE_ONLY:
            asset_id = uuid4()
            license_meta = {
                "source_url": request.url,
                "author": author,
                "permission_tier": perm_tier.value,
                "permission_declaration": request.permission_declaration.value,
                "notes": request.permission_notes or "Registered strictly for research and reference analysis.",
                "download_performed": False,
                "embed_html": metadata.embed_html if metadata else None
            }

            # Register reference metadata asset
            now_iso = datetime.now(timezone.utc).isoformat()
            record = AssetRecord(
                asset_id=asset_id,
                project_id=project_uuid,
                original_filename=f"ref_{video_id or asset_id.hex[:8]}.url",
                display_name=f"[REF] {title}",
                media_type=MediaType.VIDEO if request.media_type == "video" else MediaType.AUDIO,
                detected_format="url_reference",
                mime_type="text/x-uri",
                byte_size=0,
                checksum_sha256="0" * 64,
                storage_path=request.url,
                import_timestamp=now_iso,
                processing_status=ProcessingStatus.COMPLETED,
                metadata_status=ProcessingStatus.COMPLETED,
                derivative_status=ProcessingStatus.QUEUED,
                source_type="YOUTUBE_REFERENCE",
                license_info=json.dumps(license_meta),
                roles=[AssetRole.REFERENCE_VIDEO if request.media_type == "video" else AssetRole.REFERENCE_AUDIO]
            )
            self.db.register_asset(record)

            progress = MediaImportProgress(
                status="completed",
                progress_pct=100.0,
                asset_id=str(asset_id),
                local_path=request.url,
                permission_tier=perm_tier,
                downloaded_bytes=0,
                total_bytes=0,
                speed_str="N/A (Reference-Only Registered)"
            )
            self.active_jobs[job_id] = progress
            return progress

        # 4. Authorized Media Download Execution
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip().replace(" ", "_")[:40]
        ext = "mp4" if request.media_type == "video" else request.audio_format.lower()
        if ext not in ("mp4", "webm", "mkv", "mov", "wav", "mp3", "flac", "aac", "m4a"):
            ext = "wav" if request.media_type == "audio_only" else "mp4"

        unique_name = f"{safe_title}_{uuid4().hex[:8]}.{ext}"
        target_path = self.storage_base / unique_name

        try:
            if Path(request.url).exists():
                # Local authorized file import
                shutil.copy2(Path(request.url), target_path)
            else:
                # Online download via yt-dlp
                self._download_via_ytdlp(request, target_path)

            # Compute SHA-256
            sha256 = self._compute_sha256(target_path)
            file_size = target_path.stat().st_size

            # FFprobe integrity validation
            is_valid, duration = self._validate_media_file(target_path)
            if not is_valid:
                target_path.unlink(missing_ok=True)
                return MediaImportProgress(
                    status="failed",
                    error_message="Downloaded file failed media container / integrity verification."
                )

            # Determine Role
            target_role = AssetRole.SOURCE_FOOTAGE
            if request.destination_role == "REFERENCE_VIDEO":
                target_role = AssetRole.REFERENCE_VIDEO
            elif request.destination_role == "REFERENCE_AUDIO":
                target_role = AssetRole.REFERENCE_AUDIO
            elif request.destination_role == "MUSIC":
                target_role = AssetRole.MUSIC
            elif request.media_type == "audio_only":
                target_role = AssetRole.MUSIC

            asset_id = uuid4()
            now_iso = datetime.now(timezone.utc).isoformat()
            license_meta = {
                "source_url": request.url,
                "author": author,
                "permission_tier": perm_tier.value,
                "permission_declaration": request.permission_declaration.value,
                "notes": request.permission_notes or "Authorized import with verified license declaration.",
                "download_performed": True,
                "duration_sec": duration,
                "sha256": sha256
            }

            media_t = MediaType.VIDEO if request.media_type == "video" else MediaType.AUDIO
            record = AssetRecord(
                asset_id=asset_id,
                project_id=project_uuid,
                original_filename=unique_name,
                display_name=title,
                media_type=media_t,
                detected_format=ext,
                mime_type=f"video/{ext}" if media_t == MediaType.VIDEO else f"audio/{ext}",
                byte_size=file_size,
                checksum_sha256=sha256,
                storage_path=str(target_path),
                import_timestamp=now_iso,
                processing_status=ProcessingStatus.COMPLETED,
                metadata_status=ProcessingStatus.COMPLETED,
                derivative_status=ProcessingStatus.COMPLETED,
                source_type="ONLINE_AUTHORIZED_DOWNLOAD",
                license_info=json.dumps(license_meta),
                roles=[target_role]
            )
            self.db.register_asset(record)

            progress = MediaImportProgress(
                status="completed",
                progress_pct=100.0,
                asset_id=str(asset_id),
                local_path=str(target_path),
                permission_tier=perm_tier,
                downloaded_bytes=file_size,
                total_bytes=file_size,
                speed_str="Verified & Ingested"
            )
            self.active_jobs[job_id] = progress
            return progress

        except Exception as e:
            logger.error(f"Media import execution error: {e}")
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            return MediaImportProgress(
                status="failed",
                error_message=str(e),
                permission_tier=perm_tier
            )

    def import_local_media_file(
        self,
        local_path: Path,
        project_id: UUID,
        display_name: Optional[str] = None,
        permission_declaration: PermissionDeclaration = PermissionDeclaration.USER_OWNED,
        role: AssetRole = AssetRole.SOURCE_FOOTAGE
    ) -> AssetRecord:
        """
        Directly ingests a local user-provided file into the central Asset Library.
        """
        local_path = local_path.resolve()
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        sha256 = self._compute_sha256(local_path)
        file_size = local_path.stat().st_size
        ext = local_path.suffix.lstrip(".").lower()

        # Copy to managed external assets directory
        target_path = self.storage_base / f"{local_path.stem}_{uuid4().hex[:8]}.{ext}"
        shutil.copy2(local_path, target_path)

        media_t = MediaType.AUDIO if ext in ("wav", "mp3", "flac", "aac", "m4a", "ogg") else MediaType.VIDEO
        asset_id = uuid4()
        now_iso = datetime.now(timezone.utc).isoformat()
        perm_tier = self._map_permission_tier(permission_declaration)

        license_meta = {
            "source_type": "LOCAL_USER_IMPORT",
            "permission_tier": perm_tier.value,
            "permission_declaration": permission_declaration.value,
            "original_path": str(local_path)
        }

        record = AssetRecord(
            asset_id=asset_id,
            project_id=project_id,
            original_filename=target_path.name,
            display_name=display_name or local_path.stem,
            media_type=media_t,
            detected_format=ext,
            mime_type=f"video/{ext}" if media_t == MediaType.VIDEO else f"audio/{ext}",
            byte_size=file_size,
            checksum_sha256=sha256,
            storage_path=str(target_path),
            import_timestamp=now_iso,
            processing_status=ProcessingStatus.COMPLETED,
            metadata_status=ProcessingStatus.COMPLETED,
            derivative_status=ProcessingStatus.COMPLETED,
            source_type="LOCAL_USER_FILE",
            license_info=json.dumps(license_meta),
            roles=[role]
        )
        self.db.register_asset(record)
        return record

    def _download_via_ytdlp(self, request: MediaImportRequest, target_path: Path):
        """Executes permitted yt-dlp download with strict format constraints."""
        cmd = [self.yt_dlp, "--no-warnings", "-o", str(target_path)]

        if request.media_type == "audio_only":
            cmd.extend([
                "-x",
                "--audio-format", request.audio_format.lower()
            ])
        else:
            # Video with resolution constraint
            res_val = request.resolution.replace("p", "")
            if res_val.isdigit():
                cmd.extend([
                    "-f", f"bestvideo[height<={res_val}]+bestaudio/best[height<={res_val}]/best",
                    "--merge-output-format", "mp4"
                ])
            else:
                cmd.extend(["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"])

        cmd.append(request.url)

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        if res.returncode != 0:
            raise RuntimeError(f"yt-dlp download failed: {res.stderr[:300]}")

    def _validate_media_file(self, file_path: Path) -> Tuple[bool, float]:
        """Runs ffprobe on file to ensure healthy container and streams."""
        cmd = [
            self.ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(file_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and res.stdout:
            try:
                data = json.loads(res.stdout)
                dur = float(data.get("format", {}).get("duration", 0.0))
                return True, dur
            except Exception:
                pass
        return False, 0.0

    def _compute_sha256(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _map_permission_tier(self, decl: PermissionDeclaration) -> MediaPermissionTier:
        if decl in (PermissionDeclaration.USER_OWNED, PermissionDeclaration.PUBLIC_DOMAIN):
            return MediaPermissionTier.COMMERCIAL_PERMITTED
        if decl in (PermissionDeclaration.CREATOR_AUTHORIZED, PermissionDeclaration.CREATIVE_COMMONS):
            return MediaPermissionTier.EDITING_PERMITTED
        return MediaPermissionTier.REFERENCE_ONLY
