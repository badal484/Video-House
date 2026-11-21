# AI Generation Studio REST API & CLI Reference
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 01_studio_application  
**Document:** GENERATION_API_REFERENCE.md  
**Version:** 1.0.0  

---

## 1. Overview

Department 15 exposes REST endpoints via FastAPI in `departments/01_studio_application/api.py`.

---

## 2. API Endpoints

### 2.1 Job Execution & Management
- `POST /api/v1/generation/jobs`: Submit an asynchronous media generation job.
- `GET /api/v1/generation/jobs/{job_id}`: Poll job status, progress percentage, and output assets.
- `POST /api/v1/generation/jobs/{job_id}/cancel`: Cancel a queued or running generation job.
- `GET /api/v1/generation/projects/{project_id}/jobs`: List all generation jobs for a project.

### 2.2 Providers & Models
- `GET /api/v1/generation/providers`: List registered generation providers and declared capabilities.
- `GET /api/v1/generation/models`: List available foundational models and cost rates.

### 2.3 Prompt & Character Management
- `POST /api/v1/generation/compile-prompt`: Compile a structured prompt into provider-tailored syntax.
- `POST /api/v1/generation/characters`: Register a reusable character reference profile.
- `GET /api/v1/generation/characters/{character_id}`: Retrieve character reference pack and turnaround sheet.

### 2.4 Approvals & Budgets
- `POST /api/v1/generation/jobs/{job_id}/approve`: Human approval for blocked high-cost generations.
- `GET /api/v1/generation/projects/{project_id}/budget`: Inspect project budget allocation, spend, and ceiling.
