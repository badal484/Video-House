# Local and Distributed Rendering Specification

## 1. Multi-Tier Worker Architecture
The studio runtime manages a hybrid compute pool combining local workstation acceleration with remote worker nodes:

1. **Local Render Worker (`LocalRenderWorker`):**
   - Direct in-process or local subprocess execution.
   - Hardware-accelerated encoding via Apple Silicon VideoToolbox (`h264_videotoolbox`, `hevc_videotoolbox`, `prores_videotoolbox`).
   - Zero network transmission latency; operates directly on local storage.
2. **Remote Render Worker (`RemoteRenderWorker`):**
   - Dispatches tasks to remote GPU clusters or cloud instances via secure REST/gRPC.
   - Manages asset synchronization (staging raw footage and textures to worker scratch storage).
   - Polls task status with exponential backoff and retrieves rendered image sequences.
3. **Worker Manager (`WorkerManager`):**
   - Tracks worker health via periodic heartbeats (30-second interval).
   - Routes tasks based on hardware capabilities (e.g. routing CUDA diffusion lip-sync tasks to remote GPU workers, while keeping ProRes timeline conforming local).

## 2. Distributed Task Splitting Rules
To preserve temporal integrity, tasks are partitioned strictly according to the operation type:
- **Intra-Frame Splitting (Allowed):** 3D Cycles renders, 2D vector drawing rasterization, and static background generation are chunked into contiguous frame spans (e.g. frames 0–49, 50–99).
- **Temporal Context Splitting (Protected):** Temporal motion estimation, video stabilization, frame rate interpolation (RIFE), and inter-frame video encoding are never split at arbitrary frames. They are chunked strictly at scene cut boundaries.
