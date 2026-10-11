from app.checks.warning import check_warning
from app.models import Application, Status
from tests.rules.helpers import WARN, mk, wrap

APP = Application()


def run(text):
    return check_warning(APP, mk(wrap(text)))


def test_exact():
    r = run(WARN)
    assert r.status is Status.MATCH and r.confirm


def test_title_case_header():
    r = run(WARN.replace("GOVERNMENT WARNING", "Government Warning"))
    assert r.status is Status.DISAGREE and "capital letters" in r.reason


def test_reworded():
    r = run(WARN.replace("may cause health problems", "may cause serious health problems"))
    assert r.status is Status.DISAGREE and "serious" in r.reason


def test_clause_two_removed():
    r = run(WARN.split(" (2)")[0])
    assert r.status is Status.DISAGREE and "Missing" in r.reason


def test_missing_colon_is_wording():
    r = run(WARN.replace("WARNING:", "WARNING"))
    assert r.status is Status.DISAGREE


def test_ocr_unsure_only():
    r = run(WARN.replace("pregnancy", "pregnancv".replace("v", "y")).replace("Surgeon", "Surgeon").replace("drive", "dr1ve"))
    assert r.status is Status.LOOK


def test_not_found():
    r = check_warning(APP, mk(["OLD TOM DISTILLERY", "750 mL"]))
    assert r.status is Status.MISSING


def test_extra_text_after_warning_is_ignored():
    r = check_warning(APP, mk(wrap(WARN) + ["BARCODE 12345 6789"]))
    assert r.status is Status.MATCH


def test_low_confidence_cannot_match():
    r = check_warning(APP, mk(wrap(WARN), conf=0.4))
    assert r.status is Status.LOOK
