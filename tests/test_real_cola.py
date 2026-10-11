"""Five TTB-approved labels. A rule failure on any of them is a false alarm."""
import json
from functools import cache
from pathlib import Path

import pytest

from app.models import Application
from app.pipeline import check_label

D = Path(__file__).resolve().parent.parent / "labels" / "real-cola"
CASES = json.loads((D / "cases.json").read_text(encoding="utf-8"))


@cache
def rows(name):
    c = CASES[name]
    files = [(f, (D / f).read_bytes()) for f in c["images"]]
    return check_label(Application(**c["application"]), files).results


@pytest.mark.parametrize("name", sorted(CASES))
def test_no_false_rule_failures(name):
    bad = [(r.item, r.status_text, r.reason) for r in rows(name)
           if r.status_text in ("Doesn't follow the rule", "Label and application disagree")]
    assert not bad, bad


def test_all_caps_warning_body_is_accepted():
    row = next(r for r in rows("old-elk") if r.item == "Government warning")
    assert row.status.name == "MATCH"


def test_blown_in_net_contents_wording():
    row = next(r for r in rows("old-elk") if r.item == "Net contents")
    assert row.status.name == "LOOK" and "molded into the glass" in row.reason
