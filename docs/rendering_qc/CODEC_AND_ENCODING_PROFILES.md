# Codec and Encoding Profiles Specification

## 1. Configurable Render Profile Architecture
Delivery requirements vary radically depending on the destination (theatrical, streaming, social media, or archival). The `RenderProfileRegistry` provides versioned, strongly-typed profiles.

## 2. Core Profile Schema Parameters
Every `RenderProfile` specifies:
- `profile_id`: String identifier (e.g. `prores_422_hq_master`, `youtube_1080p_standard`).
- `name`: Human-readable title.
- `target_use`: Category (`MASTER`, `SOCIAL`, `BROADCAST`, `ARCHIVAL`, `PREVIEW`).
- `container`: Container extension (`mov`, `mp4`, `mkv`, `mxf`).
- `video_codec`: Video encoder codec (`prores_ks`, `h264`, `hevc`, `av1`, `ffv1`).
- `width` / `height`: Resolution dimensions (e.g. $1920\times1080$, $3840\times2160$, $1080\times1920$).
- `frame_rate`: Target rational fps (e.g. 24.0, 25.0, 29.97, 60.0).
- `pixel_format`: Chroma and bit depth (e.g. `yuv422p10le`, `yuv420p`, `yuva444p10le`).
- `bitrate_kbps`: Target video bitrate or None for CRF/lossless.
- `color_space`: NCLX color metadata (`bt709`, `bt2020nc`, `display_p3`).
- `transfer_characteristic`: EOTF curve (`bt709`, `smpte2084`, `arib-std-b67`).
- `audio_codec`: Audio compression codec (`pcm_s24le`, `aac`, `opus`).
- `audio_sample_rate`: Audio sampling frequency (48,000 Hz broadcast standard).
- `audio_channels`: Channel layout (Stereo, 5.1 Surround, Multitrack Stems).
- `target_loudness_lufs`: Target integrated loudness (-23.0 LUFS for broadcast, -14.0 for social).
- `max_true_peak_db`: Maximum true peak ceiling (-1.0 dBTP).
- `faststart`: Relocates MP4 `moov` atom to head of file.
- `qc_policy_id`: Identifier of the QC policy applied.

