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

2.1 CLI

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

2.2 Graphic User Interface (GUI)

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

Visit http://localhost:5000 after the container starts. Downloads will be saved to the local `downloads` folder through a bind mount.

