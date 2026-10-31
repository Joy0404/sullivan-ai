"""Credential-free acceptance checks for a running Sullivan AI deployment."""

from __future__ import annotations

import argparse
import json
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def verify(base: str, wait_seconds: int = 60) -> None:
    def fetch(path, body=None):
        request = Request(
            base + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, response.read()
        except HTTPError as error:
            # Keep server response bodies out of logs.
            return error.code, b""

    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            status, data = fetch("/health")
            assert status == 200 and json.loads(data)["status"] == "ok"
            break
        except Exception:
            if time.monotonic() >= deadline:
                raise RuntimeError("Health check did not become ready") from None
            time.sleep(1)
    assert fetch("/")[0] == 200
    status, javascript = fetch("/app.js")
    assert (
        status == 200 and b"localhost" not in javascript and b":8000" not in javascript
    )
    assert b"gemini_api_key" not in javascript
    assert fetch("/styles.css")[0] == 200
    for path in ["/.env", "/.git/config", "/v1/unknown"]:
        assert fetch(path)[0] == 404
    status, data = fetch("/v1/lectures", {"title": "Deployment sample verification"})
    assert status == 201
    sid = json.loads(data)["session_id"]
    status, data = fetch(f"/v1/lectures/{sid}/demo-analysis", {})
    assert status == 200
    snapshot = json.loads(data)
    assert snapshot["safe_description_count"] > 0 and snapshot["held_count"] > 0
    # No consent or code is supplied: these calls must never reach Gemini.
    status, _ = fetch(
        f"/v1/lectures/{sid}/video-link",
        {
            "url": "https://www.youtube.com/watch?v=R0dqsl3Vgns",
            "rights_confirmed": True,
        },
    )
    assert status == 400
    status, _ = fetch(
        f"/v1/lectures/{sid}/agent-turn", {"message": "verify consent gate"}
    )
    # An unconfigured agent returns 503 before any provider call; a configured
    # agent must reject missing consent with 400. Both are fail-closed states.
    assert status in {400, 503}
    fetch(f"/v1/lectures/{sid}/end", {})
    print(
        "PASS: health, web assets, same-origin API, secret-path blocking, sample analysis and consent gates"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Allow HTTP for a local container test",
    )
    args = parser.parse_args()
    parts = urlsplit(args.url)
    if (
        (
            parts.scheme != "https"
            and not (
                args.allow_local
                and parts.scheme == "http"
                and parts.hostname in {"127.0.0.1", "localhost"}
            )
        )
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or parts.path not in {"", "/"}
    ):
        parser.error(
            "Use a service root HTTPS URL, or explicit --allow-local for loopback HTTP"
        )
    try:
        verify(args.url.rstrip("/"))
    except Exception:
        raise SystemExit(
            "FAIL: service acceptance check failed; credentials and response details suppressed"
        ) from None
