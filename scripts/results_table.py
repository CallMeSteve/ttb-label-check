"""Write docs/results.md: every rendered case, what was expected, what the app returned. Failures included."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.conftest import expected_cases, run_case  # noqa: E402

lines = [
    "# Results on the test labels",
    "",
    "Every rendered case, what I expected, and what the app returned on this run. A row marked MISS is a failure.",
    "",
    "Known limit: the app does not decide whether GOVERNMENT WARNING: is bold and the rest is not. The warning row always "
    "asks the agent to confirm that by eye, so `warn_header_regular` and `warn_all_bold` are expected to say Matches on "
    "wording and capitals and are not flagged for weight.",
    "",
    "| Case | Row | Expected | Got | |",
    "|---|---|---|---|---|",
]
miss = 0
for name, spec in expected_cases().items():
    got = {r.item: r.status.name for r in run_case(name).results}
    if "base" in spec:
        clean = {r.item: r.status.name for r in run_case(spec["base"]).results}
        for item, status in clean.items():
            ok = got.get(item) == status
            miss += not ok
            lines.append(f"| {name} | {item} | {status} (same as clean) | {got.get(item)} | {'ok' if ok else 'MISS'} |")
        continue
    for item, want in spec["expect"].items():
        ok = got.get(item) == want
        miss += not ok
        lines.append(f"| {name} | {item} | {want} | {got.get(item)} | {'ok' if ok else 'MISS'} |")
lines += ["", f"{miss} rows missed.", ""]
(ROOT / "docs" / "results.md").write_text("\n".join(lines), encoding="utf-8")
print(f"{miss} rows missed")
