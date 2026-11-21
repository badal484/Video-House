# Rendering, Quality Control & Delivery Studio Implementation

## 1. System Mission & Architectural Scope
Part 14 unifies Quality Control (Department 18: `quality_control`) and Rendering & Delivery (Department 19: `rendering_delivery`). It sits downstream of all DCC creative and editorial departments, transforming validated production projects into technically compliant, multi-format master packages.

## 2. Structural Subsystem Architecture
```
departments/18_quality_control/
├── __init__.py
├── interface.py                       # Department contract (IQualityControl)
├── service.py                         # QualityControlService facade
├── core/
│   ├── __init__.py
│   └── models.py                      # Pydantic v2 domain models for QC
├── inspectors/
│   ├── __init__.py
│   ├── file_integrity.py              # MediaInfo / stream / container validator
│   ├── video_validator.py             # Black, frozen, flash frames, VFR, resolution
│   ├── audio_validator.py             # EBU R128 loudness, true-peak, clipping, sync
│   ├── color_validator.py             # Gamut, transfer curves, MaxCLL/MaxFALL
│   └── subtitle_validator.py          # CPS reading speed, CPL, overlap, timing
├── metrics/
│   ├── __init__.py
│   └── visual_metrics.py              # VMAF, PSNR, SSIM evaluation
└── rules/
    ├── __init__.py
    └── qc_policy_engine.py            # Rule engine with INFO/WARNING/ERROR/CRITICAL

departments/19_rendering_delivery/
├── __init__.py
├── interface.py                       # Department contract (IRenderingDelivery)
├── service.py                         # RenderingDeliveryService facade
├── core/
│   ├── __init__.py
│   └── models.py                      # RenderPlan, RenderJob, DeliveryPackage models
├── compiler/
│   ├── __init__.py
│   ├── preflight.py                   # Pre-render asset, font, LUT, plugin inspector
│   ├── render_plan_compiler.py        # Compiles project timeline into execution DAG
│   └── dependency_graph.py            # Stage dependency resolver
├── profiles/
│   ├── __init__.py
│   └── profile_registry.py            # Master, social, broadcast, archival profiles
├── queue/
│   ├── __init__.py
│   ├── render_queue_manager.py        # Asynchronous priority queue
│   └── recovery_manager.py            # Checkpoints, retry, and crash recovery
├── workers/
│   ├── __init__.py
│   ├── worker_manager.py              # Worker registration & capability matcher
│   ├── local_worker.py                # Local CPU / VideoToolbox worker
│   └── remote_worker.py               # Distributed cloud worker client
├── encoding/
│   ├── __init__.py
│   ├── encoding_engine.py             # FFmpeg & VideoToolbox multi-pass encoder
│   └── timeline_adapter.py            # Part 05 OTIO intermediate frame rasterizer
├── delivery/
│   ├── __init__.py
│   ├── package_manager.py             # Multi-stream & sidecar packager
│   ├── manifest_generator.py          # Machine-readable delivery_manifest.json
│   └── cost_manager.py                # Compute time, cloud cost, budget ceiling
└── integrations/
    ├── __init__.py
    ├── timeline_render_bridge.py      # Part 05 OpenTimelineIO bridge
    ├── dcc_render_bridge.py           # Parts 06-13 DCC render dispatch bridge
    └── asset_store_bridge.py          # Part 21 Common Asset Registry persistence
```

## 3. Department Interactions & Data Flow
1. **Compilation & Preflight:** The creative project is inspected by `PreflightValidator`. Offline media, missing LUTs, fonts, or unsupported operations throw blocking errors before rendering begins.
2. **DAG Compilation:** `RenderPlanCompiler` generates a deterministic execution graph ordering DCC renders, timeline intermediate rasterization, audio mastering, and target encoding.
3. **Queue & Worker Dispatch:** Jobs are dispatched to `LocalRenderWorker` (VideoToolbox hardware acceleration) or `RemoteRenderWorker`.
4. **Encoding & Transcoding:** Validated intermediate frames are encoded into target container formats according to the active `RenderProfile`.
5. **Quality Control Gate:** The rendered media is inspected by `QualityControlService`. If critical rules fail (e.g. resolution mismatch, loud clipping), the job is flagged `QC_FAILED` and delivery is halted.
6. **Delivery Packaging:** Passing renders are packaged with subtitle sidecars, audio stems, thumbnails, SHA-256 checksums, and signed manifests.

