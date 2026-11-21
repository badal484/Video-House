# Infrastructure Technology Comparison & Selection Matrix
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Technical Evaluation  

---

## 1. Storage & Persistence Tier Comparison

| Dimension | SQLite + WAL (Current / Selected Local) | PostgreSQL + PostGIS (Selected Cloud) | MongoDB / Document DB | Amazon DynamoDB |
| :--- | :--- | :--- | :--- | :--- |
| **ACID Guarantees** | Full ACID (Single-writer WAL) | Full ACID (Multi-version MVCC) | Document-level only | Item-level / DynamoDB Transact |
| **Binary Asset Linking** | Relational foreign keys & cascade | Relational foreign keys & cascade | Loose ObjectId references | Partition key lookups |
| **Memory Footprint** | Extremely low (~8 MB) | Moderate (~80–150 MB) | High (~300–800 MB) | Cloud-managed (Serverless) |
| **Operational Simplicity** | Zero external processes; single file | Dedicated service container | Clustered replicas required | AWS IAM / Cloud-bound |
| **Performance (Local)** | >50,000 read queries/sec in-process | ~12,000 queries/sec (TCP socket) | ~8,000 queries/sec | ~2,500 queries/sec (WAN) |
| **Recommendation** | **Adopted for Local & Single-Node** | **Adopted for Clustered Cloud Tier**| **Rejected** (weak schema rigor) | **Rejected** (vendor lock-in) |

---

## 2. Job Queue & Work Distribution Comparison

| Dimension | Asyncio SQLite Queue (Current) | Redis + BullMQ / Celery | Temporal.io Durable Workflows | Apache Kafka |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture** | In-process asynchronous task queue | Memory pub/sub with worker pools | Event-sourcing orchestration | Distributed commit log |
| **Crash Recovery** | SQLite table state recovery | Redis AOF persistence | Event history state replay | Partition offset tracking |
| **Task Replay & Timers**| Basic retry loop with sleep | Delayed tasks via sorted sets | Built-in durable timers & loops | Manual consumer offsets |
| **Footprint** | 0 external services | ~40 MB Redis instance | Multi-container cluster (~1 GB) | Heavy JVM cluster (>2 GB) |
| **Recommendation** | **Default Local Execution Engine** | **Recommended Cloud Queue Engine**| **Adopted for Long-Running DAGs**| **Rejected** (unnecessary complexity) |

---

## 3. Media Processing Infrastructure Comparison

| Dimension | FFmpeg + VideoToolbox (Selected) | GStreamer Pipelines | Cloud Transcoding APIs (AWS Elemental) |
| :--- | :--- | :--- | :--- |
| **Latency** | Sub-millisecond pipeline launch | Complex pipeline initialization | High (HTTP upload + queuing) |
| **Hardware Acceleration** | Apple Silicon VideoToolbox, NVENC, QSV | Hardware plugins (vaapi, nvh264enc) | Cloud-managed dedicated ASICs |
| **Format Flexibility** | Broadest industry format coverage | Extensive plugin architecture | Restricted to standard web/broadcast profiles |
| **Commercial Licensing** | LGPL 2.1+ / GPL v2+ (isolated CLI) | LGPL 2.1+ (complex plugin licensing) | High per-minute commercial billing fees |
| **Recommendation** | **PRIMARY STUDIO MEDIA ENGINE** | **Rejected** (brittle pipeline debugging) | **Rejected for Core** (cost & latency) |

---

## 4. Containerization & Deployment Orchestration

| Dimension | Docker Compose (Selected) | Kubernetes (K8s) | Nomad by HashiCorp | Fly.io / Railway PaaS |
| :--- | :--- | :--- | :--- | :--- |
| **Setup Complexity** | Single declarative YAML file | High (Ingress, CNI, CSI, Helm, CRDs) | Moderate (HCL files, Nomad server) | Very Low (CLI push) |
| **Local Dev Parity** | 100% identical between dev & prod | Poor (Minikube/k3s overhead on 16GB RAM) | Moderate | Low (proprietary platform semantics) |
| **Resource Overhead** | Minimal (~20 MB engine overhead) | >1.5 GB just for control plane | ~150 MB Nomad client/server | Minimal local |
| **GPU Scheduling** | Native `--gpus all` or macOS Metal | NVIDIA GPU Operator | Nomad GPU device driver | Cloud GPU add-on pricing |
| **Recommendation** | **CANONICAL LOCAL & CLOUD BASELINE**| **Optional for High-Scale Enterprise**| **Alternative for Bare-Metal** | **Convenient Cloud Preview Option** |

