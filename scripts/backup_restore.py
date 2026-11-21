#!/usr/bin/env python3
"""
Production Backup, Recovery & Storage Maintenance Utility.
Performs atomic project backups, archive verification, disaster recovery restore,
orphaned asset detection, and storage quota enforcement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tarfile
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID


def calculate_sha256(file_path: Path) -> str:
    """Calculates cryptographic SHA-256 hash of a file."""
    if not file_path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class StudioBackupManager:
    """Manages project backups, disaster recovery, and storage maintenance."""

    def __init__(self, db_path: str = "projects/studio_asset_registry.db", storage_root: str = "assets"):
        self.db_path = Path(db_path)
        self.storage_root = Path(storage_root)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_project_backup(self, project_id: str, output_dir: str = "backups") -> Path:
        """
        Creates an atomic, self-contained compressed archive containing all project metadata,
        timelines, asset database rows, and original physical media files.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_name = f"backup_{project_id[:8]}_{timestamp}.tar.gz"
        archive_file = out_path / archive_name

        temp_stage = out_path / f"tmp_{project_id[:8]}_{timestamp}"
        temp_stage.mkdir(parents=True, exist_ok=True)

        try:
            conn = self._get_connection()
            # 1. Fetch project row
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
            p_row = cur.fetchone()
            if not p_row:
                raise ValueError(f"Project '{project_id}' not found in database.")

            project_meta = dict(p_row)

            # 2. Fetch all project tables
            cur.execute("SELECT * FROM assets WHERE project_id = ?", (project_id,))
            assets = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM timelines WHERE project_id = ?", (project_id,))
            timelines = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM project_versions WHERE project_id = ?", (project_id,))
            versions = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM render_plans WHERE project_id = ?", (project_id,))
            render_plans = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM qc_reports WHERE project_id = ?", (project_id,))
            qc_reports = [dict(r) for r in cur.fetchall()]

            metadata_dump = {
                "backup_version": "1.0.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "project_id": project_id,
                "project": project_meta,
                "assets": assets,
                "timelines": timelines,
                "versions": versions,
                "render_plans": render_plans,
                "qc_reports": qc_reports,
            }

            meta_file = temp_stage / "project_metadata.json"
            meta_file.write_text(json.dumps(metadata_dump, indent=2))

            # 3. Copy physical assets
            media_stage = temp_stage / "media"
            media_stage.mkdir(exist_ok=True)
            copied_manifest: List[Dict[str, Any]] = []

            for a in assets:
                orig_path_str = a.get("storage_path") or a.get("original_path")
                if orig_path_str:
                    orig_path = Path(orig_path_str)
                    if orig_path.exists() and orig_path.is_file():
                        dest = media_stage / f"{a['asset_id']}_{orig_path.name}"
                        shutil.copy2(orig_path, dest)
                        copied_manifest.append({
                            "asset_id": a["asset_id"],
                            "file_name": dest.name,
                            "sha256": calculate_sha256(dest),
                            "size_bytes": dest.stat().st_size,
                        })

            manifest_file = temp_stage / "backup_manifest.json"
            manifest_file.write_text(json.dumps(copied_manifest, indent=2))

            # 4. Create tar.gz archive
            with tarfile.open(archive_file, "w:gz") as tar:
                tar.add(temp_stage, arcname=f"project_{project_id}")

            return archive_file

        finally:
            if temp_stage.exists():
                shutil.rmtree(temp_stage)

    def verify_backup_integrity(self, archive_file: Path) -> Tuple[bool, str]:
        """Verifies tar archive readability and SHA-256 media checksums."""
        if not archive_file.exists():
            return False, "Archive file does not exist."

        try:
            with tarfile.open(archive_file, "r:gz") as tar:
                names = tar.getnames()
                root_prefix = names[0].split("/")[0] if names else ""
                meta_member = tar.extractfile(f"{root_prefix}/project_metadata.json")
                if not meta_member:
                    return False, "Missing project_metadata.json in archive."

                manifest_member = tar.extractfile(f"{root_prefix}/backup_manifest.json")
                if not manifest_member:
                    return False, "Missing backup_manifest.json in archive."

                manifest = json.loads(manifest_member.read().decode("utf-8"))
                for entry in manifest:
                    member_path = f"{root_prefix}/media/{entry['file_name']}"
                    f_obj = tar.extractfile(member_path)
                    if not f_obj:
                        return False, f"Missing media file {entry['file_name']} in archive."
                    hasher = hashlib.sha256()
                    while chunk := f_obj.read(65536):
                        hasher.update(chunk)
                    computed = hasher.hexdigest()
                    if computed != entry["sha256"]:
                        return False, f"Checksum mismatch for {entry['file_name']}: expected {entry['sha256']}, got {computed}"

            return True, "Backup archive integrity verified (all checksums valid)."
        except Exception as e:
            return False, f"Archive extraction/verification error: {str(e)}"

    def restore_project_backup(self, archive_file: Path, target_db: Optional[str] = None) -> str:
        """Restores a project from a verified backup archive into SQLite and local storage."""
        valid, msg = self.verify_backup_integrity(archive_file)
        if not valid:
            raise ValueError(f"Cannot restore corrupted archive: {msg}")

        dest_db = Path(target_db) if target_db else self.db_path
        extract_tmp = archive_file.parent / f"restore_tmp_{archive_file.stem}"
        extract_tmp.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(archive_file, "r:gz") as tar:
                if hasattr(tarfile, 'data_filter'):
                    tar.extractall(extract_tmp, filter='data')
                else:
                    tar.extractall(extract_tmp)

            # Find root dir
            subdirs = [p for p in extract_tmp.iterdir() if p.is_dir()]
            root_dir = subdirs[0] if subdirs else extract_tmp

            meta_data = json.loads((root_dir / "project_metadata.json").read_text())
            project_id = meta_data["project_id"]
            proj = meta_data["project"]

            # Connect and restore DB
            conn = sqlite3.connect(dest_db)
            cur = conn.cursor()

            # Insert/Replace Project
            cur.execute("""
                INSERT OR REPLACE INTO projects (
                    project_id, name, created_at, updated_at, settings_json
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                proj["project_id"], proj["name"],
                proj.get("created_at", datetime.now(timezone.utc).isoformat()),
                datetime.now(timezone.utc).isoformat(),
                proj.get("settings_json", "{}")
            ))

            # Restore media files to assets/{project_id}/originals
            dest_media_dir = self.storage_root / project_id / "originals"
            dest_media_dir.mkdir(parents=True, exist_ok=True)

            media_source_dir = root_dir / "media"
            for a in meta_data.get("assets", []):
                # Look for matching extracted media file
                aid = a["asset_id"]
                matching = list(media_source_dir.glob(f"{aid}_*"))
                restored_path = a.get("storage_path") or a.get("original_path", "")
                if matching:
                    f = matching[0]
                    dest_file = dest_media_dir / f.name.replace(f"{aid}_", "")
                    shutil.copy2(f, dest_file)
                    restored_path = str(dest_file)

                cur.execute("""
                    INSERT OR REPLACE INTO assets (
                        asset_id, project_id, original_filename, display_name, media_type,
                        detected_format, mime_type, byte_size, checksum_sha256, storage_path,
                        import_timestamp, processing_status, metadata_status, derivative_status,
                        error_message, version, source_type, license_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    a["asset_id"], a["project_id"],
                    a.get("original_filename", a.get("display_name", "asset")),
                    a.get("display_name", "asset"),
                    a.get("media_type", "VIDEO"),
                    a.get("detected_format", "mp4"),
                    a.get("mime_type", "video/mp4"),
                    a.get("byte_size", a.get("file_size_bytes", 0)),
                    a.get("checksum_sha256", a.get("sha256_checksum", "")),
                    restored_path,
                    a.get("import_timestamp", datetime.now(timezone.utc).isoformat()),
                    a.get("processing_status", "COMPLETED"),
                    a.get("metadata_status", "COMPLETED"),
                    a.get("derivative_status", "COMPLETED"),
                    a.get("error_message"),
                    a.get("version", 1),
                    a.get("source_type", "UPLOAD"),
                    a.get("license_info")
                ))

            conn.commit()
            conn.close()
            return project_id

        finally:
            if extract_tmp.exists():
                shutil.rmtree(extract_tmp)

    def find_orphaned_files(self) -> List[Path]:
        """Finds files on disk that are not registered in the asset registry database."""
        if not self.db_path.exists():
            return []

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT storage_path FROM assets WHERE storage_path IS NOT NULL")
        registered_paths = {Path(r[0]).resolve() for r in cur.fetchall() if r[0]}
        conn.close()

        orphans: List[Path] = []
        if self.storage_root.exists():
            for p in self.storage_root.rglob("*"):
                if p.is_file() and "originals" not in p.parts:  # Protect originals always
                    if p.resolve() not in registered_paths:
                        orphans.append(p)
        return orphans


