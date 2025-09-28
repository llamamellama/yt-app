"""Reusable YouTube download helpers."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Iterable

import yt_dlp

DEFAULT_OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"

QUALITY_OPTIONS = {
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "best": "bestvideo+bestaudio/best",
}

FALLBACK_OPTIONS = {
    "2160p": "best[height<=2160]",
    "1440p": "best[height<=1440]",
    "1080p": "best[height<=1080]",
    "720p": "best[height<=720]",
    "480p": "best[height<=480]",
    "360p": "best[height<=360]",
    "best": "best",
}

AVAILABLE_QUALITIES = tuple(QUALITY_OPTIONS.keys())


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def download_video(
    url: str,
    quality: str,
    *,
    downloads_dir: Path,
    output_template: str = DEFAULT_OUTPUT_TEMPLATE,
) -> list[str]:
    downloads_dir.mkdir(parents=True, exist_ok=True)
    can_merge = ffmpeg_available()
    format_selector = QUALITY_OPTIONS[quality] if can_merge else FALLBACK_OPTIONS[quality]

    if not can_merge and "+" in QUALITY_OPTIONS[quality]:
        print(
            "Warning: ffmpeg not found. Falling back to a single-stream download, which may reduce quality.",
            file=sys.stderr,
        )

    ydl_opts: dict[str, object] = {
        "format": format_selector,
        "outtmpl": str(downloads_dir / output_template),
        "quiet": False,
        "noplaylist": True,
        "merge_output_format": "mp4" if can_merge else None,
    }

    # Remove None for merge_output_format to avoid yt-dlp warning
    if ydl_opts["merge_output_format"] is None:
        del ydl_opts["merge_output_format"]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    return _collect_downloaded_files(info)


def _collect_downloaded_files(info: dict[str, object]) -> list[Path]:
    filenames: list[Path] = []

    requested_downloads = info.get("requested_downloads") if isinstance(info, dict) else None
    if isinstance(requested_downloads, Iterable):
        for item in requested_downloads:
            if isinstance(item, dict):
                filename = item.get("_filename") or item.get("filepath")
                if isinstance(filename, str):
                    filenames.append(Path(filename))

    if not filenames and isinstance(info, dict):
        filename = info.get("_filename") or info.get("filepath")
        if isinstance(filename, str):
            filenames.append(Path(filename))

    return filenames

