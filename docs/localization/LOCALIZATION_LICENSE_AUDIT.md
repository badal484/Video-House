# Localization License Audit & Governance Compliance

## 1. Compliance Audit Overview
Under Studio Prime Directive #6 and commercial deployment requirements, every software library, pre-trained neural network checkpoint, and cloud API integrated into Department 17 must be audited for commercial licensing suitability.

## 2. Audit Matrix of Core Dependencies

| Component / Library | Stated License | Commercial Usability | Risk Category | Operational Guardrail |
| :--- | :--- | :--- | :--- | :--- |
| **faster-whisper** | MIT | Permitted | Green | Safe for direct in-process local execution. |
| **WhisperX** | BSD-3-Clause | Permitted | Green | Safe for in-process execution. |
| **CTranslate2** | MIT | Permitted | Green | Fast C++ inference engine. |
| **pyannote.audio** | MIT | Permitted (Code) | Amber | Code is MIT. HuggingFace checkpoints require user token acceptance. Model weights must be verified. |
| **Kokoro-82M** | Apache 2.0 | Permitted | Green | Commercial-ready compact TTS. |
| **LatentSync** | Apache 2.0 | Permitted | Green | Permissive open-weights model by ByteDance. |
| **MuseTalk** | MIT | Permitted | Green | Permissive open-source research model. |
| **Sync Labs API** | Commercial SLA | Permitted | Green | Enterprise commercial vendor. |
| **Wav2Lip Checkpoints** | **CC-BY-NC 4.0** | **PROHIBITED** | **Red** | **STRICTLY BLOCKED** from core distribution. Isolated behind remote adapter boundary or blocked completely. |
| **SadTalker Checkpoints** | **CC-BY-NC 4.0** | **PROHIBITED** | **Red** | **STRICTLY BLOCKED** from production packaging. |
| **pysubs2** | BSD-3-Clause | Permitted | Green | Subtitle parsing & formatting library. |
| **OpenTimelineIO** | Apache 2.0 | Permitted | Green | Canonical editorial data structure. |
| **ffmpeg-python** | MIT | Permitted | Green | Deterministic media multiplexing. |

## 3. Biometric Governance & Ethical Voice Rights
Modern international legislation requires strict safeguards against unauthorized deepfakes and non-consensual voice replication:
1. **Verifiable Consent Token:** Every voice profile registered in the studio requires a cryptographic hash and signature of the voice actor's signed agreement.
2. **Metadata Transparency:** Every exported dubbed audio file and video derivative includes C2PA provenance manifests denoting synthesized voice generation and lip-sync modification.
3. **Audit Trail:** Department 22 (`licensing_cost_tracking`) logs every character synthesized and frame morphed for licensing royalty tracking.
