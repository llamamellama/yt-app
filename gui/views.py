"""Blueprint handling the GUI routes."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from yt_downloader.downloader import download_video

bp = Blueprint("gui", __name__)


@bp.route("/", methods=["GET", "POST"])
def index() -> str:
    downloads_dir: Path = current_app.config["DOWNLOADS_DIR"]
    qualities = current_app.config["AVAILABLE_QUALITIES"]
    session_downloads: list[str] = current_app.config.setdefault("SESSION_DOWNLOADS", [])
    last_download: str | None = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        quality = request.form.get("quality", "best")

        if not url:
            flash("Please provide a YouTube URL.", "error")
        elif quality not in qualities:
            flash("Invalid quality selection.", "error")
        else:
            try:
                files = download_video(url, quality, downloads_dir=downloads_dir)
                if files:
                    last_download = files[-1].name
                    session_downloads.append(last_download)
                    flash(
                        f"Download complete: {last_download}",
                        "success",
                    )
                else:
                    flash("Download completed, but no file info was returned.", "error")
            except Exception as exc:  # yt_dlp can raise different exceptions
                flash(f"Download failed: {exc}", "error")

        return redirect(url_for("gui.index"))

    return render_template(
        "index.html",
        qualities=qualities,
        downloads=session_downloads,
        last_download=last_download,
    )

