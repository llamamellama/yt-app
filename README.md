# YouTube Downloader

Simple CLI and web UI to download YouTube videos at a requested quality using `yt-dlp`.

### Optional

```
python3 -m venv .venv
source .venv/bin/activate
```

1. Setup Step

```
pip install -r requirements.txt
```

2.1. CLI

```
python main.py "<youtube_url>"" <quality>
```

Example:

```
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" best
```

Supported qualities include `2160p`, `1440p`, `1080p`, `720p`, `480p`, `360p`, and `best`.

If `ffmpeg` is not installed, the script automatically falls back to single-stream downloads, which may reduce quality. Install `ffmpeg` for the best results:

```
brew install ffmpeg
```

2.2. Graphic User Interface (GUI)

Run the Flask web UI locally:

```
python app.py
```

Open http://localhost:5001 and use the form to paste a YouTube URL and choose the quality from the dropdown. Recent downloads appear below the form.

Optionally set a custom secret key (recommended for multi-user deployments):

```
export FLASK_SECRET_KEY="some-long-random-string"
```

Or run it via Docker:

```
docker compose up --build
```

Visit http://localhost:5001 after the container starts. Downloads will be saved to the local `downloads` folder through a bind mount.

## Distribution

Build standalone executables with PyInstaller (bundles Python and the app):

### macOS

```
python -m pip install -r requirements.txt -r requirements-dev.txt
bash scripts/build_macos.sh
open dist/YouTubeDownloader
```

To bundle system ffmpeg explicitly (optional):

```
export FFMPEG_PATH="/usr/local/bin/ffmpeg"
export FFPROBE_PATH="/usr/local/bin/ffprobe"
bash scripts/build_macos.sh
```

Gatekeeper note: unsigned apps may prompt on first launch. For distribution, consider codesigning/notarization.

### Windows

```
py -m pip install -r requirements.txt -r requirements-dev.txt
PowerShell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
start dist/YouTubeDownloader/YouTubeDownloader.exe
```

Optionally specify ffmpeg paths:

```
PowerShell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -FfmpegPath "C:\\path\\to\\ffmpeg.exe" -FfprobePath "C:\\path\\to\\ffprobe.exe"
```

The app starts a local server on the configured port (default 5001) and auto-opens your browser.

### Troubleshooting builds

- Ensure you’re using the same Python interpreter for installing and building. The scripts call `python -m PyInstaller` to avoid PATH issues.
- If you have multiple Pythons (pyenv, Homebrew, system), run:

```
which python
python -V
python -m pip show pyinstaller
```

- On macOS, if you see “command not found: pyinstaller”, re-run: `python -m pip install pyinstaller` and use `bash scripts/build_macos.sh`.

