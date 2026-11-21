# Claude Code & Assistant Guidelines
**Project:** Universal AI Video Production Studio  
**Workspace:** `/Users/badal11/Desktop/Video House`  

---

## 1. Build, Test & Lint Commands

```bash
# Environment Setup (Python 3.13 Virtual Environment)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Unit Tests
pytest tests/unit -v

# Run Integration Tests
pytest tests/integration -v

# Linting & Type Checking
ruff check .
ruff format . --check
mypy core departments schemas

# Run Studio API Backend (Local Development)
python3 -m uvicorn departments.01_studio_application.api:app --reload --port 8000
```

---

## 2. Core Architecture Constraints for Code Generation

- **Pydantic v2 Contracts:** All inter-department messages, requests, and serialized schemas must use Pydantic v2 (`from pydantic import BaseModel, Field`).
- **Path Handling:** Always use `pathlib.Path` instead of string path manipulations.
- **Async I/O:** Use asynchronous I/O (`asyncio`, `httpx`, `anyio`) for network requests, provider adapters, and file streaming.
- **Hardware Concurrency:** The local workstation is an Apple M4 with 10 CPU cores and 16GB RAM. In multi-processing loops, limit default concurrency to 6-8 worker threads to prevent UI starvation.
- **Time Representation:** Always use `opentimelineio.opentime.RationalTime` for video timeline arithmetic. Never calculate frame positions using Python floating-point division without snapping to integer rational rates.
- **Never Hardcode Secrets:** API keys for Gemini, TwelveLabs, ElevenLabs, Runway, and Kling must be loaded exclusively via environment variables (`GEMINI_API_KEY`, `TWELVELABS_API_KEY`, etc.) or `.env` files.
