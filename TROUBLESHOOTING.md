# Troubleshooting & Diagnostics Guide
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Operations Guide  

---

## 1. Top Diagnostic Scenarios & Resolutions

### 1.1 `sqlite3.OperationalError: database is locked`
- **Cause:** Multiple concurrent asynchronous writers attempting SQLite transactions without WAL mode or during an uncheckpointed long transaction.
- **Resolution:**
  ```bash
  # Check if WAL mode is enabled
  sqlite3 projects/studio_asset_registry.db "PRAGMA journal_mode;"
  # If not 'wal', enable it:
  sqlite3 projects/studio_asset_registry.db "PRAGMA journal_mode=WAL;"
  sqlite3 projects/studio_asset_registry.db "PRAGMA busy_timeout=5000;"
  ```

### 1.2 `VideoToolbox Encoding Error (-12908)`
- **Cause:** macOS hardware encoder session limit reached (maximum 4 concurrent hardware sessions on Apple M-series chips).
- **Resolution:**
  The studio worker manager automatically limits active hardware sessions to 2 concurrent jobs. If an external application (e.g. DaVinci Resolve or Final Cut Pro) is monopolizing the hardware ASIC, restart the studio or fall back to CPU encoding:
  `export HARDWARE_ACCELERATION=cpu`

### 1.3 `415 Unsupported Media Type` on Ingestion
- **Cause:** Uploaded file extension does not match its true binary magic bytes (e.g., an HTML error page or shell script renamed to `.mp4`).
- **Resolution:**
  Inspect file headers:
  ```bash
  file --mime-type <PATH_TO_FILE>
  ```
  Provide valid MP4, MOV, MKV, WAV, MP3, PNG, or JPEG files.

### 1.4 Broken Audio / Video Sync on Rendered Master
- **Cause:** Variable Frame Rate (VFR) source material causing timestamp drift.
- **Resolution:**
  Department 03 conforms VFR material to Constant Frame Rate (CFR) during ingestion. Ensure all source media passes through the proxy/conformance pipeline before timeline insertion.

