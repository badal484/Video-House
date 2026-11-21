# Lip-Synchronization Architecture Specification

## 1. System Pipeline Overview
The `LipSyncOrchestrator` replaces the mouth and lower-facial geometry of an on-screen speaker to synchronize with a target audio track.

```
Original Video Frame ──► [Face Detector] ──► [Lower Face Crop ROI]
                                                     │
Target Audio Chunk ─────► [Audio Encoder] ───────────┤
                                                     ▼
                                            [Diffusion / GAN Sync]
                                            (Sync Labs / MuseTalk)
                                                     │
                                                     ▼
                                            [Restored Lip Patch]
                                                     │
                                                     ▼
                                            [Poisson Seamless Blend]
                                                     │
                                                     ▼
                                            [Synchronized Frame]
```

## 2. Multi-Tier Provider Router
1. **Commercial Cloud Tier:** `SyncLabsAdapter`
   - Submits original video asset URL and dubbed target audio stem to the Sync Labs API.
   - Polls job status with backoff; retrieves 1080p/4K synced video asset.
2. **Local / Remote Worker Tier:** `LocalLipSyncAdapter`
   - Interfaces with MuseTalk or LatentSync inference servers.
   - Performs face landmark detection (MediaPipe/RetinaFace), crops lower 35% bounding region around mouth coordinates.
   - Generates synced inpainting patch, applies bilateral filtering, and blends back onto full-frame canvas.
3. **Licensing Isolation Guard:**
   - Evaluates provider configurations before execution.
   - Rejects non-commercial checkpoints (e.g. Wav2Lip) to uphold Studio Prime Directive #6.
