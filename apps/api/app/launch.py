"""Drop privileges and run one worker. Production accounts require a persistent volume."""

import os
import sys

UID = 10001


def main():
    if os.geteuid() == 0:
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
