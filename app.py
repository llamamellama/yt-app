"""Entry point for running the Flask GUI."""

from __future__ import annotations

import os
from pathlib import Path

from gui import create_app


def main() -> None:
    downloads_path = Path(os.environ.get("DOWNLOADS_DIR", "downloads"))
    port = int(os.environ.get("PORT", 5001))
    app = create_app(downloads_path)
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()

