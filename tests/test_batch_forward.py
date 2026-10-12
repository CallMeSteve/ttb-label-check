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


def test_opening_the_batch_page_does_not_wake_the_backend(forwarded):
    seen, client = forwarded
    r = client.get("/batch")
    assert r.status_code == 200 and 'id="batch-form"' in r.text
    assert seen == []


def test_warm_call_only_fires_after_files_are_picked():
    from pathlib import Path
    END = chr(10) + "  }" + chr(10)
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
    # The only warm call lives inside warmBatch, which add() calls once picked files are ready.
    assert js.count('fetch("/batch/warm")') == 1
    body = js.split("function warmBatch()")[1].split(END)[0]
    assert 'fetch("/batch/warm")' in body and "chosen.length" in body
    assert js.count("warmBatch()") == 2  # its definition and the call inside add()
    assert "warmBatch();" in js.split("function add(files)")[1].split(END)[0]


def test_big_photos_are_shrunk_before_upload_and_keep_their_names():
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "new File([b], f.name" in js and "UPLOAD_LIMIT" in js


def test_dot_dot_paths_and_warm_queries_are_not_passed_on(forwarded):
    seen, client = forwarded
    assert client.get("/batch/%2e%2e/health").status_code == 404
    assert seen == []
    client.get("/batch/warm?run=1")
    assert seen[0].url.path == "/health" and seen[0].url.query == b""
