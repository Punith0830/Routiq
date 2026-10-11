import socket

import pytest


@pytest.mark.parametrize("host", ["127.0.0.1", "8.8.8.8"])
def test_application_connections_remain_blocked(host):
    with socket.socket() as sock:
        with pytest.raises(AssertionError, match="Network is forbidden"):
            sock.connect((host, 443))


def test_dns_is_blocked():
    with pytest.raises(AssertionError, match="Network is forbidden"):
        socket.getaddrinfo("api.openai.com", 443)
