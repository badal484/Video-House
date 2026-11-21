# Local Development & Engineering Setup Guide
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Target Environment:** macOS (Apple Silicon M-Series) & Linux Workstations  

---

## 1. Prerequisites & System Dependencies

1. **Python 3.10, 3.11, or 3.12**
   ```bash
   python3 --version
   ```
2. **FFmpeg 6.0+ with VideoToolbox (macOS) or NVENC (Linux)**
   ```bash
   # On macOS via Homebrew
   brew install ffmpeg libsndfile

   # Verify VideoToolbox hardware acceleration
   ffmpeg -encoders 2>&1 | grep videotoolbox
   ```
3. **Git 2.40+**

---

## 2. Quickstart Installation

```bash
# 1. Clone repository
git clone https://github.com/badal484/Video-House.git
cd "Video House "

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Run test suite to verify installation
python3 -m unittest discover tests/unit/ -p "test_*.py"

# 6. Launch local studio development server
./scripts/deploy_local.sh
```

Navigate your browser to `http://localhost:8000` to interact with the Single-Page Application.

---

## 3. Project Directory Conventions

- `departments/`: 22 isolated production department modules.
- `core/`: Shared kernel (database, storage, security, timeline, media validator, observability).
- `tests/unit/`: Fast in-memory unit tests (run in <15s).
- `tests/integration/`: End-to-end multi-department integration tests.
- `test_artifacts/`: Generated test renders, SVG contact sheets, and manifests.
- `projects/`: SQLite asset registry (`studio_asset_registry.db`).
- `assets/`: Physical ingested original media and generated derivatives.
- `temp/`: Scratch directory for intermediate rendering and audio DSP.

