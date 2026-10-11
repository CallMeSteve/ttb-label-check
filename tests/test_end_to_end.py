import pytest

from tests.conftest import expected_cases, run_case

CASES = {k: v for k, v in expected_cases().items() if v["expect"]}


@pytest.mark.parametrize("name", sorted(CASES))
def test_rendered_case(name):
    got = {r.item: r for r in run_case(name).results}
    for item, want in CASES[name]["expect"].items():
        assert got[item].status.name == want, f"{item}: {got[item].reason}"


@pytest.mark.parametrize("name", sorted(CASES))
def test_no_false_alarms_on_other_rows(name):
    """A row the case does not target must not report a disagreement or a missing item."""
    got = {r.item: r for r in run_case(name).results}
    for item, r in got.items():
        if item not in CASES[name]["expect"]:
            assert r.status.name not in ("DISAGREE", "MISSING"), f"{item}: {r.reason}"


def test_every_row_has_a_crop_on_the_clean_label():
    for r in run_case("old_tom_clean").results:
        assert r.crops, r.item


def test_warning_row_always_asks_for_the_bold_check():
    for name in ("old_tom_clean", "warn_all_bold", "warn_header_regular"):
        row = next(r for r in run_case(name).results if r.item == "Government warning")
        assert row.confirm and "bold" in row.confirm


# Old Tom example values typed against pairs whose class is not whisky: the row must show the label's own
# class line and never the "Louisville, Kentucky" address line.
OTHER_CLASS = {"rum_35": "Rum", "beer_ml_only": "India Pale Ale", "beer_12oz_no_abv": "India Pale Ale",
               "table_wine_15": "Red Table Wine", "table_wine_no_abv": "Red Table Wine"}


@pytest.mark.parametrize("name,label_class", sorted(OTHER_CLASS.items()))
def test_class_row_never_picks_the_address_line(name, label_class):
    from app.models import Application
    from app.pipeline import check_label
    from tests.conftest import OUT

    spec = expected_cases()[name]
    app = dict(spec["application"], class_type="Kentucky Straight Bourbon Whisky")
    files = [(n, (OUT / n).read_bytes()) for n in spec["images"]]
    row = next(r for r in check_label(Application(**app), files).results if r.item == "Class or type")
    assert row.label_says == label_class and "Louisville" not in (row.label_says or "")
