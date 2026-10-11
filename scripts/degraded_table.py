"""Print the per-degradation results as a markdown table (for APPROACH.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.conftest import expected_cases, run_case  # noqa: E402

cases = expected_cases()
rows = {}
for name, spec in cases.items():
    if "base" in spec:
        kind = name[len(spec["base"]) + 1:]
        res = {r.item: r.status.name for r in run_case(name).results}
        clean = {r.item: r.status.name for r in run_case(spec["base"]).results}
        same = sum(1 for k, v in clean.items() if res.get(k) == v)
        rows.setdefault(kind, []).append(f"{spec['base']}: {same} of {len(clean)} rows unchanged")
print("| Degradation | Result |\n|---|---|")
for kind, vals in rows.items():
    print(f"| {kind} | " + "; ".join(vals) + " |")
n_rows = sum(len(v["expect"]) for v in cases.values() if "base" not in v)
n_cases = sum(1 for v in cases.values() if "base" not in v)
print(f"\n{n_cases} rendered cases, {n_rows} targeted rows")
