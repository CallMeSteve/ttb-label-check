import socket

import pytest
from fastapi.testclient import TestClient
from pytest_socket import SocketConnectBlockedError, enable_socket, socket_allow_hosts

from tests.conftest import OUT


@pytest.fixture
def offline():
    """Only loopback (the test client) is reachable. Everything else raises."""
    socket_allow_hosts(["127.0.0.1", "::1"], allow_unix_socket=True)
    yield
    enable_socket()


def test_full_check_with_the_network_off(offline):
    # Prove the block is on: a connection to a public address must fail.
    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("93.184.216.34", 80), timeout=1)

    from app.main import app

    files = [("images", (n, (OUT / n).read_bytes(), "image/png"))
             for n in ("old_tom_clean_front.png", "old_tom_clean_back.png")]
    data = dict(product_type="spirits", source="domestic", brand_name="OLD TOM DISTILLERY")
    with TestClient(app) as client:
        r = client.post("/check", data=data, files=files)
    assert r.status_code == 200
    assert "Nothing for you to look at" in r.text
    assert "Government warning" in r.text


def test_pages_load_nothing_from_other_hosts():
    import re
    from pathlib import Path

    html = "".join(p.read_text(encoding="utf-8") for p in Path("app/templates").glob("*.html"))
    css = Path("app/static/app.css").read_text(encoding="utf-8")
    loads = re.findall(r"""<(?:script|img|link|iframe)[^>]+(?:src|href)=["'](https?:)?//""", html)
    assert not loads
    assert "url(http" not in css and "@import" not in css
