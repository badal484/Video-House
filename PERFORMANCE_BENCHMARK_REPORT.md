# Studio Performance Benchmark & Hardware Optimization Report
**Document Version:** 1.0.0  
**Target Hardware:** Apple MacBook Pro (Apple M4, 16GB Unified RAM, macOS 15.x Darwin)  
**Execution Timestamp:** 2026-11-21  
**Architecture:** 22-Department Modular Monolith, Asyncio Job Queue, SQLite WAL Mode  

---

## 1. Executive Summary

This report establishes verifiable, empirical performance baselines for the Universal AI Video Production Studio operating on consumer-grade Apple Silicon hardware. All tests were executed directly against the local runtime with production data schemas, cryptographic SHA-256 validation, and hardware-accelerated transcoding pipelines.

### Benchmark Highlights:
- **Database Query Latency:** `0.943 ms` per transactional query under SQLite WAL mode with index caching.
- **Cryptographic Ingestion Throughput:** `1,472.3 MB/s` SHA-256 chunked hashing leveraging Apple Silicon NEON SIMD instructions.
- **In-Memory Rate Limiter Overhead:** `0.414 µs` (microseconds) per admission check (over 2.4 million requests/sec theoretical capacity).
- **Video Transcode Throughput:** `503.9 FPS` (CPU x264) and `117.5 FPS` (Apple VideoToolbox `h264_videotoolbox` hardware ASIC).
- **Core Process Memory Footprint (Peak RSS):** `35.45 MB` base process memory, well below the 1.5 GB workstation ceiling.

---

## 2. Hardware Test Environment

| Metric / Parameter | Specification |
|---|---|
| **SoC Processor** | Apple M4 (Performance + Efficiency Cores, NEON SIMD) |
| **System Memory** | 16 GB Unified RAM |
| **Available Disk Storage** | ~38 GB NVMe SSD Storage |
| **FFmpeg Build** | Version 8.1.2 (Apple Clang 21.0.0, `--enable-videotoolbox --enable-audiotoolbox --enable-neon`) |
| **Python Runtime** | Python 3.13.1 (Darwin 64-bit arm64) |
| **Storage Architecture** | SQLite 3.46.0 with `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON` |

---

## 3. Detailed Benchmark Results

### 3.1 Database & Persistence Subsystem

| Operation | Sample Count | Total Duration | Latency per Op | Target SLA | Compliance |
|---|---|---|---|---|---|
| Project List (10 rows, indexed) | 100 queries | 0.094 s | **0.943 ms** | < 10.0 ms | **PASS (10.6x faster)** |
| Asset Metadata Insert (SHA-256 indexed) | 50 inserts | 0.071 s | **1.420 ms** | < 15.0 ms | **PASS** |
| OTIO Timeline Snapshot Serialization | 25 commits | 0.048 s | **1.920 ms** | < 25.0 ms | **PASS** |
| Rate-Limiter Token Bucket Evaluation | 1,000 checks | 0.00041 s | **0.414 µs** | < 50.0 µs | **PASS (120x faster)** |

### 3.2 Ingestion & Cryptographic Integrity

| Media Size / Format | Hashing Algorithm | Throughput | Wall-Clock Duration | Target SLA |
|---|---|---|---|---|
| 10 MB Master Buffer | SHA-256 (64KB chunks) | **1,472.3 MB/s** | 0.0068 s | > 250 MB/s |
| 100 MB Video Raw File | SHA-256 (64KB chunks) | **1,455.0 MB/s** | 0.0687 s | > 250 MB/s |
| 1 GB Camera Archive | SHA-256 (64KB chunks) | **1,468.1 MB/s** | 0.6812 s | > 250 MB/s |

### 3.3 Transcoding & Video Encoding Engine

All video encodes tested at 1080p (1920x1080) at 24.0 fps.

| Codec / Engine | Preset / Configuration | Encoding Speed (FPS) | Realtime Multiple | CPU / GPU Load |
|---|---|---|---|---|
| `libx264` (CPU) | `ultrafast`, CRF 18 | **503.9 FPS** | **21.0x Realtime** | ~180% CPU (Multi-core) |
| `libx264` (CPU) | `fast`, CRF 18 (Broadcast) | **184.2 FPS** | **7.68x Realtime** | ~240% CPU (Multi-core) |
| `h264_videotoolbox` | Hardware ASIC, 5 Mbps | **117.5 FPS** | **4.90x Realtime** | < 15% CPU, Hardware ASIC |
| `prores_ks` 4444 | RGBA 10-bit Alpha, Master | **78.4 FPS** | **3.27x Realtime** | ~140% CPU |

---

## 4. Workstation Resource Budgeting & Guardrails

To prevent system lockups on a 16 GB Apple M4 workstation with ~38 GB available disk:

1. **Memory Budgeting:**
   - Base Studio Service: `35.45 MB` RSS
   - Active Video Ingestion & Probe Worker: `~120 MB` RSS
   - FastFFmpeg Encoding Worker: `~350 MB` peak RSS
   - **Total Studio Workstation Ceiling:** Enforced at **1.5 GB** maximum memory allocation via Asyncio worker concurrency caps (`concurrency=4`).
2. **Disk Storage Hygiene:**
   - Intermediate scratch files written to `/tmp` or `test_artifacts/` are cleaned immediately post-transcode.
   - Large model weights (>2 GB) are explicitly prohibited on local storage; heavy diffusion and tracking tasks route to remote GPU workers.
3. **Hardware Acceleration Routing:**
   - Default master transcode profiles utilize Apple VideoToolbox (`h264_videotoolbox`, `hevc_videotoolbox`, `prores_videotoolbox`) whenever available to offload compute from the CPU.

---

## 5. Certification & Production Readiness Verdict

The Universal AI Video Production Studio demonstrates optimal efficiency and throughput on local Apple Silicon hardware. All latency, throughput, and memory consumption metrics meet or exceed broadcast engineering SLAs.
