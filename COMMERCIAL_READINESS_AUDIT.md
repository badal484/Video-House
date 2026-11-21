# Commercial Readiness, Intellectual Property & License Audit
**Document Version:** 1.0.0  
**Phase:** Part 16 — System Integration & Production Readiness  
**Target:** Legal, Compliance, Enterprise Deployment & Commercial Distribution  
**Registry Source:** [`LICENSE_REGISTRY.csv`](file:///Users/badal11/Desktop/Video%20House%20/LICENSE_REGISTRY.csv)  

---

## 1. Executive Summary

This audit evaluates the intellectual property (IP), licensing terms, and commercial distribution readiness of the Universal AI Video Production Studio. The studio was architected to enable uninhibited commercial deployment for both enterprise SaaS hosting and on-premises client workstations.

### Core Legal Compliance Rules:
1. **Zero AGPL-3.0 in Core Runtime:** Prevent copyleft contamination that would legally require open-sourcing the studio's proprietary orchestration and UI codebase.
2. **Zero Non-Commercial (CC-BY-NC) Models:** Ensure all AI weights, model checkpoints, and datasets are licensed for commercial media generation without royalty exposure.
3. **Subprocess Isolation for GPL Tools:** Tools like Blender (GPL-3.0) are executed strictly in isolated child processes (`shell=False`) via CLI contracts, preventing in-process linking contamination.
4. **Permissive First:** Prioritize MIT, Apache-2.0, and BSD-2/3-Clause dependencies across all 22 departments.

---

## 2. Dependency & Model Audit Matrix

### 2.1 Core Infrastructure & Libraries

| Component | License | Commercial Permitted | Isolation / Hygiene Requirement |
|---|---|---|---|
| **Python 3.13** | PSF License | **YES** | Standard permissive language runtime. |
| **FastAPI / Starlette** | MIT | **YES** | Standard permissive web framework. |
| **SQLite 3** | Public Domain | **YES** | Zero restrictions, embedded transactional engine. |
| **OpenTimelineIO** | Apache-2.0 | **YES** | ASWF notice preservation required. |
| **Motion Canvas** | MIT | **YES** | Permissive 2D procedural motion engine. |
| **Spotify Pedalboard** | Apache-2.0 | **YES** | Audio DSP engine; notice preservation. |
| **FFmpeg / FFprobe** | LGPL-2.1+ / GPL-2.0+ | **YES** | Dynamically linked or invoked via subprocess CLI. When `libx264` is compiled, FFmpeg binary is GPL-2.0. Invocation as an external CLI process isolates the studio runtime from GPL copyleft. |
| **Blender 4.x** | GPL-3.0 | **YES** | Invoked exclusively via headless background CLI (`blender -b -P ...`). No in-process C-bindings. |

### 2.2 Artificial Intelligence & Vision Models

| Model / Framework | Code License | Weights License | Commercial Status | Architectural Safe Substitution |
|---|---|---|---|---|
| **Wan2.1 Video Diffusion** | Apache-2.0 | Apache-2.0 | **Approved** | Alibaba open commercial release. |
| **Flux.1-schnell** | Apache-2.0 | Apache-2.0 | **Approved** | Black Forest Labs commercial release. |
| **SAM 2.1 Video** | Apache-2.0 | Apache-2.0 | **Approved** | Meta FAIR open commercial release. |
| **Depth Anything v2** | Apache-2.0 | Apache-2.0 | **Approved** | Open commercial release. |
| **faster-whisper** | MIT | MIT (OpenAI) | **Approved** | Fully permissive commercial transcription. |
| **Kokoro-82M TTS** | Apache-2.0 | Apache-2.0 | **Approved** | Permissive text-to-speech. |
| **Demucs v4** | MIT | MIT | **Approved** | Meta AI open stem separation. |
| **Grounding DINO** | Apache-2.0 | Apache-2.0 | **Approved** | **Substituted for Ultralytics YOLOv11 (AGPL-3.0)** to eliminate AGPL copyleft contamination. |
| **E2FGVI Video Inpainting** | Apache-2.0 | Apache-2.0 | **Approved** | **Substituted for ProPainter (CC-BY-NC-4.0)** to eliminate non-commercial restrictions. |
| **PyAnnote Audio 3.1** | MIT | CC-BY-4.0 | **Conditional** | Diarization weights require attribution notice in studio credits; enterprise deployments can negotiate commercial license or route to faster-whisper speaker diarization. |

### 2.3 Cloud Multimodal & Generative APIs

| Provider | Integration Type | Commercial Usage Terms | Data Privacy Terms |
|---|---|---|---|
| **Google Gemini API (Vertex AI)** | REST / gRPC SDK | Included in API terms | Customer prompts and video inputs are **not used for model training**. |
| **TwelveLabs Marengo / Pegasus** | REST API | Commercial SaaS license | Video embeddings kept in private customer indexes. |
| **Runway Gen-3 Alpha** | REST API | Commercial rights on paid tiers | Generated video output owned by paying customer. |
| **ElevenLabs Voice AI** | REST API | Enterprise commercial tier | Commercial rights to synthesized speech audio. |

---

## 3. High-Risk Contamination Defense Verification

### 3.1 Eliminating AGPL-3.0 (YOLOv11)
- **Risk:** Ultralytics YOLOv11 is licensed under AGPL-3.0. Linking or network-serving an AGPL library legally compels an organization to release its entire application source code under AGPL.
- **Resolution:** YOLOv11 was strictly prohibited. All open-vocabulary object bounding box detection and zero-shot tracking route to **Grounding DINO (Apache-2.0)**.

### 3.2 Eliminating Non-Commercial CC-BY-NC (ProPainter)
- **Risk:** ProPainter video inpainting is licensed under Creative Commons Non-Commercial 4.0. Generating commercial media with ProPainter violates copyright.
- **Resolution:** ProPainter was eliminated. Video inpainting and optical-flow propagation route to **E2FGVI (Apache-2.0)**.

### 3.3 Eliminating Remotion Commercial Royalties
- **Risk:** Remotion requires a paid commercial license (\$250–\$500/month) for companies making over \$10k/month.
- **Resolution:** Replaced with **Motion Canvas (MIT)**, which is 100% free and open-source with zero commercial royalties.

---

## 4. Legal Compliance Certification

The Universal AI Video Production Studio codebase and its runtime dependencies have been audited and certified **Commercially Compliant**. No AGPL-3.0, CC-BY-NC, or proprietary unlicensed code exists in the runtime path.
