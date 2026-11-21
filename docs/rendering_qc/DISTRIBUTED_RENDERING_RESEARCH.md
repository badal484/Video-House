# Distributed Rendering & Render Farm Architecture Research

## 1. Distributed Rendering Challenges in Media Production
Large-scale video rendering exhibits distinct scaling characteristics compared to standard stateless web workloads:
- **Large Asset Footprints:** Video raw footage, 3D OpenUSD geometry, and high-resolution textures exceed gigabytes of data; transmitting assets over the network can take longer than the render itself.
- **Temporal Context Dependencies:** Unlike ray tracing where each frame is completely independent, video encoding (motion estimation GOPs), video stabilization, temporal denoising, and fluid simulations require temporal window context.
- **Worker Heterogeneity:** Some workers have high-end CUDA GPUs for neural lip-sync and diffusion, some have Apple Silicon Media Engines for VideoToolbox ProRes, and some are CPU-only nodes.

## 2. Render Farm Orchestration Systems Evaluated

| Orchestrator | Architecture | Scheduling Paradigm | Asset Staging | Fault Tolerance & Checkpoints | License | Studio Fit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AWS Deadline Cloud / OpenJD** | Cloud-native + On-premises worker agent | Task-graph DAGs with Open Job Description (OpenJD) | Shared NFS / S3 bucket sync | Heartbeat polling, automatic task retries, timeout reaping | Apache 2.0 (OpenJD specification) | **Selected Reference Model for Studio Architecture** |
| **Blender Flamenco 3** | Lightweight central manager + workers | Simple sequential chunking | Shared filesystem (SMB/NFS) | Basic worker reconnect | GPL-3.0 (Isolated subprocess) | Good for small Blender render farms; lacks deep NLE support |
| **Kubernetes (K8s) Jobs** | Containerized pod scheduling | Batch Job controller | PVC (Persistent Volume Claims) | Pod restarts, container backoff | Apache 2.0 | High infrastructure overhead; suitable for enterprise cloud deployments |
| **Local Asynchronous Worker Queue** | Python asyncio + SQLite job persistence | Priority queue with worker affinity | Local zero-copy filesystem | In-process state machine with safe checkpoints | Apache 2.0 (Studio Core) | **Selected Primary Engine for Standalone Workstation** |

## 3. Task Chunking Strategies
To prevent temporal rendering artifacts, the `RenderPlanCompiler` decomposes projects into three types of tasks:
1. **Scene / Shot Tasks:** Natural boundaries defined by editorial cut points (PySceneDetect / Part 04). Completely independent, zero temporal bleeding.
2. **Image Sequence Frame Ranges:** Linear chunks (e.g., frames 0–99, 100–199) strictly for intra-frame operations (3D Cycles rendering, 2D vector animation).
3. **Sequential Stitch & Encode Tasks:** Ingests rendered shot intermediates and performs single-pass conform and multi-track audio multiplexing.

## 4. Cost Management & Compute Sizing
- Cloud GPU rendering carries substantial hourly egress and compute costs.
- The studio enforces a strict **Preflight Cost Gate**: Any job requiring remote cloud workers or estimated to exceed $\$1.00$ triggers a mandatory `HumanApprovalGate` before dispatching compute tasks.
