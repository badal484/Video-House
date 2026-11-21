# Render Recovery, Reliability & Idempotency Specification

## 1. Failure Modes in Media Rendering
Long-running video rendering and encoding jobs fail due to diverse external causes:
- Host worker crashes or OS out-of-memory kernel kills.
- Insufficient disk storage in scratch or output volumes.
- Network disconnections during remote asset staging.
- Process termination during application restarts.
- Corrupted input media packets.

## 2. Recovery Strategies Implemented
The `RenderRecoveryManager` ensures robust recovery without wasting already-rendered work:

### 2.1 Safe Checkpoint Persistence
- As frame sequences or shot tasks complete, intermediate output chunks are registered in the persistent database.
- If a render job is aborted mid-sequence, the scheduler queries the database on restart, identifies the last valid completed shot, and resumes execution from that boundary.

### 2.2 Task-Level Retries & Exponential Backoff
- Failed remote render tasks are automatically retried up to 3 times with exponential backoff ($2^n \times 5\text{ seconds}$).
- Transient worker errors (e.g. temporary cloud GPU quota exhaustion) do not fail the entire project job.

### 2.3 Partial Output Quarantine & Cleanup
- Partially written video files or truncated MP4 containers are never left in production output paths.
- They are quarantined to `temp/scratch/` and automatically deleted upon job failure or recovery, preventing corrupted files from ever being delivered.

