#!/usr/bin/env python3

"""Download YouTube videos at a requested quality via yt-dlp."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from yt_dlp.utils import DownloadError

from yt_downloader.downloader import (
    AVAILABLE_QUALITIES,
    DEFAULT_OUTPUT_TEMPLATE,
    download_video,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a YouTube video with the desired quality using yt-dlp.",
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "quality",
        choices=AVAILABLE_QUALITIES,
        help="Desired video quality (e.g. 1080p, 720p, best)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT_TEMPLATE,
        help="Output template or directory (default: %(default)s)",
    )
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=Path("downloads"),
        help="Directory to save downloads (default: downloads)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help=(
            "Read login cookies from this browser to download restricted videos "
            "(age-restricted, members-only, private, premium, region-locked) that "
            "fail with HTTP 403. Example: --cookies-from-browser chrome"
        ),
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Path to a cookies.txt file (Netscape format) for authenticated downloads.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        download_video(
            args.url,
            args.quality,
            downloads_dir=args.downloads_dir,
            output_template=args.output,
            cookies_from_browser=args.cookies_from_browser,
            cookies_file=args.cookies,
        )
    except ValueError as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        return 2
    except DownloadError as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

