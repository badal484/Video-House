# Ingestion Security & Input Hardening Specification
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 Specification  
**Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Threat Model & Security Posture

Every incoming file uploaded or imported into the studio is treated as **untrusted, hostile input**. The system defends against five primary threat vectors:
1. **Path Traversal & Directory Overwriting:** Attacking file paths to write into system directories (`/etc/`, system libraries, or other project roots).
2. **Shell Injection via CLI Wrappers:** Exploiting FFmpeg or FFprobe command-line invocations via shell metacharacters (`|`, `;`, `&`, `$`, `` ` ``).
3. **Resource Exhaustion & Decompression Bombs:** Uploading multi-gigabyte files or highly compressed nested zip/gzip archives to deplete host disk and RAM.
4. **Extension Spoofing & Malicious Payloads:** Disguising executable scripts (`.sh`, `.exe`, `.py`) as media (`.mp4`, `.png`).
5. **Subprocess Hangs & CPU Lockups:** Malformed media headers causing decoders to enter infinite spin-loops.

---

## 2. Hardened Defense Controls

### 2.1 Strict Path Sanitization & Resolution
- **Filename Cleansing:** `MediaSecurityPolicy.sanitize_filename` uses regular expression `[^a-zA-Z0-9_\-\.]` to strip all control characters, directory separators (`/`, `\`), and directory traversal sequences (`..`).
- **Canonical Boundary Check:** `MediaSecurityPolicy.resolve_safe_path` resolves the path using Python `Path.resolve()` and explicitly validates that the path is an exact descendant of the allowed root using `target.relative_to(base_dir)`. Any violation immediately raises `SecurityError`.

### 2.2 Shell Injection Elimination
- **Zero Shell Execution:** All subprocess calls (`ffmpeg`, `ffprobe`) use parameterized array lists `subprocess.run(["ffmpeg", "-i", str(input), ...])` with `shell=False`. Arguments are passed directly to the OS kernel `execve` syscall, completely bypassing the shell interpreter and neutralizing injection attacks.

### 2.3 Subprocess Timeouts
- **Probing Ceiling:** All `ffprobe` operations enforce `timeout=20` seconds.
- **Transcoding Ceiling:** All `ffmpeg` proxy operations enforce `timeout=300` seconds. Any hung or stalled decoder process is terminated immediately with SIGKILL.

### 2.4 File Size Quotas
- Hard ceilings enforced before or during streaming ingestion:
  - Video Assets: Max 10.0 GB
  - Audio Assets: Max 1.0 GB
  - Image Assets: Max 250 MB
  - Text & Documents: Max 100 MB

### 2.5 Magic Signature & Deep Content Inspection
- Rather than trusting user-provided file extensions, `MediaValidator` checks file headers against verified magic byte signatures (e.g. `ftyp` box for MP4, `EBML` for MKV, `RIFF` for WAV, `PNG` magic bytes). An executable or text document renamed to `.mp4` is rejected.

