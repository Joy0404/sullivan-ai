"""Content-free, per-attempt Gemini usage records at the provider boundary.

``metered_post`` preserves provider totals (cache/thought counts are subsets,
not extra charges to add). Missing counters stay null, including failed calls.
The dedicated JSON logger never receives request/response bodies or exceptions.
``capture_usage`` is a task-local collector for reproducible measurement runs.
"""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal, TypeVar
from uuid import UUID, uuid4

import httpx

Stage = Literal["analysis", "verification", "question"]
Route = Literal["baseline", "experimental"]
ProviderAPI = Literal["generate_content", "interactions"]
T = TypeVar("T")

logger = logging.getLogger("sullivan.gemini.usage")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False
_collector: ContextVar[list[dict[str, Any]] | None] = ContextVar("gemini_usage_collector", default=None)


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cache_tokens: int | None = None
    total_tokens: int | None = None

    @property
    def measurement(self) -> str:
        return "measured" if any(value is not None for value in asdict(self).values()) else "미측정"


def parse_usage(body: Any, *, provider_api: ProviderAPI) -> TokenUsage:
    """Read only documented provider counters; never infer missing totals."""
    if not isinstance(body, Mapping):
        return TokenUsage()
    if provider_api == "generate_content":
        usage = body.get("usageMetadata")
        names = ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "cachedContentTokenCount", "totalTokenCount")
    else:
        usage = body.get("usage")
        names = ("total_input_tokens", "total_output_tokens", "total_thought_tokens", "total_cached_tokens", "total_tokens")
    if not isinstance(usage, Mapping):
        return TokenUsage()
    # bool is an int subclass, but is not a provider token count.
    values = [value if type(value) is int and value >= 0 else None for value in (usage.get(name) for name in names)]
    return TokenUsage(*values)


def new_operation_id() -> str:
    """Generate an ID unrelated to users, lecture IDs, URLs, or media."""
    return uuid4().hex


@contextmanager
def capture_usage() -> Iterator[list[dict[str, Any]]]:
    """Collect allowlisted records for this async context without altering calls."""
    records: list[dict[str, Any]] = []
    token = _collector.set(records)
    try:
        yield records
    finally:
        _collector.reset(token)


async def metered_post(
    client: httpx.AsyncClient,
    url: str,
    *,
    model: str,
    stage: Stage,
    provider_api: ProviderAPI,
    parse_response: Callable[[Any], T],
    operation_id: str | None = None,
    attempt: int = 1,
    retry: bool | None = None,
    route: Route = "baseline",
    **post_kwargs: Any,
) -> T:
    """POST once and record even HTTP, transport, JSON, or parser failures.

    The caller's synchronous ``parse_response(body)`` belongs inside the measured
    attempt so invalid model JSON is recorded as failure despite HTTP 200.
    Reuse ``new_operation_id()`` across stages/fallbacks. ``attempt`` numbers
    requests within a stage; planned additional audits use ``retry=False``.
    This helper does not retry or change generation settings.
    """
    # Only random IDs and fixed enums may enter the metric record. Invalid
    # metadata is replaced locally; it never affects the provider request.
    try:
        safe_operation_id = UUID(operation_id).hex if operation_id else new_operation_id()
    except (ValueError, AttributeError):
        safe_operation_id = new_operation_id()
    record: dict[str, Any] = {
        "event": "gemini_usage",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "operation_id": safe_operation_id,
        "request_id": uuid4().hex,
        "stage": stage if stage in {"analysis", "verification", "question"} else "analysis",
        "model": model if re.fullmatch(r"(?:models/)?gemini-[A-Za-z0-9._-]{1,110}", model) else "unknown",
        "provider_api": provider_api if provider_api in {"generate_content", "interactions"} else "generate_content",
        "route": route if route in {"baseline", "experimental"} else "baseline",
        "attempt": attempt if type(attempt) is int and attempt > 0 else 1,
        "success": False,
    }
    # A planned text-material audit is an additional request, not a retry.
    record["retry"] = retry if type(retry) is bool else record["attempt"] > 1
    usage = TokenUsage()
    try:
        response = await client.post(url, **post_kwargs)
        # Error responses sometimes include usage. Read only its counters,
        # retaining the original HTTP error if the body is not valid JSON.
        try:
            body = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        usage = parse_usage(body, provider_api=provider_api)
        response.raise_for_status()
        result = parse_response(body)
        record["success"] = True
        return result
    finally:
        record.update(asdict(usage))
        record["measurement"] = usage.measurement
        captured = _collector.get()
        if captured is not None:
            captured.append(record.copy())
        logger.info(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
