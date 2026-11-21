# UI Known Limitations & Future Roadmap

## 1. Current Workstation & Technical Constraints

1. **Apple Silicon M4 Local Workstation Limits:**
   - Unified RAM is 16GB and free disk space is ~38GB. In-process deep learning inference (e.g. Wan2.1 14B video generation or full SAM 2.1 4K video tracking) is intentionally routed to remote GPU workers or mock adapters.
   - The UI displays explicit banners indicating when a feature uses local CPU/VideoToolbox vs remote cloud workers.

2. **WebCodecs Browser Variation:**
   - While modern Chromium and Safari support WebCodecs for hardware decoding, container demuxing (MP4/MOV parsing) remains reliably backed by the Python FFmpeg engine in Department 03. The UI uses HTML5 video proxies (720p H.264) for ultra-fast, smooth playback.

---

## 2. Future Roadmap (Part 16 & Beyond)

1. **Native Desktop Wrapper:** Wrap the current ES6+ web client into a Tauri 2.0 native binary with local menu bar integration.
2. **Multi-Monitor Window Detachment:** Support popping out the Program Monitor or Audio Mixer into secondary physical monitors.
3. **Real-Time Collaborative Multi-User Cursors:** WebSocket presence indicators for team editing sessions.
