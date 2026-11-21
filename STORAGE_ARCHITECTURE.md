# Storage Architecture & Partitioning Specification
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 Specification  
**Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Storage Topology & Partitioning

The studio isolates storage by project ID and lifecycle domain. This ensures multi-tenant isolation, clean cache purging, and frictionless migration to cloud object stores (S3 / GCS).

```text
assets/
└── {project_id}/                     # Project root sandbox
    ├── originals/                    # Untouched, preserved source files
    │   └── {asset_id}_{filename}
    ├── derivatives/                  # Heavy generated assets (Proxies, WAVs)
    │   └── {asset_id}/
    │       ├── proxy_prores.mov
    │       └── extracted_audio_48k.wav
    └── previews/                     # Lightweight streaming assets
        └── {asset_id}/
            ├── thumbnail.jpg
            ├── contact_sheet.jpg
            ├── preview_720p.mp4
            └── waveform.json

temp/
└── {project_id}/                     # Temporary processing scratch (auto-cleaned)
    └── {job_id}/

projects/
└── studio_asset_registry.db          # Central SQLite Registry (WAL Mode)
```

---

## 2. Directory Separation & Invariants

1. **Originals Directory (`assets/{project_id}/originals/`):**
   - **Immutable.** Once written, files are never modified, edited in place, or overwritten.
   - Named deterministically as `{asset_id}_{safe_filename}` to guarantee zero namespace collisions even if a user uploads two different files named `clip.mp4`.
2. **Derivatives Directory (`assets/{project_id}/derivatives/{asset_id}/`):**
   - Stores downstream editing proxies and audio extraction files.
   - Disposable: Can be regenerated at any time from the original using stored `generation_params`.
3. **Previews Directory (`assets/{project_id}/previews/{asset_id}/`):**
   - Stores lightweight thumbnails, contact sheets, and streaming web previews.
   - Optimized for fast CDN delivery and browser caching.
4. **Temporary Scratch Directory (`temp/{project_id}/`):**
   - Ephemeral working directory for intermediate transcoding chunks, split streams, and uncompressed PCM buffers.
   - Automatically cleaned after background worker job completion.

---

## 3. Storage Quotas & Host Hardware Awareness

With **41 GB of free disk space** on the host workstation (M4 MacBook Pro):
- **Maximum Local Cache:** Capped at 15.0 GB in `config/storage.yaml`.
- **Cache Eviction Strategy:** Least-Recently-Used (LRU) eviction on proxy video files when project storage exceeds thresholds.
- **Quota Tracking:** `StorageService.get_project_storage_usage(project_id)` calculates total byte footprint on demand.
- **Original Media Protection:** Proxies and previews can be evicted; originals are never deleted unless the user explicitly requests asset deletion.
