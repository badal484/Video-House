# Production Runbook & Operations Manual
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Operational Runbook  

---

## 1. System Overview & Architecture

The Universal AI Video Production Studio operates as a modular monolith with isolated background workers. The system exposes:
- **Web UI & REST API:** Port `8000` (FastAPI / Uvicorn).
- **Database:** SQLite WAL file at `projects/studio_asset_registry.db`.
- **Media Asset Directory:** `assets/{project_id}/originals/` & `assets/{project_id}/derivatives/`.
- **Scratch Buffer:** `temp/` (pruned automatically).
- **Log Stream:** `logs/studio.jsonl` (JSON-formatted).

---

## 2. Daily Routine Operations

### 2.1 Starting the Production Service
```bash
# Direct startup via Python
./scripts/deploy_local.sh

# Or via Docker Compose
docker compose up -d
```

### 2.2 System Health & Telemetry Verification
```bash
# Check service health and hardware acceleration
curl -s http://localhost:8000/api/v1/system/telemetry | jq .

# Expected healthy output:
# {
#   "status": "HEALTHY",
#   "videotoolbox_acceleration": true,
#   "active_workers": 4,
#   "storage": { "free_gb": 38.5, ... }
# }
```

### 2.3 Scheduled Storage Maintenance & Cleanup
Run daily at 03:00 UTC via cron:
```bash
# Scan for orphaned derivative files without database references
python3 scripts/backup_restore.py orphans

# Prune temporary files older than 24 hours
find temp/ -type f -mtime +1 -delete
```

---

## 3. Disaster Recovery & Backup Routine

Run nightly at 02:00 UTC:
```bash
# Backup all active production projects
python3 scripts/backup_restore.py backup <PROJECT_ID> --out backups/

# Verify archive cryptographic checksum
python3 scripts/backup_restore.py verify backups/backup_<PROJECT_ID>_*.tar.gz
```

---

## 4. Emergency Procedures

### 4.1 Ingestion / Render Worker Hang
1. Identify stalled worker PID:
   ```bash
   ps aux | grep ffmpeg
   ```
2. Inspect recent logs:
   ```bash
   tail -n 100 logs/studio.jsonl | jq 'select(.level=="ERROR")'
   ```
3. Terminate hanging subprocess gracefully (`SIGTERM`), allowing cleanup handlers to delete partial artifacts.

### 4.2 SQLite Database Lock Recovery
If `sqlite3.OperationalError: database is locked` occurs:
1. Verify no lingering zombie FFmpeg processes hold open handles: `lsof projects/studio_asset_registry.db`.
2. Checkpoint WAL file:
   ```bash
   sqlite3 projects/studio_asset_registry.db "PRAGMA wal_checkpoint(TRUNCATE);"
   ```
3. Restart service.

