# Motion Graphics & Typography License Audit
**Project:** Universal AI Video Production Studio  
**Milestone:** Part 06 — Professional Motion Graphics & Typography Studio  
**Document Version:** 1.0.0  
**Compliance Lead:** Principal Systems Architect & Legal Hygiene Officer  
**Date:** 2026-11-21  

---

## 1. Purpose & Legal Hygiene Mandate

The Universal AI Video Production Studio is architected as an enterprise-grade, commercially deployable platform. In accordance with the Studio Prime Directives (`AGENTS.md`):
- **Never introduce AGPL-3.0 libraries or non-commercial (CC-BY-NC) assets into the core runtime without explicit architectural review.**
- **Never assume a downloadable font or code snippet is licensed for commercial video broadcasting or redistribution.**
- Every software library, font family, and interchange tool must be audited for license compatibility, commercial distribution rights, and patent/indemnification clauses.

---

## 2. Software Engine License Audit

| Technology / Library | Version | License | Commercial Video Production Rights | Restrictions / Caveats | Decision |
| :--- | :---: | :--- | :---: | :--- | :---: |
| **Studio Vector & Canvas Engine** | 1.0.0 | MIT / Apache 2.0 (Studio Owned) | Full (100% Royalty-Free) | None | **Approved for Core Runtime** |
| **Motion Canvas** | 3.16.x | MIT License | Full (100% Royalty-Free) | Standard MIT attribution | **Approved as Vector Provider** |
| **HyperFrames / Playwright** | 1.49.x | Apache 2.0 (Microsoft) | Full | Standard Apache 2.0 attribution | **Approved as Headless Web Provider** |
| **Remotion** | 4.0.x | Custom Remotion License | **RESTRICTED** | Free only for non-commercial or companies $\le 3$ employees. Paid commercial license required for larger deployment. | **Restricted to Optional Adapter** (Not in Core) |
| **GSAP (GreenSock)** | 3.12.x | GreenSock "Standard" License | **RESTRICTED** | Free for many uses, but requires paid "Club GreenSock" license if part of a fee-charging product distributed to multiple customers. | **REJECTED for Core Runtime** |
| **Theatre.js** | 0.7.x | Apache 2.0 | Full | None | **Approved for Future Studio UI** |
| **Pillow (PIL)** | 12.1.x | HPND / MIT Equivalent | Full | Permissive historical notice | **Approved for Core Runtime** |
| **Lottie-web / rlottie** | 5.12.x | MIT / LGPL v2.1 | Full | LGPL applies to dynamic library in rlottie if used | **Approved for Ingestion Parsing** |
| **FFmpeg** | 8.1.x | LGPL v2.1+ | Full | Subprocess execution preserves commercial isolation | **Approved (Existing Part 01–05)** |

---

## 3. Font Family License Audit (Commercial Video Distribution)

Broadcasting video content on YouTube, television, streaming, or social media constitutes commercial publication. Standard desktop font licenses (EULAs) frequently prohibit embedding glyphs into broadcast video streams without expensive enterprise extensions.

The studio standardizes exclusively on **SIL Open Font License (OFL 1.1)** and **Apache 2.0** fonts, which explicitly authorize commercial video generation, broadcasting, and redistribution:

| Font Family | Designer / Foundry | License | Commercial Broadcast Allowed? | Language & Script Coverage | Studio Role |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Inter** | Rasmus Andersson | SIL OFL 1.1 | **YES** | Latin, Cyrillic, Greek (Variable Weight) | Primary UI, Tech Lower Thirds, Modern HUDs |
| **Montserrat** | Julieta Ulanovsky | SIL OFL 1.1 | **YES** | Latin, Cyrillic (Geometric Sans) | Commercial Titles, Hero Banners, Brand Marks |
| **Roboto Mono** | Christian Robertson (Google) | Apache 2.0 | **YES** | Latin, Cyrillic, Greek (Monospace) | Telemetry Data, Timestamps, Coordinate HUDs |
| **Playfair Display** | Claus Eggers Sørensen | SIL OFL 1.1 | **YES** | Latin, Cyrillic (High-contrast Serif) | Cinematic Openers, Editorial Quotes, Film Titles |
| **Noto Sans** | Google Fonts Team | SIL OFL 1.1 | **YES** | Pan-Global scripts (Latin, Arabic, CJK, Hebrew) | Global Internationalized Subtitles & Labels |
| **Noto Sans Devanagari** | Google Fonts Team | SIL OFL 1.1 | **YES** | Devanagari (Hindi, Marathi, Sanskrit, Nepali) | Indic Multilingual Titles & Lower Thirds |

---

## 4. Compliance Summary & Architectural Guarantee

1. **Zero Copyleft Infection:** All code authored in Department 09 is permissively licensed.
2. **Zero Commercial Licensing Liabilities:** Rejection of GSAP and isolation of Remotion prevents legal encumbrances on downstream commercial creators.
3. **Typography Safety:** All default fonts bundled with presets carry verified SIL OFL 1.1 or Apache 2.0 licenses.

