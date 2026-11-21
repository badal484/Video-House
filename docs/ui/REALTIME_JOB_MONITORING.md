# Real-Time Job Monitoring & Background Queue Specification

## 1. Global Job Center Architecture

The studio processes long-running computational tasks across multiple departments:
- Media proxy generation & waveform extraction (Department 03)
- Shot boundary cut detection & audio transcription (Department 04)
- AI video, image, and voice generation (Department 15)
- DSP audio stems & dialogue restoration (Department 14)
- Multi-profile timeline rendering (Department 19)
- Automated technical QC defect auditing (Department 18)

### 1. Job Center Popover Widget
- Triggered by clicking the animated Job Center pill in the top application bar.
- Shows total active workers (e.g. `3 Active Workers`) and pending queue depth.
- Displays individual job progress cards with:
  - Job Name and Target Profile / Modality.
  - Department Badge (`Rendering`, `Generation`, `QC`, `Ingestion`).
  - Animated progress bar (0% to 100%).
  - Elapsed execution time and estimated time remaining (ETA).
  - Status indicator (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`).
  - Action buttons: "Cancel Job", "Retry", "View Output in Asset Browser", "Open QC Report".

### 2. Event-Driven Real-Time Updates
- State polling is kept strictly throttled (1,500ms intervals) and pauses automatically when browser tab is backgrounded.
- Toast notifications appear on the bottom-right for completed renders or critical QC alerts.

