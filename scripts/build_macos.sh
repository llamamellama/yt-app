#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python - <<'PY'
import importlib, sys
try:
    importlib.import_module('PyInstaller')
except Exception:
    raise SystemExit(1)
PY
if [ $? -ne 0 ]; then
  python -m pip install pyinstaller
fi

# Optionally point to local ffmpeg binaries
# export FFMPEG_PATH="/usr/local/bin/ffmpeg"
# export FFPROBE_PATH="/usr/local/bin/ffprobe"

python -m PyInstaller yt_downloader.spec --noconfirm

echo "Build complete. See dist/YouTubeDownloader"

