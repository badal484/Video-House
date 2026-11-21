# Desktop vs Web Architecture: Evaluation & Deployment Strategy

## 1. Architectural Trade-Off Analysis

Creative applications require real-time media manipulation, hardware acceleration, low-latency playback, and robust file system access. This document evaluates three deployment form factors:

| Dimension | Web-First (Browser SPA + Local Server) | Tauri (Rust + Webview) | Electron (Chromium + Node.js) |
| :--- | :--- | :--- | :--- |
| **Binary Bundle Size** | **0 MB** (Served via HTTP from local backend) | ~15–30 MB | ~150–250 MB |
| **Memory Footprint** | Extremely low (Shared with browser engine) | Low (~40–80 MB base) | High (~300–600 MB base) |
| **Hardware Video Acceleration** | Full WebGL2 / WebGPU / VideoTag hardware decoding | WebKit / WebView2 hardware acceleration | Full Chromium hardware decoding |
| **Local File System Access** | Via backend REST/WebSocket APIs | Direct Rust filesystem bindings | Direct Node.js filesystem bindings |
| **Distribution & Updates** | Instant (Zero-install; refresh browser) | Native installer (.dmg, .deb, .msi) | Native installer (.dmg, .deb, .exe) |
| **Multi-Monitor Windows** | Multiple browser tabs / detached windows | Native multi-window support | Native multi-window support |
| **Local Workstation Impact** | **Zero disk clutter**; respects 38GB disk limit | Minimal footprint | Significant memory overhead |

---

## 2. Selected Architecture: Web-First Studio Shell with Desktop-Ready Foundations

### Decision Outcome
We implement a **Web-First Single-Page Application (SPA)** served directly by the studio's existing high-performance FastAPI server (`departments/01_studio_application/api.py`).

**Key Architectural Reasons:**
1. **Zero Client Installation Barrier:** Any engineer or creative can immediately access the studio interface at `http://localhost:8000/` or `http://localhost:8000/ui` without installing Node/Electron build toolchains.
2. **Hardware Awareness (Apple M4 MacBook Pro):** Eliminates Electron's massive memory overhead, preserving 100% of the 16GB unified RAM for Apple VideoToolbox hardware encoding, PySceneDetect optical flow, and DSP audio processing.
3. **Decoupled Client-Server Boundary:** The UI communicates exclusively via standard REST endpoints (`/api/v1/*`) and Server-Sent Events / WebSockets. This allows running the backend headless on a high-powered remote GPU server or locally on the laptop with zero frontend code modifications.
4. **Tauri Drop-In Readiness:** Because the UI is built with standard web technologies (HTML5, modern CSS3 tokens, ES6+ modules) and decoupled from Node-specific internals, it can be wrapped into a native lightweight Tauri desktop binary in minutes whenever offline desktop packaging is required.

