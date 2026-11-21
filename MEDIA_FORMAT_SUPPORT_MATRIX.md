# Media Format Support & Capabilities Matrix
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 Specification  
**Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Classification Levels

Media formats ingested into the studio are categorized into distinct operational support tiers:
- **`Importable`**: Accepted by file validator and preserved safely in original storage.
- **`Metadata Extracted`**: Container, stream, and codec properties extracted via FFprobe or native parsers.
- **`Preview Generated`**: Automated thumbnail, contact sheet, or browser-compatible stream synthesized.
- **`Downstream Supported`**: Fully usable in editorial timelines (OTIO), audio DSP (Pedalboard), or 3D engines (Blender/USD).
- **`External Reference Only`**: Preserved as a reference asset; downstream processing requires manual or external handling.

---

## 2. Complete Format Support Table

| Category | Format / Extension | Magic Signature / Detection Method | Importable | Metadata Extracted | Preview Generated | Downstream Supported | Operational Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Video** | **MP4** (`.mp4`) | `ftyp` (isom, mp42) | YES | YES | YES | YES | Primary web and preview video format. |
| **Video** | **QuickTime** (`.mov`) | `ftypqt  ` or MOOV atom | YES | YES | YES | YES | Industry standard for Apple ProRes & VFX overlays. |
| **Video** | **Matroska** (`.mkv`) | EBML `\x1a\x45\xdf\xa3` | YES | YES | YES | YES | Multi-track audio and soft subtitles supported. |
| **Video** | **WebM** (`.webm`) | EBML with `webm` docType | YES | YES | YES | YES | VP8, VP9, and AV1 video with Opus audio. |
| **Video** | **AVI** (`.avi`) | `RIFF....AVI ` | YES | YES | YES | YES | Legacy video container. |
| **Video** | **MPEG-TS** (`.ts`) | Sync byte `0x47` @ 188B | YES | YES | YES | YES | Broadcast transport streams. |
| **Video** | **MXF** (`.mxf`) | SMPTE 377M KLV Header | YES | YES | Optional | YES | Avid and broadcast master standard. |
| **Audio** | **WAV** (`.wav`) | `RIFF....WAVE` | YES | YES | YES | YES | Broadcast WAV (24-bit 48kHz PCM). Waveform extracted. |
| **Audio** | **FLAC** (`.flac`) | `fLaC` | YES | YES | YES | YES | Lossless compressed audio. Waveform extracted. |
| **Audio** | **MP3** (`.mp3`) | `ID3` or MPEG frame sync | YES | YES | YES | YES | Standard compressed audio. Preview normalized. |
| **Audio** | **AAC / M4A** (`.m4a`) | ADTS sync or `ftypM4A ` | YES | YES | YES | YES | Streaming audio format. |
| **Audio** | **OGG Vorbis** (`.ogg`) | `OggS` | YES | YES | YES | YES | Open container audio. |
| **Audio** | **AIFF** (`.aiff`, `.aif`) | `FORM....AIFF` | YES | YES | YES | YES | Apple uncompressed PCM audio. |
| **Image** | **PNG** (`.png`) | `\x89PNG\r\n\x1a\n` | YES | YES | YES | YES | Lossless graphics with full alpha transparency. |
| **Image** | **JPEG** (`.jpg`, `.jpeg`) | `\xff\xd8\xff` | YES | YES | YES | YES | Standard photography and plates. |
| **Image** | **WebP** (`.webp`) | `RIFF....WEBP` | YES | YES | YES | YES | Efficient modern image format with alpha. |
| **Image** | **TIFF** (`.tif`, `.tiff`) | `II*\x00` or `MM\x00*` | YES | YES | YES | YES | High-bit-depth print and scan images. |
| **Image** | **OpenEXR** (`.exr`) | `\x76\x2f\x31\x01` | YES | YES | Tone-mapped | YES | 16/32-bit floating point multi-channel VFX plates. |
| **Image** | **SVG** (`.svg`) | XML text with `<svg` | YES | YES | YES | YES | Scalable 2D vector graphic. |
| **Subtitles** | **SubRip** (`.srt`) | Numeric cue + timecode `-->` | YES | YES | Cue List | YES | Universal subtitle format. |
| **Subtitles** | **WebVTT** (`.vtt`) | `WEBVTT` header | YES | YES | Cue List | YES | HTML5 web video subtitles. |
| **Subtitles** | **ASS / SSA** (`.ass`) | `[Script Info]` section | YES | YES | Cue List | YES | Advanced styled typography subtitles. |
| **Animation** | **Lottie** (`.json`) | JSON with `v`, `fr`, `ip`, `op` | YES | YES | Canvas AST | YES | Vector motion graphics (Motion Canvas compatible). |
| **Animation** | **Rive** (`.riv`) | `RIVE` header | YES | Minimal | No | Reference | Proprietary vector runtime format. |
| **3D Asset** | **Wavefront OBJ** (`.obj`) | Text with `v `, `f ` lines | YES | YES | No | YES | Classical polygon mesh. Ingests vertices & faces. |
| **3D Asset** | **glTF / GLB** (`.gltf`, `.glb`) | `glTF` binary or JSON asset | YES | YES | No | YES | Universal 3D scene & mesh standard. |
| **3D Asset** | **Blender** (`.blend`) | `BLENDER` header | YES | YES | No | YES | Native Blender 3D scene file. |
| **3D Asset** | **OpenUSD** (`.usd`, `.usdc`) | `PXR-USDC` or `#usda` | YES | YES | No | YES | Universal Scene Description format. |
| **3D Asset** | **FBX** (`.fbx`) | `Kaydara FBX Binary` | YES | YES | No | YES | Autodesk DCC exchange format. |
| **Production** | **Color LUT** (`.cube`) | `LUT_3D_SIZE` or `TITLE` | YES | YES | No | YES | 3D Color grading lookup table. |
| **Production** | **Typography Font** (`.otf`, `.ttf`) | `OTTO` or `\x00\x01\x00\x00` | YES | Minimal | No | YES | Font files for Motion Canvas & subtitles. |

