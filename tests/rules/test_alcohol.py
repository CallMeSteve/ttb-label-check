import pytest

from app.checks.alcohol import check_alcohol
from app.models import Application, Status
from tests.rules.helpers import mk

S = "spirits"
CASES = [
    # product, label lines, app alcohol, expected status, text expected in reason
    (S, ["Kentucky Straight Bourbon Whiskey", "45% Alc./Vol. (90 Proof)"], "", Status.MATCH, ""),
    (S, ["Kentucky Straight Bourbon Whiskey", "45% Alc./Vol. (80 Proof)"], "", Status.DISAGREE, "should be 90 proof"),
    (S, ["Bourbon Whiskey", "45% Alc./Vol."], "40", Status.DISAGREE, "Application says 40%, label says 45%"),
    (S, ["Bourbon Whiskey", "45% Alc./Vol."], "45%", Status.MATCH, ""),
    (S, ["Bourbon Whiskey", "45% ABV"], "", Status.LOOK, "ABV"),
    (S, ["Rum", "35% alc/vol"], "", Status.DISAGREE, "at least 40%"),
    (S, ["Rum", "40% alc/vol"], "", Status.MATCH, ""),
    (S, ["Flavored Vodka", "30% alc/vol"], "", Status.MATCH, ""),
    (S, ["Tequila 100% Agave", "40% Alc./Vol."], "", Status.MATCH, ""),
    (S, ["Bourbon Whiskey"], "", Status.MISSING, ""),
    ("wine", ["Red Table Wine", "Alc. 15% by vol."], "", Status.DISAGREE, "14%"),
    ("wine", ["Red Table Wine"], "", Status.MATCH, "Not required"),
    ("wine", ["Cabernet"], "", Status.LOOK, "over 14%"),
    ("malt", ["Pale Ale"], "", Status.MATCH, "Not required"),
]


@pytest.mark.parametrize("pt,texts,app_val,status,words", CASES)
def test_alcohol(pt, texts, app_val, status, words):
    r = check_alcohol(Application(product_type=pt, alcohol_content=app_val), mk(texts))
    assert r.status is status, r.reason
    assert words in r.reason
