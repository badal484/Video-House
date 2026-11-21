# Render Cost Management & Compute Quota Specification

## 1. Cost Management & Budgeting Framework
Rendering and encoding can consume massive cloud compute resources if unmonitored. The `RenderCostManager` enforces real-time budget controls and prevents runaway compute expenses.

## 2. Resource & Cost Tracking Metrics
For every render job, the cost manager tracks:
- **Local Compute:** Wall-clock seconds on local CPU / Apple Silicon VideoToolbox ASIC (zero financial charge, tracked for performance profiling).
- **Cloud Compute:** Worker instance run time $\times$ hourly rate (e.g. AWS EC2 G5.2xlarge @ $\$1.212/\text{hr}$).
- **Storage Egress:** GB transferred across cloud regions or out to external storage.
- **Provider API Charges:** Direct charges for commercial neural rendering (e.g. Sync Labs Lip-Sync per-minute pricing).

## 3. Financial Ceiling & Preflight Approval Gate
- **Project Budget Ceiling:** Projects specify a maximum allowed compute budget (e.g. $\$25.00$).
- **Single-Job Safety Cap:** If an individual render job's estimated cost exceeds $\$1.00$, the scheduler automatically transitions the job to `BLOCKED` and requests explicit user authorization via `HumanApprovalGate`.
- **Exceeded Budget Enforcement:** If a project reaches its budget limit, all non-essential rendering is paused until the user explicitly expands the ceiling.

