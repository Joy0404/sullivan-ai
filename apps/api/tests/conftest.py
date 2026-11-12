import pytest


@pytest.fixture(autouse=True)
def isolated_usage_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("SULLIVAN_PRODUCTION", "0")
    for name in ("SULLIVAN_PUBLIC_URL", "SULLIVAN_EXTENSION_CLIENTS", "SULLIVAN_EXTENSION_ORIGINS", "SULLIVAN_MIN_EXTENSION_VERSION", "SULLIVAN_SIGNUP_INVITE", "SULLIVAN_PERSISTENT_STORAGE", "WEB_CONCURRENCY"):
        monkeypatch.delenv(name, raising=False)
    # Existing domain tests isolate adapters; dedicated local access tests enable the guard.
    monkeypatch.setenv("SULLIVAN_ROLE_AUTH", "0")
    monkeypatch.setenv("SULLIVAN_ACCOUNTS_DB", str(tmp_path / "accounts.sqlite"))
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path / "usage.sqlite"))
