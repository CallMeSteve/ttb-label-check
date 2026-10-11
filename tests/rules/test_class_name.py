import pytest

from app.checks.class_type import check_class
from app.checks.name_address import check_name_address
from app.models import Application, Status
from tests.rules.helpers import mk

CLASS_CASES = [
    ("Kentucky Straight Bourbon Whiskey", "Kentucky Straight Bourbon Whisky", Status.MATCH),
    ("Bourbon Whiskey", "Straight Bourbon Whiskey", Status.DISAGREE),
    ("Straight Bourbon Whiskey", "Bourbon Whiskey", Status.DISAGREE),
    ("Vodka", "Bourbon Whiskey", Status.DISAGREE),
]


@pytest.mark.parametrize("label,app_val,status", CLASS_CASES)
def test_class(label, app_val, status):
    r = check_class(Application(class_type=app_val), mk(["OLD TOM", label]))
    assert r.status is status, r.reason


def test_dropped_straight_explains_legal_meaning():
    r = check_class(Application(class_type="Straight Bourbon Whiskey"), mk(["Bourbon Whiskey"]))
    assert "Straight' has a legal meaning" in r.reason


def test_class_blank_is_informational():
    r = check_class(Application(), mk(["Bourbon Whiskey"]))
    assert r.status is Status.INFO


def test_name_address_present():
    r = check_name_address(Application(), mk(["Distilled and bottled by Old Tom", "Louisville, KY"]))
    assert r.status is Status.MATCH


def test_name_address_missing():
    assert check_name_address(Application(), mk(["Old Tom"])).status is Status.MISSING


def test_import_without_importer():
    r = check_name_address(Application(source="imported"), mk(["Bottled by Old Tom", "Dublin"]))
    assert r.status is Status.LOOK and "Imported by" in r.reason


ADDRESS = ["Distilled and bottled by Old Tom Distillery", "Louisville, Kentucky"]
EXAMPLE_CLASS = "Kentucky Straight Bourbon Whisky"


def test_address_line_is_never_the_class():
    r = check_class(Application(class_type=EXAMPLE_CLASS), mk(["OLD TOM", "Rum"] + ADDRESS))
    assert r.status is Status.DISAGREE and r.label_says == "Rum"


def test_no_class_on_label_asks_for_a_look_not_a_disagreement():
    r = check_class(Application(class_type=EXAMPLE_CLASS), mk(["OLD TOM", "750 mL"] + ADDRESS))
    assert r.status is Status.LOOK and "Couldn't find" in r.reason and r.label_says is None


def test_whisky_and_whiskey_are_equal():
    r = check_class(Application(class_type="Straight Bourbon Whisky"), mk(["Straight Bourbon Whiskey"]))
    assert r.status is Status.MATCH
