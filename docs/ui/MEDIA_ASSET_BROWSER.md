# Media Asset Browser Specification: Asset Ingestion & Registry UI

## 1. Functional Scope

The **Media Asset Browser** interfaces with Department 02 (Media Ingestion) and Department 21 (Asset Storage), managing all raw footage, audio stems, graphics, LUTs, and generated derivatives:

### 1. View Modes
- **Visual Grid Mode:** 16:9 thumbnail cards with duration badges, resolution pills, and media type icons.
- **Detailed List Mode:** Tabular view displaying filename, role tags, duration, dimensions, framerate, file size, codec, date imported, and processing status.

### 2. Ingestion Controls
- **File Upload Dropzone:** Drag-and-drop area accepting video (`.mp4`, `.mov`, `.mkv`), audio (`.wav`, `.mp3`), image (`.png`, `.jpg`, `.exr`), and subtitle (`.srt`, `.vtt`) files.
- **Local Path Import Dialog:** Allows importing local media files by absolute path without copying large files twice, preserving workstation storage.
- **Role Assignment:** Tags assets with functional roles (`SOURCE_FOOTAGE`, `REFERENCE_IMAGE`, `VOICEOVER`, `BACKGROUND_MUSIC`, `SFX`, `LUT`, `SUBTITLE`).

### 3. Asset Detail Modal / Flyout
- Displays comprehensive technical metadata extracted by FFprobe (color primaries, transfer characteristics, audio channel layout, VFR status).
- 500-point audio waveform preview.
- SHA-256 cryptographic checksum.
- Action buttons: "Add to Timeline", "Analyze (PySceneDetect)", "Generate Proxy", "Delete Asset".
