# Frontend Architecture Specification

## 1. Architectural Patterns

The Studio Frontend uses a **Modular Component & Reactive Store Architecture**:
1. **Unidirectional Data Flow:** State flows downward from the central reactive store (`state.js`) to view components. User actions trigger mutations via asynchronous API client calls (`api_client.js`), which update the store and notify subscribed panels.
2. **Deterministic State Partitioning:**
   - `projects`: Master project records, active project ID, project settings.
   - `assets`: Registered media items, technical metadata, selected asset, filter/search queries.
   - `timeline`: Active timeline, tracks (V1, V2, A1, A2, etc.), clips, playhead position (`RationalTime`), selection, zoom level.
   - `director`: Active creative brief, concepts, script, storyboard cards, editing blueprint, approvals.
   - `agents`: 12 departmental agents, current status, active tasks, execution history.
   - `jobs`: Background jobs (ingestion, generation, rendering, QC) with real-time progress.
   - `ui`: Active workspace index, active modal, toast alerts, theme preferences.
3. **High-Frequency Playhead Decoupling:** Playhead updates (scrubbing, 60 FPS playback) do NOT re-render track DOM nodes. The playhead needle position (`left: X%`) and timecode display are updated via direct CSS transforms and `requestAnimationFrame`, ensuring zero frame drops.

---

## 2. Asynchronous API Client Design

The `api_client.js` module wraps all FastAPI backend endpoints with:
- **Strict Typing & Schema Validation:** Matches request payloads to backend Pydantic models.
- **Exponential Backoff & Retries:** Automatically retries transient network interruptions for non-destructive operations.
- **Timeout Protection:** Configurable timeouts (10s for metadata queries, 300s for media uploads).
- **Error Propagation:** Transforms backend HTTP 4xx/5xx responses into user-friendly error objects with actionable remediation steps.
