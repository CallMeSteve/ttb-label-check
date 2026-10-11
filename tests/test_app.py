import re
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import OUT


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def pic(name):
    return ("images", (name, (OUT / name).read_bytes(), "image/png"))


FORM = dict(product_type="spirits", source="domestic", brand_name="OLD TOM DISTILLERY",
            class_type="Kentucky Straight Bourbon Whisky", alcohol_content="45", net_contents="750 mL")


def test_pages_load(client):
    for path in ("/", "/batch", "/help"):
        assert client.get(path).status_code == 200
    health = client.get("/healthz").json()
    assert health["ok"] and health["ocr_warm_up_seconds"] > 0


def test_single_check_clean(client):
    r = client.post("/check", data=FORM, files=[pic("old_tom_clean_front.png"), pic("old_tom_clean_back.png")])
    assert r.status_code == 200
    assert "Nothing for you to look at" in r.text
    assert "Checked in" in r.text and "Built by Abdullah Sarwar" in r.text
    assert r.text.count("data:image/png;base64") >= 5


def test_single_check_title_case_warning(client):
    r = client.post("/check", data=FORM, files=[pic("warn_title_case_front.png"), pic("warn_title_case_back.png")])
    assert "1 thing to look at" in r.text
    assert "capital letters" in r.text


def test_missing_brand(client):
    r = client.post("/check", data={**FORM, "brand_name": ""}, files=[pic("old_tom_clean_front.png")])
    assert r.status_code == 400 and "Type the brand name from the application." in r.text


def test_wrong_file_type(client):
    r = client.post("/check", data=FORM, files=[("images", ("notes.docx", b"x", "application/octet-stream"))])
    assert "That file is a .docx. Use a JPG, PNG, or WEBP picture of the label." in r.text


def test_too_many_pictures(client):
    files = [pic("old_tom_clean_front.png")] * 5
    r = client.post("/check", data=FORM, files=files)
    assert "Up to 4 pictures per label" in r.text


def test_too_large(client):
    big = ("images", ("big.png", b"0" * (16 * 1024 * 1024), "image/png"))
    r = client.post("/check", data=FORM, files=[big])
    assert "too large (16 MB)" in r.text


def test_unreadable_picture(client):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (600, 600), "white").save(buf, "PNG")
    r = client.post("/check", data=FORM, files=[("images", ("blank.png", buf.getvalue(), "image/png"))])
    assert "read this picture" in r.text


def test_batch_without_spreadsheet(client, monkeypatch):
    monkeypatch.setenv("BATCH_WORKERS", "2")
    names = ["old_tom_clean_front.png", "old_tom_clean_back.png", "warn_missing_front.png", "warn_missing_back.png"]
    # Two applications: A1 (front+back) and B1 (front+back) via the _front/_back naming.
    files = [("images", (f"A1_{n.split('_')[-1]}", (OUT / n).read_bytes(), "image/png")) for n in names[:2]]
    files += [("images", (f"B1_{n.split('_')[-1]}", (OUT / n).read_bytes(), "image/png")) for n in names[2:]]
    r = client.post("/batch", data={"product_type": "spirits", "source": "domestic"}, files=files, follow_redirects=False)
    assert r.status_code == 303
    url = r.headers["location"]
    job_id = url.rsplit("/", 1)[1]
    for _ in range(120):
        data = client.get(f"/batch/{job_id}.json").json()
        if data["finished"]:
            break
        time.sleep(1)
    assert data["finished"] and data["total"] == 2
    assert data["notes"][0] == "4 pictures, 2 applications."
    by_id = {i["id"]: i for i in data["items"]}
    assert by_id["A1"]["looks"] == 0
    assert by_id["B1"]["looks"] >= 1
    assert "Nothing for you to look at" in client.get(f"{url}/item/1").text
    csv_text = client.get(f"{url}.csv").text
    assert "Government warning status" in csv_text and "Not on the label" in csv_text
    assert re.search(r"\d+ of 2 done", client.get(url).text)


def test_unknown_batch(client):
    assert client.get("/batch/nope").status_code == 404
    assert "isn't here" in client.get("/batch/nope").text


def test_health_alias(client):
    assert client.get("/health").json()["ok"] is True


def test_slow_check_returns_503_with_plain_message(client, monkeypatch):
    import app.main as m

    monkeypatch.setattr(m, "TIME_LIMIT", 0.05)
    monkeypatch.setattr(m, "check_label", lambda *a: time.sleep(0.5))
    r = client.post("/check", data=FORM, files=[pic("old_tom_clean_front.png")])
    assert r.status_code == 503 and "taking too long" in r.text
