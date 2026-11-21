# Generation Provider Architecture & Capability Registry
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** GENERATION_PROVIDER_ARCHITECTURE.md  
**Version:** 1.0.0  

---

## 1. Provider Independence & Abstraction Layer

The Universal AI Video Production Studio does not hardcode any third-party AI provider into business logic. Instead, Department 15 implements an extensible, plugin-based provider architecture where each model adapter derives from `BaseGenerationProvider`:

```
                    ┌─────────────────────────────────────────┐
                    │        GenerationRequestRouter          │
                    └────────────────────┬────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌───────────────┐                ┌───────────────┐                ┌───────────────┐
│ RunwayAdapter │                │ KlingAdapter  │                │ FluxAdapter   │
│ - T2V, I2V    │                │ - T2V, I2V    │                │ - T2I, I2I    │
│ - 1080p       │                │ - MotionBrush │                │ - Inpainting  │
└───────┬───────┘                └───────┬───────┘                └───────┬───────┘
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │          Asynchronous Job Queue         │
                    │       - Polling, Retries, Backoff       │
                    │       - Non-blocking Execution          │
                    └─────────────────────────────────────────┘
```

---

## 2. Common Capability Declarations

Every registered provider declares its supported capabilities using a bitwise or set-based schema:
- `text_to_video`
- `image_to_video`
- `video_to_video`
- `reference_to_video`
- `first_last_frame_video`
- `text_to_image`
- `image_to_image`
- `inpainting`
- `outpainting`
- `text_to_speech`
- `text_to_music`
- `text_to_sound`
- `text_to_3d`
- `image_to_3d`

Constraints such as maximum duration, supported aspect ratios (`16:9`, `9:16`, `1:1`, `2.39:1`), native resolutions (`720p`, `1080p`, `4K`), and rate limits are registered in `ProviderSpec`.
