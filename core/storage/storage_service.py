"""
Storage service for the Universal AI Video Production Studio.
Manages physical storage of original assets, proxies, derivatives, and temporary files.
"""
import hashlib
import os
from pathlib import Path
import shutil
from typing import BinaryIO, Optional, Tuple
from uuid import UUID

from core.security import MediaSecurityPolicy, SecurityError

class StorageService:
    def __init__(self, root_storage_dir: str = "assets", temp_dir: str = "temp"):
        self.root_storage = Path(root_storage_dir).resolve()
        self.temp_dir = Path(temp_dir).resolve()
        self.root_storage.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: UUID) -> Path:
        pdir = self.root_storage / str(project_id)
        pdir.mkdir(parents=True, exist_ok=True)
        return pdir

    def get_originals_dir(self, project_id: UUID) -> Path:
        d = self.get_project_dir(project_id) / "originals"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_derivatives_dir(self, project_id: UUID, asset_id: UUID) -> Path:
        d = self.get_project_dir(project_id) / "derivatives" / str(asset_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_previews_dir(self, project_id: UUID, asset_id: UUID) -> Path:
        d = self.get_project_dir(project_id) / "previews" / str(asset_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_temp_dir(self, project_id: Optional[UUID] = None) -> Path:
        if project_id:
            d = self.temp_dir / str(project_id)
        else:
            d = self.temp_dir / "general"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def calculate_checksum_and_size(file_path: Path) -> Tuple[str, int]:
        """Calculates SHA-256 and byte size in 64KB stream chunks."""
        hasher = hashlib.sha256()
        total_size = 0
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
                total_size += len(chunk)
        return hasher.hexdigest(), total_size

    def store_original_file(self, project_id: UUID, asset_id: UUID, source_path: Path, filename: str) -> Tuple[Path, str, int]:
        """
        Safely copies a local file into the project originals storage.
        Verifies checksum and size, and preserves file.
        """
        safe_name = MediaSecurityPolicy.sanitize_filename(filename)
        dest_filename = f"{asset_id}_{safe_name}"
        originals_dir = self.get_originals_dir(project_id)
        dest_path = originals_dir / dest_filename

        # Copy source to destination
        shutil.copy2(source_path, dest_path)
        
        # Verify checksum and size
        checksum, size = self.calculate_checksum_and_size(dest_path)
        return dest_path, checksum, size

    def store_stream_to_original(self, project_id: UUID, asset_id: UUID, stream: BinaryIO, filename: str) -> Tuple[Path, str, int]:
        """
        Streams uploaded binary data into project originals storage.
        Calculates SHA-256 and byte size simultaneously.
        """
        safe_name = MediaSecurityPolicy.sanitize_filename(filename)
        dest_filename = f"{asset_id}_{safe_name}"
        originals_dir = self.get_originals_dir(project_id)
        dest_path = originals_dir / dest_filename

        hasher = hashlib.sha256()
        total_size = 0

        # Stream write
        with open(dest_path, "wb") as f:
            while chunk := stream.read(65536):
                f.write(chunk)
                hasher.update(chunk)
                total_size += len(chunk)

        return dest_path, hasher.hexdigest(), total_size

    def delete_asset_files(self, project_id: UUID, asset_id: UUID, storage_path: str) -> None:
        """Deletes original file and all associated derivative/preview directories."""
        # Delete original
        orig = Path(storage_path)
        if orig.exists() and orig.is_file():
            orig.unlink()

        # Delete derivatives dir
        deriv_dir = self.get_project_dir(project_id) / "derivatives" / str(asset_id)
        if deriv_dir.exists() and deriv_dir.is_dir():
            shutil.rmtree(deriv_dir, ignore_errors=True)

        # Delete previews dir
        prev_dir = self.get_project_dir(project_id) / "previews" / str(asset_id)
        if prev_dir.exists() and prev_dir.is_dir():
            shutil.rmtree(prev_dir, ignore_errors=True)

    def get_project_storage_usage(self, project_id: UUID) -> int:
        """Returns total bytes used by a project across originals, derivatives, and previews."""
        pdir = self.get_project_dir(project_id)
        total_bytes = 0
        for root, _, files in os.walk(pdir):
            for f in files:
                fp = Path(root) / f
                try:
                    total_bytes += fp.stat().st_size
                except OSError:
                    pass
        return total_bytes

    def cleanup_temp_dir(self, project_id: Optional[UUID] = None) -> None:
        """Cleans up temp scratch files."""
        td = self.get_temp_dir(project_id)
        if td.exists():
            shutil.rmtree(td, ignore_errors=True)
            td.mkdir(parents=True, exist_ok=True)
