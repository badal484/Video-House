# Generation Request & Job Schema Specification
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** GENERATION_REQUEST_SCHEMA.md  
**Version:** 1.0.0  

---

## 1. Generation Request Schema (`GenerationRequest`)

```python
class GenerationRequest(BaseModel):
    request_id: UUID
    project_id: UUID
    scene_id: Optional[str]
    shot_id: Optional[str]
    modality: GenerationModality  # TEXT_TO_VIDEO, IMAGE_TO_VIDEO, etc.
    preferred_provider: Optional[str]
    preferred_model: Optional[str]
    raw_prompt: str
    compiled_prompt: Optional[str]
    negative_prompt: Optional[str]
    reference_assets: List[ReferenceAssetBinding]
    character_id: Optional[UUID]
    resolution: Tuple[int, int] = (1920, 1080)
    aspect_ratio: str = "16:9"
    duration_sec: float = 5.0
    fps: float = 24.0
    seed: Optional[int]
    camera_motion: Optional[Dict[str, Any]]
    estimated_cost_usd: float = 0.0
    idempotency_key: str
```

---

## 2. Job Lifecycle States

```
[DRAFT] ──> [VALIDATING] ──> [QUEUED] ──> [SUBMITTED] ──> [RUNNING] ──> [SUCCEEDED]
                 │              │              │              │
                 ▼              ▼              ▼              ▼
              [BLOCKED]    [CANCELLED]      [FAILED]      [EXPIRED]
```

- **DRAFT**: Request configured by user or AI Director.
- **VALIDATING**: Checking budget limits, external upload authorization, and reference assets.
- **QUEUED**: Enqueued in the internal non-blocking asynchronous worker queue.
- **SUBMITTED**: Accepted by external provider API; tracking ticket received.
- **RUNNING**: Provider currently synthesizing media latents.
- **SUCCEEDED**: Media downloaded, validated for quality control, and registered in asset store.
- **FAILED**: Generation failed; auto-retry scheduled if transient network error.
- **BLOCKED**: Budget exceeded or human approval required.
