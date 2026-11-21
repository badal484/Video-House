# QC Policy Engine & Automated Rule Evaluation Specification

## 1. Configurable Quality Policies
Quality rules cannot be rigid or universal: a theatrical master has different tolerances than a rapid mobile social video. The `QCPolicyEngine` applies configurable policies based on target delivery profiles.

## 2. Severity Classification
Every rule failure is categorized into one of four severity levels:
1. **CRITICAL:** Total delivery blocker (e.g. file unreadable, missing video stream, wrong resolution, container corrupted). Job is halted immediately and marked `QC_FAILED`.
2. **ERROR:** Specification violation (e.g. loudness exceeds tolerance by $> 1.0\text{ LUFS}$, audio true-peak clipping, missing required subtitle file). Job is flagged for remediation.
3. **WARNING:** Minor defect or soft limit (e.g. VMAF score slightly below target threshold, single black frame at scene transition, CPS reading speed $17.5$). Job may pass under "Pass with Warnings" policy.
4. **INFO:** Informational notice (e.g. high dynamic range note, faststart atom applied).

## 3. Acceptance Policies Implemented
- **STRICT_BROADCAST:** Zero tolerance. Any `CRITICAL` or `ERROR` triggers automatic rejection; `WARNING` requires human supervisor sign-off.
- **STREAMING_PREMIUM:** Zero `CRITICAL` or `ERROR`. Allows up to 2 `WARNING`s with automated mitigation notes.
- **SOCIAL_FAST_TRACK:** Focuses on file playability, aspect ratio, and faststart; allows minor loudness and compression warnings to pass automatically.
- **HUMAN_GATE_REQUIRED:** Forces a pause before delivery, presenting the technical report and interactive review timeline to the operator.

