# Cross-Department Data Contracts & Canonical Schemas
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Data Architecture Standard  

---

## 1. Prime Data Directives

1. **UUIDv4 Canonical Identifiers:** All core entities (`project_id`, `asset_id`, `timeline_id`, `track_id`, `clip_id`, `job_id`, `session_id`, `report_id`) MUST use lowercase UUIDv4 strings. No department may invent integer IDs or custom string identifiers for shared entities.
2. **Rational Time Arithmetic:** All temporal cuts, durations, keyframes, transitions, and subtitle timecodes MUST use exact rational arithmetic (`RationalTime(value, rate)`) to eliminate floating-point drift across 23.976, 24.0, 25.0, 29.97, and 60.0 FPS.
3. **Decoupled Quad-Representation:**
   - 1D Temporal Cuts: **OpenTimelineIO (OTIO)**
   - 3D Worlds: **OpenUSD**
   - Compositing Operations: **Node DAG (Directed Acyclic Graph)**
   - Vector Graphics: **Motion Canvas AST / SVG DOM**

---

## 2. Shared Canonical Data Schemas

### 2.1 Project Identity & Version Snapshot
```python
class ProjectRecord(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    stage: str = "INGESTION"  # INGESTION, PLANNING, EDITING, VFX_AUDIO, COLOR_QC, DELIVERY
    aspect_ratio: str = "16:9"  # 16:9, 9:16, 2.39:1, 1:1, 4:3
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    color_space: str = "rec709"  # rec709, acescg, dci_p3, srgb
    audio_sample_rate: int = 48000
    created_at: str
    updated_at: str

class ProjectVersionSnapshot(BaseModel):
    version_id: UUID
    project_id: UUID
    version_name: str
    notes: Optional[str] = None
    state_payload: Dict[str, Any]  # Complete serialized project graph
    created_at: str
```

### 2.2 Asset Manifest & Technical Metadata
```python
class AssetRecord(BaseModel):
    asset_id: UUID
    project_id: UUID
    display_name: str
    original_path: str
    media_type: str  # VIDEO, AUDIO, IMAGE, SUBTITLE, DOCUMENT, ARCHIVE
    source_type: str  # USER_UPLOAD, LOCAL_IMPORT, AI_GENERATED, SYNTHETIC
    roles: List[str]  # SOURCE_FOOTAGE, REFERENCE_VIDEO, B_ROLL, VFX_PLATE, SFX, MUSIC, etc.
    sha256_checksum: str
    file_size_bytes: int
    duration_sec: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    license_type: str = "Commercial-Royalty-Free"
```

### 2.3 Editorial Timeline Schema (OpenTimelineIO)
```python
class Clip(BaseModel):
    clip_id: UUID
    asset_id: UUID
    name: str
    source_range: Dict[str, Any]  # {"start_time": {"value": 0, "rate": 24}, "duration": {"value": 120, "rate": 24}}
    timeline_range: Dict[str, Any]
    speed: float = 1.0
    volume_db: float = 0.0
    pan: float = 0.0

class Track(BaseModel):
    track_id: UUID
    name: str
    kind: str  # Video, Audio
    clips: List[Clip] = Field(default_factory=list)

class Timeline(BaseModel):
    timeline_id: UUID
    project_id: UUID
    name: str
    global_start_time: Dict[str, Any]
    duration: Dict[str, Any]
    tracks: List[Track] = Field(default_factory=list)
```

### 2.4 Technical Quality Control Report Schema
```python
class QCDefect(BaseModel):
    defect_id: UUID
    check_type: str  # FILE_INTEGRITY, VIDEO_BLACK_FRAME, VIDEO_FREEZE, AUDIO_LOUDNESS, AV_SYNC, SUBTITLE_CPS
    severity: str    # CRITICAL, ERROR, WARNING, INFO
    rule_name: str
    description: str
    timestamp_sec: Optional[float] = None
    frame_number: Optional[int] = None
    remediation_suggestion: str

class QCReport(BaseModel):
    report_id: UUID
    project_id: UUID
    asset_id: UUID
    policy_name: str  # STREAMING_STANDARD, STRICT_BROADCAST, ARCHIVAL
    passed: bool
    total_issues: int
    critical_count: int
    error_count: int
    warning_count: int
    defects: List[QCDefect]
    metrics: Dict[str, Any]
    inspected_at: str
```

### 2.5 Delivery Package Manifest Schema
```python
class DeliveryManifest(BaseModel):
    package_id: UUID
    project_id: UUID
    render_profile_id: str
    master_file: Dict[str, Any]  # {"path": ..., "sha256": ..., "format": ..., "size_bytes": ...}
    audio_stems: List[Dict[str, Any]]
    subtitles: List[Dict[str, Any]]
    qc_report_id: UUID
    generated_at: str
```

