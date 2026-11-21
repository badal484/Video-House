# Rendering Security, Isolation & Asset Protection Specification

## 1. Security Architecture Overview
Media production pipelines ingest external user footage, third-party motion graphics templates, fonts, and LUT files. The studio enforces strict sandboxing and security hygiene.

## 2. Security Safeguards Implemented

### 2.1 Untrusted Input Sandboxing
- External project files, user-uploaded fonts (`.ttf`, `.otf`), and LUT files (`.cube`) are treated as untrusted data.
- Fonts and LUTs are parsed using memory-safe Python parsers with bounds checking before being loaded into rendering pipelines.
- Execution of arbitrary shell scripts embedded in uploaded projects is strictly blocked.

### 2.2 Path Traversal & File Sanitization
- All output filenames and paths are sanitized against directory traversal attacks (`../`, symlinks).
- Outputs are constrained strictly within designated workspace storage roots (`storage/deliveries/`, `temp/scratch/`).

### 2.3 Ephemeral Credentials & Token Scope
- Cloud worker communication utilizes short-lived HMAC or signed JWT tokens with 1-hour expiration.
- Cloud storage uploads use pre-signed URLs restricted to specific object keys and `PUT` verbs only.

