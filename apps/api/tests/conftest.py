import pytest
import socket


@pytest.fixture(autouse=True)
def fixture_host_resolution(monkeypatch):
    """Fixture URLs are metadata; unit tests must not wait for public DNS.

    Host-validation tests may still override the resolver explicitly, and all
    literal/private/unlisted addresses retain the ordinary validation path.
    """
    resolve = socket.getaddrinfo

    def fixture(host, *args, **kwargs):
        if host in {'www.youtube.com', 'youtube.com', 'youtu.be', 'example.com'}:
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', 0))]
        return resolve(host, *args, **kwargs)

    monkeypatch.setattr(socket, 'getaddrinfo', fixture)


@pytest.fixture(autouse=True)
def isolated_usage_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("SULLIVAN_PRODUCTION", "0")
    for name in ("SULLIVAN_PUBLIC_URL", "SULLIVAN_EXTENSION_CLIENTS", "SULLIVAN_EXTENSION_ORIGINS", "SULLIVAN_MIN_EXTENSION_VERSION", "SULLIVAN_SIGNUP_INVITE", "SULLIVAN_SIGNUP_ENABLED", "SULLIVAN_PERSISTENT_STORAGE", "WEB_CONCURRENCY"):
        monkeypatch.delenv(name, raising=False)
    # Existing domain tests isolate adapters; dedicated local access tests enable the guard.
    monkeypatch.setenv("SULLIVAN_ROLE_AUTH", "0")
    monkeypatch.setenv("SULLIVAN_ACCOUNTS_DB", str(tmp_path / "accounts.sqlite"))
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    monkeypatch.setenv("DEMO_USAGE_DB", str(tmp_path / "usage.sqlite"))
