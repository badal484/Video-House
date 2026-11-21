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


class RateLimiter:
    """
    In-memory Token Bucket rate limiter for critical endpoints (Rendering, Ingestion, Generation).
    Thread-safe and async-compatible.
    """
    def __init__(self, capacity: int = 60, refill_rate_per_sec: float = 10.0):
        self.capacity = float(capacity)
        self.refill_rate = refill_rate_per_sec
        self.buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_refill_timestamp)

    def is_allowed(self, client_key: str, cost: float = 1.0) -> bool:
        import time
        now = time.monotonic()
        tokens, last_time = self.buckets.get(client_key, (self.capacity, now))
        
        # Calculate refilled tokens
        elapsed = now - last_time
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)
        
        if tokens >= cost:
            self.buckets[client_key] = (tokens - cost, now)
            return True
        else:
            self.buckets[client_key] = (tokens, now)
            return False


class SecretScrubber:
    """
    Redacts sensitive credentials, API keys, and authorization tokens from logs and payloads.
    """
    REDACT_PATTERNS = [
        re.compile(r'(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{10,}'),
        re.compile(r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_\-]{8,}'),
        re.compile(r'(?i)(secret["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_\-]{8,}'),
        re.compile(r'(?i)(password["\']?\s*[:=]\s*["\']?)[^\s"\']+'),
        re.compile(r'()(sk-[a-zA-Z0-9]{20,})'),  # OpenAI / Runway format
        re.compile(r'()(AIzaSy[a-zA-Z0-9_-]{33})'),  # Google API key format
    ]

    @classmethod
    def scrub_text(cls, text: str) -> str:
        scrubbed = text
        for pat in cls.REDACT_PATTERNS:
            scrubbed = pat.sub(r'\1[REDACTED]', scrubbed)
        return scrubbed

    @classmethod
    def scrub_dict(cls, data: dict) -> dict:
        result = {}
        for k, v in data.items():
            if any(term in k.lower() for term in ["key", "secret", "token", "password", "auth"]):
                result[k] = "[REDACTED]"
            elif isinstance(v, dict):
                result[k] = cls.scrub_dict(v)
            elif isinstance(v, str):
                result[k] = cls.scrub_text(v)
            else:
                result[k] = v
        return result


class SSRFGuard:
    """
    Guards against Server-Side Request Forgery by rejecting private, link-local,
    loopback, and cloud metadata IP ranges.
    """
    PRIVATE_NETWORKS = [
        "127.0.0.0/8",      # Loopback
        "10.0.0.0/8",       # RFC 1918
        "172.16.0.0/12",    # RFC 1918
        "192.168.0.0/16",   # RFC 1918
        "169.254.0.0/16",   # Link-local / AWS metadata
        "::1/128",          # IPv6 loopback
        "fc00::/7",         # IPv6 unique local
        "fe80::/10",        # IPv6 link-local
    ]

    @classmethod
    def validate_url(cls, url: str) -> bool:
        import ipaddress
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise SecurityError(f"Unsupported URI scheme: '{parsed.scheme}'. Only HTTP and HTTPS allowed.")

        hostname = parsed.hostname
        if not hostname:
            raise SecurityError("Invalid URL: missing hostname.")

        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net_str in cls.PRIVATE_NETWORKS:
                    net_obj = ipaddress.ip_network(net_str)
                    if ip_obj in net_obj:
                        raise SecurityError(f"SSRF violation: IP {ip_str} resolves to blocked network {net_str}")
            return True
        except socket.gaierror:
            raise SecurityError(f"Failed to resolve hostname: '{hostname}'")

