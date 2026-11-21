# Voice, Music & Sound License Audit
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production & 22_licensing_cost_tracking  
**Document:** AUDIO_VOICE_AND_MUSIC_LICENSE_AUDIT.md  
**Version:** 1.0.0  

---

## 1. Compliance Mandate

Audio distribution is subject to stringent copyright, neighboring rights, and publicity rights legislation globally (including DMCA in the US, EU Copyright Directive, and biometric voice protection statutes). Unlicensed background music, unauthorized celebrity voice clones, or training on copyrighted audio assets represent severe legal liabilities for production studios.

Department 14 enforces automated verification across three audio categories:
1. **Voice Likeness & Consent**: Zero unauthorized voice cloning.
2. **Music Master & Publishing Rights**: Verification of sync and master licenses.
3. **Sound Effects (SFX) & Foley**: Royalty-free commercial indemnification.

---

## 2. Voice Likeness & Synthetic Voice Rights

### 2.1 Voice Consent Protocol
Before rendering synthetic dialogue or dubbing, the system verifies the actor profile in `character_identities` or `voice_profiles`:
- Every voice profile must possess a valid `consent_grant_id` and signed digital release record.
- **Biometric Likeness Verification**: No voice synthesis prompt may target living individuals without explicit cryptographic authorization keys.
- **Watermarking**: Generated synthetic speech includes high-frequency inaudible watermarking conformant to C2PA (Coalition for Content Provenance and Authenticity) standards.

---

## 3. Music Licensing Hierarchy

Every musical asset ingested into `core/assets/database.py` is tagged with its rights tier:

```
                      ┌─────────────────────────────────┐
                      │    Music Asset Ingestion Check  │
                      └────────────────┬────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│ Tier 1:       │              │ Tier 2:       │              │ Tier 3:       │
│ Original AI / │              │ Commercial    │              │ Public Domain │
│ Procedural    │              │ Library Sync  │              │ (CC0 / PD)    │
│ (100% Owned)  │              │ (Artlist/Epi) │              │ Pre-1929      │
└───────┬───────┘              └───────┬───────┘              └───────┬───────┘
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────┐
                      │    License Registry Clearance   │
                      │   (Approved for Monetization)   │
                      └─────────────────────────────────┘
```

- **Tier 1 (Original Procedural / AI)**: 100% owned by the studio. Safe for worldwide broadcast and monetization without royalty obligations.
- **Tier 2 (Commercial Sync License)**: Verified against `LICENSE_REGISTRY.csv`. Requires registered license certificate number.
- **Tier 3 (Public Domain / CC-BY)**: Attribution metadata automatically compiled into credit roll rollouts.
- **Prohibited Tiers**: Creative Commons Non-Commercial (CC-BY-NC), All Rights Reserved without explicit sync agreement, or scraping unauthorized streaming platforms.

---

## 4. In-Process DSP & Code License Audit

All dependencies utilized in Department 14 adhere strictly to permissive open-source licenses:
- **Spotify Pedalboard**: Apache-2.0 (Permissive, commercial friendly).
- **SciPy / NumPy**: BSD-3-Clause (Permissive, commercial friendly).
- **PyAV (FFmpeg)**: LGPL-2.1+ / GPL-2.0+ (Dynamic linking / CLI isolation compliant).
- **OpenTimelineIO**: Apache-2.0 (ASWF industry standard).
- **Strictly Prohibited**: AGPL-3.0 libraries are barred from the in-process execution environment.
