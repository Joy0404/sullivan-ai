"""Inspect tracked Git history without displaying credential values or blob contents."""

from pathlib import PurePosixPath
import re
import subprocess
import sys

PATTERNS = (
    re.compile(rb"AIza[0-9A-Za-z_-]{35}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
)


def run(*args):
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)


def forbidden(name):
    path = PurePosixPath(name)
    return any(p in {".env", "__pycache__", ".pytest_cache"} for p in path.parts) or (
        path.name.startswith(".env.") and path.name != ".env.example"
    )


def verify():
    commits = run("rev-list", "--all").decode().splitlines()
    if not commits:
        raise SystemExit(
            "No commits to audit; original history cannot be inferred from a ZIP"
        )
    bad_paths = set()
    for commit in commits:
        for name in (
            run("ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0")
        ):
            if name and forbidden(name):
                bad_paths.add(name)
    objects = run("rev-list", "--objects", "--all").splitlines()
    blobs = 0
    bad_blobs = 0
    for item in objects:
        oid = item.split(b" ", 1)[0].decode()
        if run("cat-file", "-t", oid).strip() != b"blob":
            continue
        blobs += 1
        data = run("cat-file", "blob", oid)
        if any(pattern.search(data) for pattern in PATTERNS):
            bad_blobs += 1
    # Names are safe to display; suspected values and full blob bodies never are.
    for name in sorted(bad_paths):
        print("FAIL: excluded path in history: " + name)
    if bad_blobs:
        print(
            f"FAIL: {bad_blobs} blobs contain recognizable secret patterns; values suppressed"
        )
    if bad_paths or bad_blobs:
        raise SystemExit(1)
    print(
        f"PASS: {len(commits)} commits, {blobs} blobs; no .env/cache paths or recognizable secret patterns"
    )


if __name__ == "__main__":
    try:
        verify()
    except subprocess.CalledProcessError:
        raise SystemExit(
            "Git history inspection failed; no blob contents displayed"
        ) from None
