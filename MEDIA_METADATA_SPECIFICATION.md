# Technical Media Metadata Specification
**Project:** Universal AI Video Production Studio  
**Phase:** Part 02 Specification  
**Version:** 1.0.0  
**Verification Date:** 2026-11-21  

---

## 1. Scope & Design Philosophy

Professional media editing requires precise understanding of video timing, color encodings, audio configurations, and container idiosyncrasies. Reducing video to merely `width x height` leads to frame-rate judder, audio sync drift, and color grading degradation.

The Universal AI Video Production Studio captures **24 distinct technical dimensions** across video, audio, image, and 3D assets.

---

## 2. Video Technical Properties

| Parameter | Type | Source | Definition & Architectural Significance |
| :--- | :---: | :--- | :--- |
| `width`, `height` | `int` | Video Stream | Pixel canvas dimensions of the decoded frame. |
| `duration_seconds` | `float` | Container / Stream | Exact floating-point duration. Checked against audio duration for drift. |
| `frame_rate` | `float` | `r_frame_rate` | Nominal stream frame rate (e.g. `24.0`, `23.976`, `29.97`, `59.94`, `60.0`). |
| `avg_frame_rate` | `float` | `avg_frame_rate` | Mathematical average frame rate over total frame count and duration. |
| `is_vfr` | `bool` | Calculated | Flag set to `True` if `abs(frame_rate - avg_frame_rate) > 0.05`. Variable Frame Rate footage must be conformed before timeline editing. |
| `video_codec` | `str` | `codec_name` | Underlying video compression standard (e.g. `h264`, `hevc`, `prores`, `dnxhr`, `vp9`, `av1`). |
| `pixel_format` | `str` | `pix_fmt` | Chroma subsampling and memory packing (e.g. `yuv420p`, `yuv422p10le`, `yuv444p12le`, `rgb24`). |
| `bit_depth` | `int` | `bits_per_raw_sample` | Color bit depth per channel (8-bit SDR, 10-bit HDR/ProRes, 12-bit Master). |
| `aspect_ratio` | `str` | `DAR` / GCD | Display aspect ratio (e.g. `16:9`, `9:16`, `2.39:1`). |
| `color_primaries` | `str` | Video Stream | Color gamut primaries (e.g. `bt709`, `bt2020`, `smpte432` / DCI-P3). |
| `color_transfer` | `str` | Video Stream | Opto-Electronic Transfer Function (e.g. `bt709`, `smpte2084` / PQ, `arib-std-b67` / HLG, `linear`). |
| `color_space` | `str` | Video Stream | Matrix coefficients (e.g. `bt709`, `bt2020nc`). |
| `is_hdr` | `bool` | Calculated | Flag set to `True` if transfer is PQ/HLG or primaries are BT.2020. Protects against accidental tonemapping loss. |
| `rotation` | `int` | Side Data / Tags | Orientation metadata (0, 90, 180, 270) commonly present in smartphone portrait videos. |
| `timecode` | `str` | Stream / Format Tags | SMPTE drop-frame or non-drop-frame start timecode (e.g. `01:00:00:00`). |
| `bitrate_bps` | `int` | Format | Data transmission rate in bits per second. |

---

## 3. Audio Technical Properties

| Parameter | Type | Source | Definition & Architectural Significance |
| :--- | :---: | :--- | :--- |
| `audio_codec` | `str` | `codec_name` | Audio compression (e.g. `pcm_s16le`, `pcm_s24le`, `aac`, `flac`, `mp3`, `opus`). |
| `audio_sample_rate` | `int` | Audio Stream | Sampling frequency (e.g. `48000` Hz for video broadcast, `44100` Hz for CD/music). |
| `audio_channels` | `int` | Audio Stream | Number of discrete audio tracks (1=Mono, 2=Stereo, 6=5.1 Surround, 8=7.1). |
| `audio_channel_layout` | `str` | Audio Stream | Channel speaker allocation (`stereo`, `5.1(side)`, `quad`). |

---

## 4. Image, 3D & Animation Properties

- **Image Assets:** Canvas dimensions (`width`, `height`), color mode (`RGB`, `RGBA`, `CMYK`, `L`), alpha channel flag (`has_alpha`), and animated frame count (`stream_count` for multi-frame GIF/WebP).
- **3D Assets:**
  - Wavefront OBJ: Vertex count (`v_count`), face count (`f_count`).
  - glTF / GLB: Scene count, node count, mesh count, and material count parsed from glTF JSON header.
- **Animation Assets (Lottie):**
  - Dimensions (`w`, `h`), frame rate (`fr`), in-point (`ip`), out-point (`op`), total animation duration in seconds, layer count.
- **Subtitle Assets:**
  - Format (`SRT`, `VTT`, `ASS`), total dialogue cue count, start timecode of first line, end timecode of last line.

