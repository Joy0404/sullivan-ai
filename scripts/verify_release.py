"""Inspect a release ZIP without printing any suspected secret values."""

from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

SECRET_PATTERNS = (
    re.compile(rb"AIza[0-9A-Za-z_-]{35}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
)


def verify(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        entries = [info for info in archive.infolist() if not info.is_dir()]
        issues = []
        for entry in entries:
            parts = PurePosixPath(entry.filename).parts
            name = parts[-1]
            if PurePosixPath(entry.filename).is_absolute() or ".." in parts:
                issues.append((entry.filename, "unsafe archive path"))
            if any(
                p
                in {
                    ".git",
                    "__pycache__",
                    ".pytest_cache",
                    ".venv",
                    "node_modules",
                    ".DS_Store",
                }
                for p in parts
            ):
                issues.append((entry.filename, "excluded artifact"))
            if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
                issues.append((entry.filename, "environment file"))
            if name.endswith((".pyc", ".db", ".sqlite", ".sqlite-wal", ".sqlite-shm")):
                issues.append((entry.filename, "runtime artifact"))
            data = archive.read(entry)
            if any(pattern.search(data) for pattern in SECRET_PATTERNS):
                issues.append((entry.filename, "possible secret; value suppressed"))
            if "/apps/web/" in "/" + entry.filename and name.endswith(
                (".js", ".html", ".css")
            ):
                if b"localhost" in data or b":8000" in data:
                    issues.append((entry.filename, "non-relative development address"))
        if issues:
            for filename, reason in issues:
                print(f"FAIL: {filename}: {reason}")
            raise SystemExit(1)
        print(
            f"PASS: {len(entries)} files; no environment files, caches, runtime DBs or recognizable secret patterns; web addresses verified"
        )
        return len(entries)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/verify_release.py RELEASE.zip")
    verify(Path(sys.argv[1]))
