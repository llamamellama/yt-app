"""Reusable YouTube download helpers."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
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
    # Audio only. "audio" (the default) prefers YouTube's AAC stream, which plays
    # almost everywhere; "audio-opus" prefers its Opus stream. Within each, yt-dlp
    # still picks the original language, non-DRC, highest quality tier. The
    # /best fallback relies on ffmpeg to drop the video.
    "audio": "bestaudio[acodec^=mp4a]/bestaudio/best",
    "audio-opus": "bestaudio[acodec=opus]/bestaudio/best",
}

FALLBACK_OPTIONS = {
    "2160p": "best[height<=2160]",
    "1440p": "best[height<=1440]",
    "1080p": "best[height<=1080]",
    "720p": "best[height<=720]",
    "480p": "best[height<=480]",
    "360p": "best[height<=360]",
    "best": "best",
    # Without ffmpeg we can't strip video from a combined stream, so require a
    # real audio-only stream rather than silently saving a video.
    "audio": "bestaudio[acodec^=mp4a]/bestaudio",
    "audio-opus": "bestaudio[acodec=opus]/bestaudio",
}

# Codec ffmpeg saves each audio-only quality as. "m4a" always yields AAC: it
# copies an AAC stream as-is and re-encodes only if none was available. "best"
# never re-encodes; it keeps whatever codec was downloaded.
AUDIO_CODECS = {
    "audio": "m4a",
    "audio-opus": "best",
}

AVAILABLE_QUALITIES = tuple(QUALITY_OPTIONS.keys())

# Browsers yt-dlp can read cookies from directly. Used to authenticate
# downloads of restricted videos (age-restricted, members-only, private,
# premium, or region-locked) that otherwise return HTTP 403 Forbidden.
SUPPORTED_COOKIE_BROWSERS = (
    "chrome",
    "safari",
    "firefox",
    "edge",
    "brave",
    "chromium",
    "opera",
    "vivaldi",
)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


# Binary name yt-dlp expects for each runtime, in yt-dlp's priority order.
JS_RUNTIME_BINARIES = {
    "deno": "deno",
    "node": "node",
    "bun": "bun",
    "quickjs": "qjs",
}

# Minimum versions accepted by yt-dlp (mirrors yt_dlp.utils._jsruntime); only
# used as a fallback if yt-dlp's own runtime probing API is unavailable.
JS_RUNTIME_MIN_VERSIONS = {
    "deno": (2, 3, 0),
    "node": (22, 0, 0),
    "bun": (1, 2, 11),
}


def _candidate_runtime_paths(binary: str) -> list[Path]:
    """Locate every copy of *binary* we can find: PATH, then version managers."""
    home = Path.home()
    candidates: list[Path] = []

    if found := shutil.which(binary):
        candidates.append(Path(found))

    # Common install locations that may not be on PATH (or may be shadowed by an
    # older default), e.g. nvm keeps every installed Node version side by side.
    search_dirs: list[Path] = [
        Path("/opt/homebrew/bin"),
        Path("/usr/local/bin"),
        home / ".deno" / "bin",
        home / ".bun" / "bin",
        home / ".volta" / "bin",
    ]
    nvm_dir = Path(os.environ.get("NVM_DIR", home / ".nvm"))
    search_dirs.extend(sorted((nvm_dir / "versions" / "node").glob("*/bin"), reverse=True))
    search_dirs.extend(sorted((home / ".fnm" / "node-versions").glob("*/installation/bin"), reverse=True))
    search_dirs.extend(sorted((home / ".local" / "share" / "fnm" / "node-versions").glob("*/installation/bin"), reverse=True))

    for directory in search_dirs:
        exe = directory / binary
        if exe.is_file() and os.access(exe, os.X_OK):
            candidates.append(exe)

    # De-duplicate while preserving order (resolve symlinks such as nvm shims).
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        real = path.resolve()
        if real not in seen:
            seen.add(real)
            unique.append(path)
    return unique


def _probe_runtime(name: str, path: Path) -> tuple[int, ...] | None:
    """Return the runtime's version tuple if yt-dlp considers it supported."""
    try:
        from yt_dlp.globals import supported_js_runtimes

        runtime_cls = supported_js_runtimes.value.get(name)
    except Exception:  # pragma: no cover - API drift in yt-dlp
        runtime_cls = None

    if runtime_cls is not None:
        try:
            info = runtime_cls(path=str(path)).info
        except Exception:
            return None
        if info is None or not info.supported:
            return None
        return tuple(info.version_tuple)

    # Fallback: parse `--version` ourselves.
    try:
        out = subprocess.run(
            [str(path), "--version"], capture_output=True, text=True, timeout=10, check=False
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"(\d+(?:\.\d+)+)", out)
    if not match:
        return None
    version = tuple(int(part) for part in match.group(1).split("."))
    if version < JS_RUNTIME_MIN_VERSIONS.get(name, (0,)):
        return None
    return version


