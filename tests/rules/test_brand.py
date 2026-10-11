import pytest

from app.checks.brand import check_brand
from app.models import Application, Status
from tests.rules.helpers import mk

CASES = [
    ("STONE'S THROW", "Stone's Throw", Status.MATCH),
    ("Stone’s Throw", "STONES THROW", Status.MATCH),
    ("OLD TOM DISTILLERY", "OLD TOM DISTILLERY", Status.MATCH),
    ("OLD TOMS DISTILLERY", "OLD TOM DISTILLERY", Status.DISAGREE),
    ("OLD T0M DISTILLERY", "OLD TOM DISTILLERY", Status.LOOK),
    ("SOMETHING ELSE ENTIRELY", "OLD TOM DISTILLERY", Status.MISSING),
]


@pytest.mark.parametrize("label,app_brand,expected", CASES)
def test_brand(label, app_brand, expected):
    lines = mk([label, "Kentucky Straight Bourbon Whiskey"], heights={0: 90})
    r = check_brand(Application(brand_name=app_brand), lines)
    assert r.status is expected, r.reason


def test_case_difference_cites_the_rule():
    r = check_brand(Application(brand_name="Stone's Throw"), mk(["STONE'S THROW"]))
    assert "Capitals don't matter" in r.reason and r.rule == "27 CFR 5.52(d)"


def test_no_application_brand_is_informational():
    r = check_brand(Application(), mk(["small", "BIG BRAND"], heights={1: 80}))
    assert r.status is Status.INFO and r.label_says == "BIG BRAND"


def test_fanciful_name_partly_read_is_look_not_a_red_verdict():
    # Old Elk COLA on the live settings: the reader saw "ELK STRAIGHT BOURBON WHISKEY" for "9 YEAR STRAIGHT BOURBON WHISKEY".
    from app.checks.brand import check_fanciful
    r = check_fanciful(Application(brand_name="OLD ELK", fanciful_name="9 YEAR STRAIGHT BOURBON WHISKEY"),
                       mk(["OLD ELK", "ELK STRAIGHT BOURBON WHISKEY"]))
    assert r.status is Status.LOOK, r.reason
