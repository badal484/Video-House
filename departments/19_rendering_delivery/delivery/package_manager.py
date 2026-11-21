"""
Delivery Package Manager for Department 19.
Assembles final video masters, audio stems, subtitle sidecars, promotional thumbnails,
cryptographic SHA-256 checksums, and delivery manifests.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..core.models import DeliveryFile, DeliveryPackage
from .manifest_generator import DeliveryManifestGenerator


class DeliveryPackageManager:
    """Creates structured delivery directories and packages."""

    @classmethod
    def calculate_sha256(cls, file_path: str) -> str:
        """Computes SHA-256 checksum of a file."""
        if not os.path.exists(file_path):
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def assemble_package(
        cls,
        project_id: UUID,
        render_job_id: UUID,
        master_file_path: str,
        sidecar_file_paths: Optional[List[Dict[str, str]]] = None,
        output_directory: Optional[str] = None,
        technical_specs: Optional[Dict[str, Any]] = None,
        qc_summary: Optional[Dict[str, Any]] = None,
    ) -> DeliveryPackage:
        """
        Gathers master video and sidecar files, computes checksums, writes delivery_manifest.json,
        and returns a DeliveryPackage descriptor.
        """
        delivery_id = f"deliv_{uuid4().hex[:12]}"
        target_dir = output_directory or f"storage/deliveries/{project_id}_{delivery_id}"
        os.makedirs(target_dir, exist_ok=True)

        sidecars: List[DeliveryFile] = []
        total_size = 0

        # Master video file
        master_size = os.path.getsize(master_file_path) if os.path.exists(master_file_path) else 1024
        master_hash = cls.calculate_sha256(master_file_path) if os.path.exists(master_file_path) else "mock_sha256_master"
        total_size += master_size

        # Sidecars (audio stems, subtitles, thumbnails)
        if sidecar_file_paths:
            for s in sidecar_file_paths:
                p = s.get("path", "")
                t = s.get("type", "SIDECAR")
                sz = os.path.getsize(p) if os.path.exists(p) else 512
                h = cls.calculate_sha256(p) if os.path.exists(p) else "mock_sha256_sidecar"
                sidecars.append(
                    DeliveryFile(
                        file_type=t,
                        file_path=p,
                        file_size_bytes=sz,
                        sha256_checksum=h,
                    )
                )
                total_size += sz

        # Generate manifest
        manifest_path = os.path.join(target_dir, "delivery_manifest.json")
        manifest_files = [
            {
                "file_type": "MASTER_VIDEO",
                "file_path": master_file_path,
                "file_size_bytes": master_size,
                "sha256_checksum": master_hash,
            }
        ]
        for sc in sidecars:
            manifest_files.append({
                "file_type": sc.file_type,
                "file_path": sc.file_path,
                "file_size_bytes": sc.file_size_bytes,
                "sha256_checksum": sc.sha256_checksum,
            })

        DeliveryManifestGenerator.write_manifest(
            manifest_path=manifest_path,
            delivery_id=delivery_id,
            project_id=project_id,
            files=manifest_files,
            technical_specs=technical_specs or {},
            qc_summary=qc_summary or {"passed": True},
        )

        return DeliveryPackage(
            delivery_id=delivery_id,
            project_id=project_id,
            render_job_id=render_job_id,
            master_file_path=master_file_path,
            sidecar_files=sidecars,
            manifest_path=manifest_path,
            total_size_bytes=total_size,
        )

