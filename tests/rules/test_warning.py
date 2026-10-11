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


def test_unread_colon_is_a_look_not_a_violation():
    r = run(WARN.replace("WARNING:", "WARNING"))
    assert r.status is Status.LOOK


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


def test_all_caps_body_is_legal():
    assert run(WARN.upper()).status is Status.MATCH


def test_ocr_noise_inside_words_is_a_look_not_a_violation():
    noisy = (WARN.replace("GOVERNMENT WARNING:", "GOVERNMENTWARNING:").replace("(1)", "[1)")
             .replace("operate", "opérate").replace("ability", "abiuty").replace("alcoholic", "alcohouc", 1))
    r = run(noisy)
    assert r.status is Status.LOOK, r.reason


def test_hyphenated_line_break_and_stray_lines_do_not_break_the_match():
    text = WARN.replace("Consumption", "Consump-\ntion").split("\n")
    lines = mk(wrap(text[0], 60) + wrap(text[1], 60)[:1] + ["www.responsibility.org"] + wrap(text[1], 60)[1:])
    assert check_warning(APP, lines).status is Status.MATCH
