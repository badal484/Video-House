# Production Feasibility & Compute Cost Engine
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 07 Production Planning  
**Last Verified:** 2026-11-21  

---

## 1. Hardware Awareness: Apple Silicon M4 Workstation

The primary development and edge workstation is an **Apple MacBook Pro (Apple M4, 16GB Unified RAM, ~41GB free SSD storage)**.

The `ProductionFeasibilityService` strictly enforces hardware tiering rules:
1. **Local Permitted Tasks (Low RAM / Zero Weight Downloads):**
   - Speech transcription (`faster-whisper int8` via CTranslate2 CPU/NEON: ~400MB RAM).
   - Audio DSP mixing & mastering (`Spotify Pedalboard` + SciPy: ~250MB RAM).
   - Video cut boundary detection (`PySceneDetect` + OpenCV: ~300MB RAM).
   - Motion Canvas headless 2D rendering (Node.js: ~800MB RAM).
   - Editorial assembly & OTIO rational time computation (<100MB RAM).
2. **Strictly Prohibited Local Tasks (Dispatched to Cloud / Remote GPU):**
   - **Local Model Weights > 2 GB:** Never downloaded to local disk.
   - Heavy diffusion models (Wan2.1 14B, Kling 1.5, Runway Gen-3, Flux.1 Pro).
   - 4K video dense object tracking & rotoscoping (SAM 2.1 Large).
   - Heavy 3D ray-traced rendering (Blender Cycles GPU).

---

## 2. Compute Cost Range & Uncertainty Modeling

Unlike naive estimators that output a single misleading number, the studio computes **cost ranges with explicit uncertainty intervals**:

$$\text{Total Cost Range} = [\text{Min USD}, \text{Max USD}]$$
- **Known Costs ($C_{\text{known}}$):** LLM creative planning tokens and local compute ($0.01).
- **Variable AI Video Generation:** Estimated between $\$0.035$ and $\$0.055$ per second.
- **Uncertainty Interval:** Accounts for potential user re-rolls, prompt variations, and candidate generation:
$$\text{Uncertainty USD} = \frac{\text{Max USD} - \text{Min USD}}{2}$$

---

## 3. Data Structure (`ProductionFeasibility`)

```python
@dataclass
class ProductionFeasibility:
    feasibility_id: UUID
    project_id: UUID
    overall_feasibility_score: float  # 0.0 to 1.0
    complexity_category: ComplexityCategory
    estimated_cost_range: Dict[str, float] = field(default_factory=lambda: {
        "min_usd": 0.0,
        "max_usd": 0.0,
        "known_cost_usd": 0.0,
        "uncertainty_usd": 0.0
    })
    cloud_dependencies: List[str] = field(default_factory=list)
    local_hardware_feasibility: Dict[str, Any] = field(default_factory=dict)
    technical_risks: List[str] = field(default_factory=list)
    recommended_alternatives: List[str] = field(default_factory=list)
```
