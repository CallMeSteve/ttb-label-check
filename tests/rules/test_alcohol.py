import pytest

from app.checks.alcohol import check_alcohol
from app.models import Application, Status
from tests.rules.helpers import mk

S = "spirits"
CASES = [
    # product, label lines, app alcohol, expected status, text expected in reason
    (S, ["Kentucky Straight Bourbon Whiskey", "45% Alc./Vol. (90 Proof)"], "", Status.MATCH, ""),
    (S, ["Bourbon Whiskey", "45% Alc./Vol. (80 Proof)"], "", Status.DISAGREE, "is 90 proof, but the label says 80 Proof"),
    (S, ["Bourbon Whiskey", "45% Alc./Vol."], "40", Status.DISAGREE, "Application says 40%, label says 45%"),
    (S, ["Bourbon Whiskey", "45% Alc./Vol."], "45%", Status.MATCH, ""),
    (S, ["Bourbon Whiskey", "45% ABV"], "", Status.LOOK, "ABV"),
    (S, ["Rum", "35% alc/vol"], "", Status.DISAGREE, "at least 40%"),
    (S, ["Rum", "40% alc/vol"], "", Status.MATCH, ""),
    (S, ["Flavored Vodka", "30% alc/vol"], "", Status.MATCH, ""),
    (S, ["Tequila 100% Agave", "40% Alc./Vol."], "", Status.MATCH, ""),
    # Found in the pre-submission review: the ingredient percent sat close enough to Alc./Vol. to be read as ABV.
    (S, ["CASA AZUL", "100% Agave", "Tequila", "40% Alc./Vol. (80 Proof)", "750 mL"], "40%", Status.MATCH, ""),
    # A liqueur named after its base spirit has no 40% class minimum.
    (S, ["Bourbon Cream Liqueur", "17% Alc./Vol. (34 Proof)"], "", Status.MATCH, ""),
    (S, ["Whiskey Cordial", "30% Alc./Vol."], "", Status.MATCH, ""),
    (S, ["Sloe Gin", "26% Alc./Vol."], "", Status.MATCH, ""),
    (S, ["Peppermint Schnapps", "30% Alc./Vol."], "", Status.MATCH, ""),
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


def test_label_contradiction_is_not_called_an_application_disagreement():
    app = Application(alcohol_content="45% Alc./Vol. (90 Proof)")
    r = check_alcohol(app, mk(["Bourbon Whiskey", "45% Alc./Vol. (80 Proof)"]))
    assert r.status_text == "Doesn't follow the rule"
    assert r.reason == "The label contradicts itself: 45% Alc./Vol. is 90 proof, but the label says 80 Proof."


def test_both_problems_keep_the_second_sentence():
    r = check_alcohol(Application(alcohol_content="40"), mk(["Bourbon Whiskey", "45% Alc./Vol. (80 Proof)"]))
    assert r.status_text == "Doesn't follow the rule" and "Application says 40%, label says 45%." in r.reason


def test_plain_application_mismatch_keeps_its_heading():
    r = check_alcohol(Application(alcohol_content="40"), mk(["Bourbon Whiskey", "45% Alc./Vol."]))
    assert r.status_text == "Label and application disagree"
