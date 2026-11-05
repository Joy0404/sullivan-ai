import pytest


@pytest.fixture(autouse=True)
def isolated_usage_storage(monkeypatch, tmp_path):
    # Existing domain tests isolate adapters; dedicated local access tests enable the guard.
    monkeypatch.setenv("SULLIVAN_ROLE_AUTH", "0")
    monkeypatch.setenv("SULLIVAN_ACCOUNTS_DB", str(tmp_path / "accounts.sqlite"))
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path / "usage.sqlite"))
