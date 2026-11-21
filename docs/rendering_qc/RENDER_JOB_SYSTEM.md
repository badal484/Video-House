# Render Job System Specification

## 1. Job Lifecycle & State Machine
The `RenderJobSystem` manages asynchronous rendering tasks, persistent job histories, progress tracking, and failure handling.

```
       [DRAFT]
          │
          ▼
    [VALIDATING] ──(Validation Failed)──► [BLOCKED]
          │
          ▼ (Preflight Passed)
       [QUEUED]
          │
          ▼ (Worker Assigned)
      [SCHEDULED]
          │
          ▼
       [RUNNING] ──(Worker Crash / Error)──► [RECOVERING] ──► [FAILED]
          │                                        │
          │                                        └──(Retry)──► [QUEUED]
          ▼ (Render Complete)
      [RENDERED]
          │
          ▼
     [QC_PENDING]
          │
          ├──(Critical Rule Violation)──► [QC_FAILED]
          │
          ▼ (All Rules Passed)
      [APPROVED]
          │
          ▼
      [DELIVERED]
```

## 2. Render Job Schema Attributes
Every `RenderJob` maintains complete provenance:
- `job_id`: Unique UUID.
- `project_id`: Target project UUID.
- `sequence_id`: Editorial timeline sequence UUID.
- `project_version`: Integer revision counter.
- `timeline_version`: Revision counter of the editorial timeline.
- `render_profile_id`: Identifier of the delivery profile used.
- `status`: Active state in the job lifecycle.
- `priority`: Scheduling priority (1 to 10; default 5).
- `worker_id`: Identifier of the executing worker.
- `progress`: Floating point completion percentage (0.0 to 100.0).
- `estimated_duration_sec`: Estimated total run time.
- `estimated_cost_usd`: Estimated compute cost.
- `actual_cost_usd`: Realized compute charge.
- `output_path`: Absolute path of the rendered artifact.
- `qc_report_id`: Linked UUID of the Quality Control report.
- `created_at` / `completed_at`: ISO-8601 UTC timestamps.

## 3. Idempotency & Duplicate Prevention
- The queue computes a deterministic cache key from:
  $$\text{Key} = \text{SHA256}(\text{project\_id} + \text{timeline\_version} + \text{render\_profile\_id} + \text{asset\_hashes})$$
- If an existing render with an identical cache key is already completed or currently running, the job system returns the existing job record, preventing redundant encoding passes.

