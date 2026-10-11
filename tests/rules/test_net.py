import pytest

from app.checks.net_contents import check_net
from app.models import Application, Status
from tests.rules.helpers import mk

CASES = [
    ("spirits", ["750 mL"], "", Status.MATCH, ""),
    ("spirits", ["700 mL"], "", Status.MATCH, ""),
    ("spirits", ["1 L"], "", Status.MATCH, ""),
    ("spirits", ["750 mL (25.4 FL OZ)"], "", Status.MATCH, ""),
    ("spirits", ["600 mL"], "", Status.DISAGREE, "not an approved bottle size"),
    ("spirits", ["25.4 FL OZ"], "", Status.DISAGREE, "metric"),
    ("spirits", ["Bourbon"], "", Status.LOOK, "molded"),
    ("spirits", ["750 mL"], "700 mL", Status.DISAGREE, "Application says"),
    ("spirits", ["750 mL"], "75 cl", Status.MATCH, ""),
    ("malt", ["355 mL"], "", Status.DISAGREE, "fluid ounces"),
    ("malt", ["12 FL. OZ."], "", Status.MATCH, ""),
    ("malt", ["12 FL. OZ. (355 mL)"], "12 fl oz", Status.MATCH, ""),
    ("wine", ["750 mL"], "", Status.MATCH, ""),
    ("wine", ["600 mL"], "", Status.MATCH, ""),
    ("wine", ["650 mL"], "", Status.DISAGREE, "wine"),
]


@pytest.mark.parametrize("pt,texts,app_val,status,words", CASES)
def test_net(pt, texts, app_val, status, words):
    r = check_net(Application(product_type=pt, net_contents=app_val), mk(texts))
    assert r.status is status, r.reason
    assert words in r.reason
