# Disaster Recovery, Backup & Restore Runbook
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Recovery Objectives:** RPO = 24 Hours, RTO = <30 Minutes  

---

## 1. Recovery Objectives (RPO & RTO)

- **Recovery Point Objective (RPO):** Maximum 24 hours of data loss (nightly automated snapshots) or 5 minutes for active projects with version milestone snapshotting.
- **Recovery Time Objective (RTO):** Full project state restoration and physical media relinking in under 30 minutes.

---

## 2. Backup Execution Procedures

### 2.1 Automated Project Backup via CLI
```bash
# Create self-contained archive (.tar.gz)
python3 scripts/backup_restore.py backup <PROJECT_ID> --out /mnt/backups/

# The generated archive contains:
# - project_metadata.json (Project settings, stages, timelines, version history)
# - backup_manifest.json (SHA-256 hashes of all assets)
# - media/ (Physical source media originals)
```

### 2.2 Database-Level Hot Backup (SQLite WAL)
```bash
# Safe live SQLite backup without locking writers
sqlite3 projects/studio_asset_registry.db ".backup 'backups/db_backup_$(date +%Y%m%d).db'"
```

---

## 3. Disaster Recovery Restoration Procedures

### 3.1 Verification Prior to Restore
Always verify archive cryptographic integrity before restoring:
```bash
python3 scripts/backup_restore.py verify backups/backup_<PROJECT_ID>_20261121_020000.tar.gz

# Expected output:
# Verification: PASSED - Backup archive integrity verified (all checksums valid).
```

### 3.2 Restoring Project on Clean Host
```bash
# Restore project, database entries, and media files to assets/
python3 scripts/backup_restore.py restore backups/backup_<PROJECT_ID>_20261121_020000.tar.gz

# Output:
# Project restored successfully: <PROJECT_ID>
```
3. Restart studio service. The project and all source assets, timelines, and versions appear in the UI immediately.
