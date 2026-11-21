# Threat Model & STRIDE Analysis
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Methodology:** Microsoft STRIDE Model & Attack Tree Decomposition  
**Status:** Canonical Security Threat Model  

---

## 1. STRIDE Threat Matrix

| STRIDE Threat Category | Studio Attack Surface | Threat Scenario | Architectural Countermeasure | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | API Authentication & Webhooks | Attacker presents forged bearer token or spoofed webhook callback. | Cryptographic JWT signing with HMAC-SHA256, short TTLs (1 hour), and webhook signature validation. | Medium |
| **Tampering** | Stored Media Assets & Timelines | Unauthorized modification of source media files or OTIO timeline JSON on disk. | Streaming SHA-256 integrity checksums stored in SQLite; immutable project version snapshots. | High |
| **Repudiation** | Creative Plan Approvals & Dubbing | User disputes initiating an expensive generative render job or unauthorized voice clone. | Audit trail logging in `project_versions` and `biometric_consents` recording timestamp, user ID, and IP address. | Medium |
| **Information Disclosure** | Media Derivatives & Telemetry | Leaking confidential unreleased movie footage or API keys via error traces. | Media streaming endpoints require authenticated project scope; Sentry/Loki log sanitizers redact credentials. | High |
| **Denial of Service** | Decompression Bombs & Render Queues | Malicious client submits infinite loop render jobs or zip bombs exhausting disk space. | Preflight validation gatekeeper, worker concurrency limits (4 max), disk space alert triggers (<5 GB pause). | High |
| **Elevation of Privilege** | Codec Exploitation & Shell Escapes | Specially crafted video packet exploits FFmpeg C-decoder to gain host shell access. | Non-root container user (`appuser`, UID 10001); subprocesses executed with `shell=False` and strict `RLIMIT`. | Critical |

---

## 2. Attack Tree Decomposition

### Attack Goal: Execute Arbitrary Host Command via Media Ingestion
```
[Execute Arbitrary Code on Host]
├── [Path Traversal File Overwrite]
│   ├── Bypass filename sanitization --> MITIGATED: Discard client name, generate UUIDv4
│   └── Escape project directory --> MITIGATED: os.path.realpath() verification
├── [Subprocess Command Injection]
│   ├── Inject shell metacharacters (;, |, `) --> MITIGATED: shell=False with List[str] arguments
│   └── Inject malicious FFmpeg CLI options --> MITIGATED: Strict argument schema whitelisting
└── [Codec Memory Corruption]
    ├── Craft malformed MP4/MOV header --> MITIGATED: 31 magic byte signature preflight
    └── Trigger heap overflow in libavcodec --> MITIGATED: Unprivileged sandbox execution
```
