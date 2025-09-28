"""Entry point for running the Flask GUI."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import socket
import threading
import time
import webbrowser

from gui import create_app


def main() -> None:
    downloads_path = Path(os.environ.get("DOWNLOADS_DIR", "downloads"))
    port = int(os.environ.get("PORT", 5001))
    app = create_app(downloads_path)

    def _try_open_url(url: str) -> bool:
        try:
            if webbrowser.open_new(url):
                return True
        except Exception:
            pass

        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["/usr/bin/open", url], check=False)
                return True
            if system == "Windows":
                try:
                    os.startfile(url)  # type: ignore[attr-defined]
                    return True
                except Exception:
                    subprocess.run(["cmd", "/c", "start", "", url], check=False, shell=True)
                    return True
            # Linux/other
            subprocess.run(["xdg-open", url], check=False)
            return True
        except Exception:
            return False

    def open_browser_when_ready() -> None:
        deadline = time.time() + 20.0
        address = ("127.0.0.1", port)
        while time.time() < deadline:
            s = socket.socket()
            s.settimeout(0.5)
            try:
                s.connect(address)
                s.close()
                _try_open_url(f"http://127.0.0.1:{port}")
                return
            except Exception:
                time.sleep(0.5)
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        # Fallback: attempt to open even if we couldn't detect readiness
        _try_open_url(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()

