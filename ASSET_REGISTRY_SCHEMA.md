# Central Asset Registry Schema Specification
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 Specification  
**Database Engine:** SQLite 3.x  
**File Location:** `projects/studio_asset_registry.db`  

---

## 1. Entity-Relationship Model

```mermaid
erDiagram
    PROJECTS ||--o{ ASSETS : contains
    ASSETS ||--o{ ASSET_ROLES : has
    ASSETS ||--o| TECHNICAL_METADATA : describes
    ASSETS ||--o{ DERIVATIVES : generates
    ASSETS ||--o{ PROCESSING_JOBS : tracks
    ASSETS ||--o{ ASSET_DEPENDENCIES : references

    PROJECTS {
        TEXT project_id PK
        TEXT name
        TEXT created_at
        TEXT updated_at
        TEXT settings_json
    }

    ASSETS {
        TEXT asset_id PK
        TEXT project_id FK
        TEXT original_filename
        TEXT display_name
        TEXT media_type
        TEXT detected_format
        TEXT mime_type
        INTEGER byte_size
        TEXT checksum_sha256
        TEXT storage_path
        TEXT import_timestamp
        TEXT processing_status
        TEXT metadata_status
        TEXT derivative_status
        TEXT error_message
        INTEGER version
        TEXT source_type
        TEXT license_info
    }

    ASSET_ROLES {
        TEXT asset_id PK, FK
        TEXT role PK
    }

    TECHNICAL_METADATA {
        TEXT asset_id PK, FK
        INTEGER width
        INTEGER height
        REAL duration_seconds
        REAL frame_rate
        REAL avg_frame_rate
        INTEGER is_vfr
        TEXT video_codec
        TEXT audio_codec
        TEXT pixel_format
        INTEGER bit_depth
        TEXT aspect_ratio
        TEXT color_primaries
        TEXT color_transfer
        TEXT color_space
        INTEGER is_hdr
        INTEGER rotation
        TEXT timecode
        INTEGER audio_sample_rate
        INTEGER audio_channels
        TEXT audio_channel_layout
        INTEGER stream_count
        INTEGER bitrate_bps
        TEXT raw_probe_json
    }

    DERIVATIVES {
        TEXT derivative_id PK
        TEXT asset_id FK
        TEXT derivative_type
        TEXT storage_path
        INTEGER byte_size
        TEXT mime_type
        TEXT generation_params_json
        TEXT created_at
        TEXT status
    }

    PROCESSING_JOBS {
        TEXT job_id PK
        TEXT asset_id FK
        TEXT job_type
        TEXT status
        INTEGER progress_pct
        INTEGER retry_count
        INTEGER max_retries
        TEXT error_details
        TEXT created_at
        TEXT updated_at
    }
```

---

## 2. Table Definitions

### Table: `projects`
- `project_id` (TEXT, PK): UUIDv4 string.
- `name` (TEXT): Project title.
- `created_at` (TEXT): ISO-8601 UTC timestamp.
- `updated_at` (TEXT): ISO-8601 UTC timestamp.
- `settings_json` (TEXT): Serialized project configurations (frame rate, canvas dimensions, audio rate).

### Table: `assets`
- `asset_id` (TEXT, PK): Unique immutable identifier.
- `project_id` (TEXT, FK): Parent project reference.
- `original_filename` (TEXT): Exact original filename uploaded by user.
- `display_name` (TEXT): User-facing customizable name.
- `media_type` (TEXT): Enumeration: `VIDEO`, `AUDIO`, `IMAGE`, `SUBTITLE`, `ANIMATION`, `THREE_D`, `PRODUCTION_DOCUMENT`, `UNKNOWN`.
- `detected_format` (TEXT): Lowercase container / format identifier (`mp4`, `wav`, `png`, `gltf`, `obj`).
- `mime_type` (TEXT): Canonical MIME type.
- `byte_size` (INTEGER): Exact file size in bytes.
- `checksum_sha256` (TEXT): 64-character hexadecimal SHA-256 hash.
- `storage_path` (TEXT): Relative path to preserved original file.
- `import_timestamp` (TEXT): ISO-8601 UTC timestamp of import.
- `processing_status` (TEXT): `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`.
- `metadata_status` (TEXT): Status of technical stream metadata extraction.
- `derivative_status` (TEXT): Status of proxy/thumbnail generation.
- `error_message` (TEXT, Nullable): Diagnostic error string upon failure.
- `version` (INTEGER): Version number (default 1).
- `source_type` (TEXT): `UPLOAD`, `LOCAL_IMPORT`, `GENERATED`.
- `license_info` (TEXT, Nullable): Commercial licensing notes or attribution strings.

### Table: `asset_roles`
Enables assigning multiple production roles to a single physical asset without file duplication.
- `asset_id` (TEXT, FK): Asset reference.
- `role` (TEXT): `SOURCE_FOOTAGE`, `REFERENCE_VIDEO`, `REFERENCE_AUDIO`, `REFERENCE_IMAGE`, `MUSIC`, `SOUND_EFFECT`, `VOICE_RECORDING`, `GENERATED_VIDEO`, `GENERATED_IMAGE`, `CHARACTER_REFERENCE`, `ANIMATION_ASSET`, `THREE_D_MODEL`, `TEXTURE`, `LUT`, `SUBTITLE`, `SCRIPT`, `PROJECT_DOCUMENT`.

### Table: `technical_metadata`
Detailed stream attributes extracted by FFprobe and specialized parsers.

### Table: `derivatives`
Tracks generated auxiliary files (proxies, thumbnails, contact sheets, extracted WAV stems, waveforms).

### Table: `processing_jobs`
Durable tracking for background workers, progress percentage, and retry attempts.
