import json
import socket
import threading
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    original_connect = socket.socket.connect
    original_socketpair = socket.socketpair
    ipc = threading.local()

    def internal_socketpair(*args, **kwargs):
        # Windows implements socketpair through a loopback connection. Permit
        # only that internal call, on this thread, while constructing the pair.
        ipc.creating_pair = True
        try:
            return original_socketpair(*args, **kwargs)
        finally:
            ipc.creating_pair = False

    def guarded_connect(sock, address):
        if getattr(ipc, "creating_pair", False) and isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return original_connect(sock, address)
        raise AssertionError("Network is forbidden in offline tests")

    def blocked(*args, **kwargs):
        raise AssertionError("Network is forbidden in offline tests")
    monkeypatch.setattr(socket, "socketpair", internal_socketpair)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket.socket, "sendto", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def config_data():
    path = Path(__file__).parents[1] / "app/config/routiq_chatbot.json"
    return json.loads(path.read_text(encoding="utf-8-sig"))
