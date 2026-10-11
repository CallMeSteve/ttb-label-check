import json
import sys
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "labels" / "all-test-cases"


def expected_cases() -> dict:
    return json.loads((OUT / "expected.json").read_text(encoding="utf-8"))


@cache
def run_case(name: str):
    from app.models import Application
    from app.pipeline import check_label

    spec = expected_cases()[name]
    files = [(n, (OUT / n).read_bytes()) for n in spec["images"]]
    return check_label(Application(**spec["application"]), files)
