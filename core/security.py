"""
Security safeguards and sanitization for media ingestion.
Prevents path traversal, shell injection, archive bombs, and malicious spoofed files.
"""
import os
from pathlib import Path
import re
from typing import Tuple

SAFE_FILENAME_RE = re.compile(r'[^a-zA-Z0-9_\-\.]')

class SecurityError(Exception):
    """Raised when an operation violates security policies."""
    pass

class MediaSecurityPolicy:
    MAX_VIDEO_SIZE_BYTES = 10 * 1024 * 1024 * 1024      # 10 GB
    MAX_AUDIO_SIZE_BYTES = 1024 * 1024 * 1024           # 1 GB
    MAX_IMAGE_SIZE_BYTES = 250 * 1024 * 1024            # 250 MB
    MAX_DOCUMENT_SIZE_BYTES = 100 * 1024 * 1024         # 100 MB
    SUBPROCESS_TIMEOUT_PROBE_SEC = 20                   # 20 sec max for ffprobe
    SUBPROCESS_TIMEOUT_RENDER_SEC = 300                 # 5 min max for derivative transcoding

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Strips directory components and replaces unsafe characters.
        Prevents path traversal attacks like '../../etc/passwd'.
        """
        # Strip directory components
        base = os.path.basename(filename.strip().replace('\\', '/'))
        # Replace non-whitelisted characters with underscore
        clean = SAFE_FILENAME_RE.sub('_', base)
        # Collapse multiple dots or underscores
        clean = re.sub(r'\.{2,}', '.', clean)
        clean = re.sub(r'_{2,}', '_', clean)
        if not clean or clean == '.':
            clean = "unnamed_asset.bin"
        return clean

    @staticmethod
    def resolve_safe_path(base_dir: Path, relative_path: str) -> Path:
        """
        Resolves relative path within base_dir.
        Raises SecurityError if the resolved path escapes base_dir.
        """
        base_dir = base_dir.resolve()
        target_path = (base_dir / relative_path).resolve()
        try:
            target_path.relative_to(base_dir)
        except ValueError:
            raise SecurityError(f"Path traversal detected: {relative_path} attempts to escape {base_dir}")
        return target_path

    @staticmethod
    def validate_file_size(byte_size: int, media_category: str) -> None:
        """
        Validates file size against category ceilings.
        """
        limits = {
            "VIDEO": MediaSecurityPolicy.MAX_VIDEO_SIZE_BYTES,
            "AUDIO": MediaSecurityPolicy.MAX_AUDIO_SIZE_BYTES,
            "IMAGE": MediaSecurityPolicy.MAX_IMAGE_SIZE_BYTES,
            "DOCUMENT": MediaSecurityPolicy.MAX_DOCUMENT_SIZE_BYTES,
            "DEFAULT": MediaSecurityPolicy.MAX_DOCUMENT_SIZE_BYTES
        }
        max_allowed = limits.get(media_category.upper(), limits["DEFAULT"])
        if byte_size > max_allowed:
            raise SecurityError(
                f"File size {byte_size} bytes exceeds maximum allowed {max_allowed} bytes for category {media_category}"
            )
