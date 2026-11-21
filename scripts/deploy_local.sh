#!/usr/bin/env bash
# ==============================================================================
# Local Startup Script for Universal AI Video Production Studio
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo " Starting Universal AI Video Production Studio on Local Machine"
echo "======================================================================"

# 1. Check Python version
PYTHON_BIN=$(command -v python3 || true)
if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: python3 not found. Please install Python 3.10+."
    exit 1
fi

PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo " Python Runtime: $PYTHON_BIN (v$PY_VER)"

# 2. Check FFmpeg
FFMPEG_BIN=$(command -v ffmpeg || true)
if [ -z "$FFMPEG_BIN" ]; then
    echo "WARNING: ffmpeg not found in PATH. Media transcoding will be impaired."
else
    echo " Media Engine: $FFMPEG_BIN"
fi

# 3. Create required directories
mkdir -p assets projects temp logs backups

# 4. Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo " Creating .env from .env.example..."
        cp .env.example .env
    fi
fi

# 5. Launch FastAPI via uvicorn
echo " Launching Studio API Server & Web UI on http://localhost:8000"
echo " Press Ctrl+C to stop."
exec python3 -m uvicorn departments.studio_application.api:app --host 0.0.0.0 --port 8000 --log-level info
