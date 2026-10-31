"""Prepare the attached data directory, drop privileges, and exec the web server."""

import os
from pathlib import Path
import sys

UID = 10001


def main():
    if os.geteuid() == 0:
        # A runtime disk can hide ownership assigned in the Docker image.
        # Change only its root directory; never recursively follow stored paths.
        data_dir = Path(os.getenv("DEMO_DATA_DIR", "/var/data"))
        if os.getenv("RENDER") == "true" and os.path.ismount(data_dir):
            os.chown(data_dir, UID, UID)
        os.setgroups([])
        os.setgid(UID)
        os.setuid(UID)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.getenv("PORT", "10000"),
            "--workers",
            "1",
            "--no-proxy-headers",
            "--no-access-log",
        ],
    )


if __name__ == "__main__":
    main()
