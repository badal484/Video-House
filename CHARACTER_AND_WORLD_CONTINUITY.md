# Character & World Continuity Specification
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Department:** 12 Character Production  
**Last Verified:** 2026-11-21  

---

## 1. The Continuity Challenge in AI Video Production

In generative video pipelines, individual shot models generate frames in isolation, resulting in classic continuity failures:
1. **Wardrobe & Appearance Drift:** Characters spontaneously changing shirts, jewelry, or eye color between cuts.
2. **Spatial Direction (180-Degree Rule) Violations:** Camera jumping over the line of action, causing two conversing characters to both look in the same screen direction.
3. **Lighting & Time-of-Day Inconsistencies:** Sunlight changing angles or fluorescent room fixtures turning into warm tungsten candles across sequential shots.
4. **Prop Disappearances:** Held items vanishing from one cut to the next.

---

## 2. World Continuity Architecture & Entity Profiles

Department 12 establishes explicit continuity entities and constraint rules stored in SQLite:

### 2.1 CharacterProfile
Stores immutable physical traits, wardrobe presets, personality traits, and reference image asset IDs.
```python
@dataclass
class CharacterProfile:
    character_id: UUID
    project_id: UUID
    name: str
    age_appearance: str
    gender: str
    physical_description: str
    costume_wardrobe: str
    personality_traits: List[str] = field(default_factory=list)
    reference_asset_ids: List[UUID] = field(default_factory=list)
    voice_profile_id: Optional[str] = None
    continuity_rules: List[str] = field(default_factory=list)
```

### 2.2 EnvironmentProfile
Stores location layout, lighting conditions, continuous time-of-day, and spatial geometry.
```python
@dataclass
class EnvironmentProfile:
    environment_id: UUID
    project_id: UUID
    name: str
    description: str
    location_type: str  # "INTERIOR", "EXTERIOR", "STUDIO", "ABSTRACT"
    lighting_conditions: str
    time_of_day: str
    spatial_layout: str
    reference_asset_ids: List[UUID] = field(default_factory=list)
```

---

## 3. Automated Continuity Auditing (`audit_shot_continuity`)

The `WorldContinuityService` audits planned shots against active continuity rules prior to generation:
- **Wardrobe & Appearance:** Verifies that shots including a character explicitly mandate their registered costume in prompt prompts and continuity requirements.
- **180-Degree Line of Action:** Flags consecutive shots where eye-lines or screen directions cross without motivated camera movement.
- **Lighting Coherence:** Ensures that consecutive shots within the same scene environment do not specify contradictory key light sources.

