# Service Dependency Graph & Failure Domains
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved System Architecture Baseline  

---

## 1. Directed Acyclic Service Dependency Graph

The 22 departments form a strict Directed Acyclic Graph (DAG) with zero circular dependencies. 

```mermaid
graph TD
    subgraph Tier0["Tier 0: Foundational Storage & Project Registry"]
        D21["Dept 21: Storage & Asset Registry"]
        D02["Dept 02: Project Management"]
        D22["Dept 22: Licensing & Cost Tracking"]
    end

    subgraph Tier1["Tier 1: Media Intake & Understanding"]
        D03["Dept 03: Media Ingestion"]
        D04["Dept 04: Media Intelligence"]
        D05["Dept 05: Multimodal Providers"]
    end

    subgraph Tier2["Tier 2: Creative Direction & Planning"]
        D06["Dept 06: Creative Direction"]
        D07["Dept 07: Production Planning"]
        D12["Dept 12: Character & World Continuity"]
        D20["Dept 20: Agent Orchestration"]
    end

    subgraph Tier3["Tier 3: Specialized Content Production"]
        D08["Dept 08: Video Editing (OTIO)"]
        D09["Dept 09: Motion Graphics"]
        D10["Dept 10: 2D Animation"]
        D11["Dept 11: 3D Animation"]
        D13["Dept 13: VFX Compositing"]
        D14["Dept 14: Audio Production"]
        D15["Dept 15: AI Generative Router"]
    end

    subgraph Tier4["Tier 4: Finishing, Quality Control & Packaging"]
        D16["Dept 16: Color & Restoration"]
        D17["Dept 17: Subtitles & Dubbing"]
        D18["Dept 18: Quality Control"]
        D19["Dept 19: Rendering & Delivery"]
    end

    subgraph Tier5["Tier 5: Presentation & Client Gateway"]
        D01["Dept 01: Studio Application (SPA Gateway)"]
    end

    %% Dependencies
    D02 --> D21
    D03 --> D21
    D03 --> D02
    D04 --> D03
    D04 --> D05
    D06 --> D04
    D06 --> D02
    D07 --> D06
    D07 --> D12
    D08 --> D07
    D08 --> D03
    D09 --> D07
    D10 --> D07
    D10 --> D12
    D11 --> D07
    D13 --> D07
    D13 --> D08
    D14 --> D07
    D15 --> D07
    D15 --> D12
    D16 --> D08
    D17 --> D08
    D17 --> D04
    D18 --> D19
    D19 --> D08
    D19 --> D14
    D19 --> D16
    D19 --> D17
    D19 --> D22
    D01 --> D02
    D01 --> D03
    D01 --> D08
    D01 --> D19
    D20 --> D06
    D20 --> D07
    D20 --> D19
```

---

## 2. Failure Domain Isolation & Graceful Degradation

| Department Failure | Blast Radius | System Impact | Graceful Degradation Strategy |
| :--- | :--- | :--- | :--- |
| **Dept 03: Ingestion Worker Crash** | Single asset transcode failure | Asset marked `FAILED`; API unblocked | Automatic retry with exponential backoff; original file intact. |
| **Dept 04: Whisper / PySceneDetect Failure** | Automatic metadata extraction fails | Shot boundaries & transcript missing | Manual cut markers & manual text transcript input enabled in UI. |
| **Dept 05: Multimodal Provider Outage** | External LLM analysis unavailable | Brief analysis hangs | Local deterministic rule fallback generates structured script stub. |
| **Dept 09: Motion Canvas Render Failure** | Motion graphic layer render error | Transparent title missing | Fallback to deterministic SVG text overlay on timeline V2 track. |
| **Dept 14: Audio DSP / Demucs Error** | Audio stem extraction fails | Stems unavailable | Fallback to original stereo mix with baseline -14 LUFS gain adjustment. |
| **Dept 15: AI Video Generation Timeout** | Cloud diffusion job times out | Generative shot missing | Production planner flags missing coverage; prompts manual replacement. |
| **Dept 18: Quality Control Policy Alert** | Broadcast compliance defect detected | Delivery package blocked | Detailed defect report returned to user with specific remediation hints. |
| **Dept 19: Hardware Encoder Crash** | VideoToolbox ASIC error | Master export interrupted | Automatic fallback to deterministic CPU software encoder (`libx264`). |
