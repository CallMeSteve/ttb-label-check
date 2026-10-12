import io

from fastapi.testclient import TestClient
from PIL import Image

import app.main as m
from app.batch import _safe
from app.models import FIELD_LIMIT, Application


def test_every_page_carries_the_browser_safety_settings():
    r = TestClient(m.app).get("/help")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "no-referrer"


def test_huge_dimension_picture_is_refused_before_it_is_opened():
    buf = io.BytesIO()
    Image.new("L", (9000, 9000)).save(buf, "PNG")  # small file, 81 million pixels
    r = TestClient(m.app).post("/check", data={"brand_name": "OLD TOM DISTILLERY"},
                               files=[("images", ("big.png", buf.getvalue(), "image/png"))])
    assert r.status_code == 400 and "60 megapixels" in r.text


def test_typed_values_are_capped():
    app = Application(class_type="WHISKY " * 1000)
    assert len(app.class_type) == FIELD_LIMIT


def test_health_does_not_run_the_reader_on_request():
    r = TestClient(m.app).get("/health?run=1")
    assert r.status_code == 200 and set(r.json()) == {"ok", "ocr_warm_up_seconds"}


def test_csv_cells_that_look_like_formulas_are_neutralised():
    for start in ("=", "+", "-", "@", "\t", "\r"):
        assert _safe(start + "SUM(A1)").startswith("'")
    assert _safe("OLD TOM") == "OLD TOM"