def detect_js_runtimes() -> dict[str, dict]:
    """Return supported JavaScript runtimes to hand to yt-dlp as ``js_runtimes``.

    Modern yt-dlp needs a JS runtime to solve YouTube's player/nsig challenge.
    Without one it skips formats and can pick a stream URL that returns HTTP
    403. yt-dlp only auto-enables ``deno`` and, since 2026.8, rejects Node
    older than 22. This looks in PATH *and* in nvm/fnm/Homebrew install
    locations, verifies each candidate against yt-dlp's minimum version, and
    returns the newest supported copy of each runtime with an explicit path.
    """
    runtimes: dict[str, dict] = {}
    for name, binary in JS_RUNTIME_BINARIES.items():
        best: tuple[tuple[int, ...], Path] | None = None
        for path in _candidate_runtime_paths(binary):
            version = _probe_runtime(name, path)
            if version is not None and (best is None or version > best[0]):
                best = (version, path)
        if best is not None:
            runtimes[name] = {"path": str(best[1])}
    return runtimes


def download_video(
    url: str,
    quality: str,
    *,
    downloads_dir: Path,
    output_template: str = DEFAULT_OUTPUT_TEMPLATE,
    cookies_from_browser: str | None = None,
    cookies_file: Path | None = None,
) -> list[Path]:
    downloads_dir.mkdir(parents=True, exist_ok=True)
    can_merge = ffmpeg_available()
    audio_codec = AUDIO_CODECS.get(quality)
    format_selector = QUALITY_OPTIONS[quality] if can_merge else FALLBACK_OPTIONS[quality]

    if not can_merge and "+" in QUALITY_OPTIONS[quality]:
        print(
            "Warning: ffmpeg not found. Falling back to a single-stream download, which may reduce quality.",
            file=sys.stderr,
        )
    if not can_merge and audio_codec:
        print(
            "Warning: ffmpeg not found. Saving the audio stream exactly as downloaded, which some players "
            "handle poorly (e.g. showing the wrong length). Install ffmpeg for a standard audio file.",
            file=sys.stderr,
        )

    ydl_opts: dict[str, object] = {
        "format": format_selector,
        "outtmpl": str(downloads_dir / output_template),
        "quiet": False,
        "noplaylist": True,
        "merge_output_format": "mp4" if can_merge and not audio_codec else None,
    }

    # Remove None for merge_output_format to avoid yt-dlp warning
    if ydl_opts["merge_output_format"] is None:
        del ydl_opts["merge_output_format"]

    # Save audio as a plain audio file (.m4a for AAC, .opus for Opus). A stream
    # already in the target codec is copied, not re-encoded, so it keeps exactly
    # the quality YouTube serves.
    if audio_codec and can_merge:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_codec,
                # Only used if a stream must be re-encoded (e.g. no AAC stream
                # for "audio"); high enough to keep the extra loss small.
                "preferredquality": "192",
            }
        ]

    # Use an installed JS runtime (node/deno/etc.) so all formats resolve and
    # YouTube doesn't fall back to SABR-only streams that return HTTP 403.
    js_runtimes = detect_js_runtimes()
    if js_runtimes:
        ydl_opts["js_runtimes"] = js_runtimes
    else:
        print(
            "Warning: no supported JavaScript runtime found (yt-dlp needs Node >= 22, "
            "Deno >= 2.3, or Bun >= 1.2.11). Some formats may be missing and downloads "
            "may fail with HTTP 403. Install one, e.g. `brew install node` or `nvm install 22`.",
            file=sys.stderr,
        )

    # Authenticate as a signed-in user for restricted videos that 403 otherwise.
    if cookies_from_browser:
        browser = cookies_from_browser.strip().lower()
        if browser not in SUPPORTED_COOKIE_BROWSERS:
            raise ValueError(
                f"Unsupported browser '{cookies_from_browser}'. "
                f"Choose one of: {', '.join(SUPPORTED_COOKIE_BROWSERS)}."
            )
        # yt-dlp expects a tuple: (browser, profile, keyring, container)
        ydl_opts["cookiesfrombrowser"] = (browser,)
    if cookies_file:
        ydl_opts["cookiefile"] = str(cookies_file)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    return _collect_downloaded_files(info)


def _collect_downloaded_files(info: dict[str, object]) -> list[Path]:
    filenames: list[Path] = []

    # Prefer "filepath": it is the final file after post-processing (e.g. audio
    # extracted to .opus), while "_filename" is the pre-processing name, which
    # yt-dlp deletes once the post-processor finishes.
    requested_downloads = info.get("requested_downloads") if isinstance(info, dict) else None
    if isinstance(requested_downloads, Iterable):
        for item in requested_downloads:
            if isinstance(item, dict):
                filename = item.get("filepath") or item.get("_filename")
                if isinstance(filename, str):
                    filenames.append(Path(filename))

    if not filenames and isinstance(info, dict):
        filename = info.get("filepath") or info.get("_filename")
        if isinstance(filename, str):
            filenames.append(Path(filename))

    return filenames

