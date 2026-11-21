# Delivery Package and Manifest Specification

## 1. Delivery Package Architecture
The `DeliveryPackageManager` structures all approved final media assets, audio stems, subtitle tracks, promotional imagery, and cryptographic manifests into a standardized delivery directory.

## 2. Standard Directory Layout
```
deliveries/{project_id}_{delivery_id}/
├── master/
│   ├── program_master.mov             # Primary ProRes 422 HQ / H.264 Master
│   └── program_master.sha256          # Cryptographic SHA-256 hash
├── stems/
│   ├── audio_dialogue.wav             # Isolated dialogue stem
│   ├── audio_music.wav                # Isolated score stem
│   └── audio_foley.wav                # Isolated sound effects stem
├── subtitles/
│   ├── subtitles_en.vtt               # English WebVTT sidecar
│   ├── subtitles_es.vtt               # Spanish WebVTT sidecar
│   └── subtitles_hi.ass               # Hindi styled karaoke ASS sidecar
├── artwork/
│   ├── thumbnail.jpg                  # 1920x1080 promotional thumbnail
│   └── poster_frame.png               # Key visual poster frame
├── qc/
│   └── technical_qc_report.json       # Complete automated QC audit report
└── delivery_manifest.json             # Root machine-readable delivery manifest
```

## 3. Machine-Readable Delivery Manifest Schema
The root `delivery_manifest.json` documents:
- `delivery_id`: Unique UUID.
- `project_id`: Target project UUID.
- `project_version`: Revision number.
- `render_profile_id`: Profile used for mastering.
- `files`: Array of file records holding filename, path, file_size_bytes, and sha256_checksum.
- `technical_specs`: Resolution, frame rate, video codec, audio sample rate, color primaries, transfer curve.
- `qc_summary`: Overall pass status, total rules evaluated, warnings count.
- `provenance`: Timestamp, studio render engine version, and C2PA metadata link.

