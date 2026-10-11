import pytest

from app.checks.class_type import check_class
from app.checks.name_address import check_name_address
from app.models import Application, Status
from tests.rules.helpers import mk

CLASS_CASES = [
    ("Kentucky Straight Bourbon Whiskey", "Kentucky Straight Bourbon Whisky", Status.MATCH),
    ("Bourbon Whiskey", "Straight Bourbon Whiskey", Status.DISAGREE),
    ("Straight Bourbon Whiskey", "Bourbon Whiskey", Status.DISAGREE),
    ("Vodka", "Bourbon Whiskey", Status.MISSING),
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