def main():
    parser = argparse.ArgumentParser(description="Universal Studio Backup & Recovery Utility")
    subparsers = parser.add_subparsers(dest="command")

    backup_parser = subparsers.add_parser("backup", help="Create project backup archive")
    backup_parser.add_argument("project_id", help="UUID of project to back up")
    backup_parser.add_argument("--out", default="backups", help="Output directory")

    verify_parser = subparsers.add_parser("verify", help="Verify backup archive integrity")
    verify_parser.add_argument("archive", help="Path to .tar.gz archive")

    restore_parser = subparsers.add_parser("restore", help="Restore project from backup")
    restore_parser.add_argument("archive", help="Path to .tar.gz archive")

    orphans_parser = subparsers.add_parser("orphans", help="Detect orphaned files")

    args = parser.parse_args()
    mgr = StudioBackupManager()

    if args.command == "backup":
        arch = mgr.create_project_backup(args.project_id, args.out)
        print(f"Backup created successfully: {arch}")
    elif args.command == "verify":
        valid, msg = mgr.verify_backup_integrity(Path(args.archive))
        print(f"Verification: {'PASSED' if valid else 'FAILED'} - {msg}")
    elif args.command == "restore":
        pid = mgr.restore_project_backup(Path(args.archive))
        print(f"Project restored successfully: {pid}")
    elif args.command == "orphans":
        orphans = mgr.find_orphaned_files()
        print(f"Found {len(orphans)} orphaned files.")
        for o in orphans[:10]:
            print(f" - {o}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
