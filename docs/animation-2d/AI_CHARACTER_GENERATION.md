# AI CHARACTER GENERATION & CONSISTENCY SPECIFICATION
**Department:** 12_character_production & 10_animation_2d  
**Topic:** Reference Image Conditioning, Pose Control, and Multi-View Synthesis  

---

## 1. Architecture of AI Character Synthesis

```
[ Character Concept / Text Prompt ]
               │
               ├──► [ Approved Reference Images (Front, 3/4, Profile) ]
               │              │
               │              ▼
               │     [ IP-Adapter Token Projection ]
               │              │
               ├──► [ Target Pose / Skeleton (OpenPose) ]
               │              │
               │              ▼
               │     [ Spatial ControlNet Guidance ]
               │              │
               ▼              ▼
     [ Latent Diffusion Multi-Conditioning ]
                     │
                     ▼
       [ Candidate Character Image ]
                     │
                     ▼
       [ Automated Identity Auditor ]
       • Proportion check (head ratio)
       • Color distance delta (CIE Lab)
       • Face geometry score
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    [ PASSED ]             [ REJECTED ]
(Commit to Asset Store)  (Regenerate with seed shift)
```

---

## 2. Preventing Hallucination & Identity Drift

Standard text-to-image models fail character consistency because diffusion cross-attention randomly re-synthesizes facial features, hair partings, and clothing accessories on every seed.

### Studio Enforcement Protocol:
1. **Decoupled Identity Conditioning:** Face structure is conditioned via facial feature embedding; costume color palette is conditioned via explicit RGB constraints; pose is conditioned via OpenPose skeletal coordinate maps.
2. **Settei Constraint Masking:** Background generation is separated from character generation. Characters are generated against pure alpha or neutral flat backdrops before compositing.
3. **Automated Drift Rejection:** If the candidate image violates the registered `CharacterIdentity` color palette by $\Delta E > 8.0$ or proportion by $> 5\%$, the candidate is automatically discarded without human intervention.
