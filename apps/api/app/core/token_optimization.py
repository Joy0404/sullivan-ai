"""Explicit research route; production always starts on the accepted baseline.

There is intentionally no environment switch or automatic promotion. A paired
benchmark may opt in within its own async context, without affecting students.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_route: ContextVar[str] = ContextVar("token_optimization_route", default="baseline")


def current_route() -> str:
    return _route.get()


@contextmanager
def experimental_route():
    token = _route.set("experimental")
    try:
        yield
    finally:
        _route.reset(token)
