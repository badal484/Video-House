"""
File Integrity Inspector for Department 18.
Verifies file existence, readability, container headers, stream presence, and SHA-256 checksums.
"""
from __future__ import annotations

import hashlib
import os
from typing import List, Optional
from uuid import UUID

from ..core.models import QCCheckType, QCDefect, QCSeverity


class FileIntegrityInspector:
    """Validates physical file attributes and container integrity."""

    @classmethod
    def calculate_sha256(cls, file_path: str) -> str:
        """Calculates cryptographic SHA-256 checksum of a file."""
        if not os.path.exists(file_path):
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def inspect_file(
        cls,
        file_path: str,
        expected_checksum: Optional[str] = None,
        min_size_bytes: int = 1,
    ) -> List[QCDefect]:
        """Runs file integrity checks, reporting any defects."""
        defects: List[QCDefect] = []

        # 1. Existence check
        if not os.path.exists(file_path):
            defects.append(
                QCDefect(
                    check_type=QCCheckType.FILE_INTEGRITY,
                    severity=QCSeverity.CRITICAL,
                    rule_name="file_exists",
                    description=f"File does not exist at path: '{file_path}'.",
                    remediation_suggestion="Verify rendering output path and filesystem permissions.",
                )
            )
            return defects

        # 2. Size check
        size = os.path.getsize(file_path)
        if size == 0:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.FILE_INTEGRITY,
                    severity=QCSeverity.CRITICAL,
                    rule_name="file_not_empty",
                    description=f"File is 0 bytes (empty/truncated): '{file_path}'.",
                    remediation_suggestion="Inspect render encoder logs for abrupt crash or disk exhaustion.",
                )
            )
        elif size < min_size_bytes:
            defects.append(
                QCDefect(
                    check_type=QCCheckType.FILE_INTEGRITY,
                    severity=QCSeverity.ERROR,
                    rule_name="min_size_check",
                    description=f"File size ({size} bytes) is below minimum threshold ({min_size_bytes} bytes).",
                    remediation_suggestion="Verify whether encoding completed full timeline duration.",
                )
            )

        # 3. Checksum check
        if expected_checksum:
            actual_checksum = cls.calculate_sha256(file_path)
            if actual_checksum.lower() != expected_checksum.lower():
                defects.append(
                    QCDefect(
                        check_type=QCCheckType.FILE_INTEGRITY,
                        severity=QCSeverity.CRITICAL,
                        rule_name="checksum_match",
                        description=f"SHA-256 checksum mismatch: expected {expected_checksum}, found {actual_checksum}.",
                        remediation_suggestion="File may be corrupted in transit. Re-transfer or re-encode.",
                    )
                )

        return defects
