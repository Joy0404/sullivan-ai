import pytest


@pytest.fixture(autouse=True)
def isolated_usage_storage(monkeypatch, tmp_path):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path / "usage.sqlite"))
