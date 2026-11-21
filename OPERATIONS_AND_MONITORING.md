# Operations & Ongoing Monitoring Manual
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Operational Standard  

---

## 1. Key Performance Indicators (KPIs) & Monitoring

| Metric | Target SLA | Warning Threshold | Critical Threshold |
| :--- | :--- | :--- | :--- |
| **API P99 Latency** | <50 ms | >150 ms | >500 ms |
| **Ingestion Transcode Speed** | >4.0x Realtime | <1.5x Realtime | <1.0x Realtime |
| **Master Export Speed (1080p)** | >6.0x Realtime (VideoToolbox) | <2.0x Realtime | <1.0x Realtime |
| **Worker Queue Wait Time** | <2.0 Seconds | >10.0 Seconds | >30.0 Seconds |
| **QC Pass Rate on Masters** | >98.0% | <90.0% | <80.0% |

---

## 2. Monitoring Endpoints

- **System Telemetry:** `GET http://localhost:8000/api/v1/system/telemetry`
- **Prometheus Metrics:** `GET http://localhost:8000/metrics`
- **Application Health:** `GET http://localhost:8000/api/v1/system/telemetry` (Returns HTTP 200 `{"status": "HEALTHY"}`)

---

## 3. Maintenance Window Checklist

When applying major updates or schema migrations:
1. Notify active users via the global announcements broadcast.
2. Put application in maintenance mode (pause queue intake).
3. Wait for active transcode/render workers to drain.
4. Execute full project and database backup (`scripts/backup_restore.py`).
5. Apply git update / container pull.
6. Run database migrations.
7. Execute integration test verification (`python3 -m unittest discover tests/integration/`).
8. Resume worker queue intake.
