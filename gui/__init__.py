"""Flask application factory for the YouTube downloader GUI."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from yt_downloader.downloader import AVAILABLE_QUALITIES


def create_app(downloads_dir: Path | None = None) -> Flask:
    app = Flask(__name__)

    secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")
    app.secret_key = secret_key

    if downloads_dir is None:
        downloads_dir = Path("downloads")

    app.config["DOWNLOADS_DIR"] = downloads_dir
    app.config["AVAILABLE_QUALITIES"] = AVAILABLE_QUALITIES
    app.config["SESSION_DOWNLOADS"] = []  # list[str] of filenames for current run

    from .views import bp

    app.register_blueprint(bp)

    return app

