"""Run every rendered case through OCR and the checks; print rows that miss expected.json."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models import Application  # noqa: E402
from app.pipeline import check_label  # noqa: E402

OUT = ROOT / "labels" / "out"


def run_case(spec: dict):
    files = [(n, (OUT / n).read_bytes()) for n in spec["images"]]
    return check_label(Application(**spec["application"]), files)


def main() -> int:
    expected = json.loads((OUT / "expected.json").read_text(encoding="utf-8"))
    bad = 0
    for name, spec in expected.items():
        t = time.perf_counter()
        out = run_case(spec)
        got = {r.item: r for r in out.results}
        line = []
        for item, want in spec["expect"].items():
            r = got.get(item)
            have = r.status.name if r else "ABSENT"
            if have != want:
                bad += 1
                line.append(f"  {item}: want {want}, got {have}: {r.reason if r else ''}")
        print(f"{name:26s} {time.perf_counter() - t:5.2f}s " + ("OK" if not line else "FAIL"))
        for ln in line:
            print(ln)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
