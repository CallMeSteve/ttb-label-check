import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as m


@pytest.fixture
def forwarded(monkeypatch):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST":
            return httpx.Response(303, headers={"location": "/batch/abc123"})
        if request.url.path == "/batch/abc123.json":
            return httpx.Response(200, json={"done": 2, "total": 2, "finished": True})
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)

    monkeypatch.setenv("BATCH_BACKEND_URL", "https://batch.internal/")
    monkeypatch.setattr(m, "_backend_transport", httpx.MockTransport(handler))
    return seen, TestClient(m.app)


def test_post_batch_is_forwarded_with_its_files(forwarded):
    seen, client = forwarded
    r = client.post("/batch", data={"product_type": "spirits"},
                    files=[("images", ("A1_front.png", b"png-bytes", "image/png"))], follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/batch/abc123"
    sent = seen[0]
    assert sent.method == "POST" and str(sent.url) == "https://batch.internal/batch"
    assert sent.headers["content-type"].startswith("multipart/form-data")
    assert b"A1_front.png" in sent.content and b"png-bytes" in sent.content


def test_status_json_is_passed_through(forwarded):
    seen, client = forwarded
    r = client.get("/batch/abc123.json?x=1")
    assert r.status_code == 200 and r.json() == {"done": 2, "total": 2, "finished": True}
    assert str(seen[0].url) == "https://batch.internal/batch/abc123.json?x=1"


def test_warm_goes_to_the_backend_health_check(forwarded):
    seen, client = forwarded
    assert client.get("/batch/warm").json() == {"ok": True}
    assert seen[0].url.path == "/health"


def test_other_pages_are_not_forwarded(forwarded):
    seen, client = forwarded
    assert client.get("/help").status_code == 200
    assert seen == []


def test_unreachable_backend_gives_a_plain_message(monkeypatch):
    def boom(request):
        raise httpx.ConnectError("down")

    monkeypatch.setenv("BATCH_BACKEND_URL", "https://batch.internal")
    monkeypatch.setattr(m, "_backend_transport", httpx.MockTransport(boom))
    r = TestClient(m.app).get("/batch/abc.json")
    assert r.status_code == 502 and "Try again" in r.text


def test_unset_means_everything_runs_here(monkeypatch):
    monkeypatch.delenv("BATCH_BACKEND_URL", raising=False)
    client = TestClient(m.app)
    assert client.get("/batch/warm").json() == {"ok": True}
    assert client.get("/batch").status_code == 200
    assert client.get("/batch/nope").status_code == 404
