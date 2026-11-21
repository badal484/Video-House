# Generation Security, Privacy & License Compliance
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 22_licensing_cost_tracking  
**Document:** GENERATION_SECURITY_AND_LICENSES.md  
**Version:** 1.0.0  

---

## 1. Credential & Secret Hygiene

- **API Keys**: Stored exclusively in environment variables (`RUNWAY_API_KEY`, `KLING_API_KEY`, `ELEVENLABS_API_KEY`, etc.) or secure vault stores.
- **Zero Logging**: API tokens are automatically sanitized from stdout, log files, and database records.

---

## 2. Data Privacy & Zero-Training Compliance

- External commercial providers with terms asserting ownership or rights to train on user media are barred from production use unless explicitly cleared under an Enterprise zero-data-retention agreement.
- Confidential client projects can enforce an `on_premise_only` flag, restricting generation to local open models (Wan2.1, Kokoro-82M, Procedural Audio).
