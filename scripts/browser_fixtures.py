"""Network-independent DNS boundary for disposable browser fixtures.

These hosts are fixture metadata, never live playback/provider acceptance.
Localhost, literal/private addresses and every other host use the real resolver.
"""
from contextlib import contextmanager
from functools import wraps
import socket
from unittest.mock import patch


@contextmanager
def fixture_video_dns():
    resolve = socket.getaddrinfo

    def fixture(host, *args, **kwargs):
        if host in {'www.youtube.com', 'youtube.com', 'youtu.be', 'example.com'}:
            return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', 0))]
        return resolve(host, *args, **kwargs)

    with patch.object(socket, 'getaddrinfo', side_effect=fixture):
        yield


def offline_video_fixtures(function):
    @wraps(function)
    def run(*args, **kwargs):
        with fixture_video_dns():
            return function(*args, **kwargs)
    return run
