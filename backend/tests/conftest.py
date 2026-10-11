import socket
import pytest


@pytest.fixture(autouse=True)
def no_external_connections(monkeypatch):
    original_connect = socket.socket.connect
    def restricted(sock, address):
        # Windows asyncio builds a loopback socketpair for its own event loop.
        if isinstance(address, tuple) and address[0] in {'127.0.0.1', '::1'}:
            return original_connect(sock, address)
        raise AssertionError('External network calls are forbidden in backend tests')
    def denied(*args, **kwargs):
        raise AssertionError('External network calls are forbidden in backend tests')
    monkeypatch.setattr(socket.socket, 'connect', restricted)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)
