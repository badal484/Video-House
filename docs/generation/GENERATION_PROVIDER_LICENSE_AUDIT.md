# Generative Provider License & Privacy Audit
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 22_licensing_cost_tracking  
**Document:** GENERATION_PROVIDER_LICENSE_AUDIT.md  
**Version:** 1.0.0  

---

## 1. Legal & Regulatory Audit Framework

Media generation creates potential legal exposure across four vectors:
1. **Model Training Data Copyright**: Fair use vs infringement risks.
2. **Output Intellectual Property Rights**: Ownership and copyrightability of AI-generated assets.
3. **Data Privacy & Scraping**: Whether user-uploaded images/videos are retained for training.
4. **Biometric & Publicity Rights**: Unauthorized voice cloning or celebrity likeness generation.

---

## 2. Provider Legal & Privacy Comparison

| Provider | Data Privacy & Retention Policy | Inputs Used for Training? | Output Commercial Ownership | Content Moderation Filter | Indemnification Offered? |
|---|---|---|---|---|---|
| **Runway ML** | Zero retention option on enterprise; API data stored 30 days for abuse | No (API tier exempt) | Customer owns all outputs | Strict automated vision/text safety | Yes (Enterprise tier) |
| **Kling AI** | Standard cloud storage for task history; prompt logged | Opt-out via enterprise | User owns generated outputs | Multi-language automated filter | No |
| **Black Forest Labs (FLUX.1 Pro)** | API requests processed via partner clouds (Replicate, Together); zero training | No (API terms) | Customer owns all generated images | Standard safety prompt filters | No |
| **ElevenLabs** | Voice data protected; zero training on private voices | No (Paid plans exempt) | User owns full commercial audio rights | Voice biometric verification check | Yes (Enterprise tier) |
| **Meta AudioCraft (MusicGen)** | Local inference (Zero external transmission) | N/A (Local model) | User owns output under MIT terms | None (Local execution) | Self-indemnified |
| **Wan2.1 (Open Weights)** | Local / Private cloud inference | N/A (Self-hosted) | 100% Customer ownership | Customizable local filter | Self-indemnified |

---

## 3. Studio Compliance Directives

- **Approval Gate for External Uploads**: In accordance with Prime Directive 6, user footage and character references may never be uploaded to external commercial APIs without explicit human authorization.
- **Provenance Logging**: Every generated asset records its generation metadata, model version, seed, prompt, and license identifier in the Central Common Asset Registry.
