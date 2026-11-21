# Creative Brief Specification & Data Schema
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 06 Creative Direction  
**Last Verified:** 2026-11-21  

---

## 1. Overview

The `CreativeBrief` is the canonical contract defining the artistic intent, audience expectations, technical constraints, and production scope for any studio project. It translates ambiguous user prompts into machine-actionable parameters.

---

## 2. Canonical Data Model (`CreativeBrief`)

```python
@dataclass
class CreativeBrief:
    brief_id: UUID
    project_id: UUID
    # Project Identity
    project_name: str
    production_type: ProductionType     # COMMERCIAL, SHORT_FILM, ANIME, etc.
    genre: str                          # e.g. "Automotive & Luxury", "Sci-Fi"
    target_duration_sec: float          # In seconds (e.g. 15.0, 30.0, 60.0)
    intended_platform: str              # e.g. "Broadcast / Cinema", "YouTube", "TikTok"
    aspect_ratio: str = "16:9"          # "16:9", "9:16", "1:1", "2.39:1"
    resolution: str = "1920x1080"       # "1920x1080", "3840x2160", "1080x1920"
    fps: float = 24.0                   # 24.0, 25.0, 30.0, 60.0
    language: str = "en"
    target_audience: str = "General audience"
    
    # Creative Intent & Objectives
    purpose: str = ""
    core_message: str = ""
    desired_audience_response: str = ""
    call_to_action: Optional[str] = None
    emotional_objective: str = ""
    narrative_objective: str = ""
    
    # Aesthetic & Stylistic Parameters
    visual_style: str = "Cinematic Realism"
    cinematography: str = "Smooth dynamic camera moves"
    lighting_style: str = "High contrast dramatic lighting"
    color_palette: List[str] = field(default_factory=lambda: ["#000000", "#FFFFFF", "#1E3A8A", "#D97706"])
    pacing_style: PacingStyle = PacingStyle.DYNAMIC_BALANCED
    typography_style: str = "Clean modern sans-serif"
    sound_design_notes: str = "Punchy impact sound design with deep sub-bass hits"
    music_direction: str = "Driving cinematic electronic orchestral"
    
    # Constraints & Metadata
    available_footage_ids: List[UUID] = field(default_factory=list)
    reference_asset_ids: List[UUID] = field(default_factory=list)
    budget_tier: str = "STANDARD"
    model_restrictions: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    version: int = 1
```

---

## 3. Relational Database Schema (`creative_briefs`)

```sql
CREATE TABLE IF NOT EXISTS creative_briefs (
    brief_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    production_type TEXT NOT NULL,
    genre TEXT NOT NULL,
    target_duration_sec REAL NOT NULL,
    intended_platform TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL,
    resolution TEXT NOT NULL,
    fps REAL NOT NULL,
    language TEXT NOT NULL,
    target_audience TEXT,
    purpose TEXT,
    core_message TEXT,
    desired_audience_response TEXT,
    call_to_action TEXT,
    emotional_objective TEXT,
    narrative_objective TEXT,
    visual_style TEXT,
    cinematography TEXT,
    lighting_style TEXT,
    color_palette TEXT, -- JSON array of hex codes
    pacing_style TEXT,
    typography_style TEXT,
    sound_design_notes TEXT,
    music_direction TEXT,
    available_footage_ids TEXT, -- JSON array of UUIDs
    reference_asset_ids TEXT,   -- JSON array of UUIDs
    budget_tier TEXT,
    model_restrictions TEXT,   -- JSON array
    exclusions TEXT,           -- JSON array
    assumptions TEXT,          -- JSON array
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
```

---

## 4. Assumption Logging & Clarification Policy

When an incoming brief lacks crucial creative or technical parameters:
1. **Target Duration:** If unspecified, defaults to 30.0s and logs: `"Target duration defaulted to 30.0 seconds."`
2. **Platform & Aspect Ratio:** If mentioning mobile/TikTok, defaults to 9:16 vertical; otherwise defaults to 16:9 landscape.
3. **Clarification Trigger:** If the input prompt contains fewer than 10 words or lacks key constraints, the service automatically flags clarification questions to prompt the human director before committing resources.

