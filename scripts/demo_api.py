"""Load the deterministic lecture fixture into a running local API."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API = "http://localhost:8000"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(
        f"{API}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req) as response:
        return json.load(response)


def main() -> None:
    fixture = json.loads(
        (ROOT / "packages" / "test-fixtures" / "lecture_analysis_demo.json").read_text(
            encoding="utf-8"
        )
    )
    session = request("POST", "/v1/lectures", fixture["lecture"])
    session_id = session["session_id"]
    snapshot = request(
        "POST",
        f"/v1/lectures/{session_id}/analysis",
        fixture["analysis"],
    )
    navigation = request(
        "POST",
        f"/v1/lectures/{session_id}/navigate",
        {"command": "밑줄 문장 읽어줘", "current_sentence_id": None},
    )
    print(
        json.dumps(
            {"snapshot": snapshot, "navigation": navigation},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
