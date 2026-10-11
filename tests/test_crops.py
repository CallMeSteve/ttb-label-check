"""Every picture shown next to a result must point at the words that row is about."""
import json
from pathlib import Path

import pytest
from PIL import Image

from app.checks.run import run_checks
from app.crops import _clusters
from app.models import Application, Box
from app.ocr import read_lines

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "labels/all-test-cases/expected.json").read_text(encoding="utf-8"))
ALCOHOL_WORDS = ("%", "PROOF", "ALC", "VOL", "ABV")


def test_far_apart_lines_get_separate_pictures():
    a, b = Box(0, 10, 10, 200, 40), Box(0, 10, 600, 200, 630)
    assert len(_clusters([a, b])) == 2
    c = Box(0, 10, 45, 200, 75)
    assert len(_clusters([a, c])) == 1


@pytest.mark.parametrize("name", sorted(CASES))
def test_alcohol_picture_points_at_the_alcohol_statement(name):
    spec = CASES[name]
    lines = []
    for i, f in enumerate(spec["images"]):
        lines += read_lines(Image.open(ROOT / "labels/all-test-cases" / f).convert("RGB"), i)
    by_box = {ln.box: ln for ln in lines}
    for r in run_checks(Application(**spec["application"]), lines):
        if r.item != "Alcohol content" or not r.evidence:
            continue
        cited = [by_box[b].text.upper() for b in r.evidence if b in by_box]
        stray = [c for c in cited if not any(w in c for w in ALCOHOL_WORDS)]
        # A class-minimum finding also points at the class word ("Rum"), which is the evidence for it.
        if "must be at least" in r.reason or "Table wine" in r.reason:
            stray = stray[1:]
        assert not stray, f"alcohol picture also points at {stray}"
