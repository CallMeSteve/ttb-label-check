import pytest

from tests.conftest import expected_cases, run_case

DEGRADED = {k: v for k, v in expected_cases().items() if "base" in v}
RANK = {"MATCH": 0, "INFO": 0, "LOOK": 1, "DISAGREE": 2, "MISSING": 2}


@pytest.mark.parametrize("name", sorted(DEGRADED))
def test_no_false_matches(name):
    """A degraded picture may drop from Matches to Look at this. It never shows Matches
    on a row whose clean version is not Matches."""
    clean = {r.item: r for r in run_case(DEGRADED[name]["base"]).results}
    got = {r.item: r for r in run_case(name).results}
    for item, r in got.items():
        if item in clean and clean[item].status.name != "MATCH":
            assert r.status.name != "MATCH", f"{item}: clean {clean[item].status.name}, degraded MATCH"
