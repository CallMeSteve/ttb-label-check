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

BEFORE = {
    "old-elk": "Government warning: Doesn't follow the rule. Net contents: Look at this.",
    "jeffersons-ocean": "Class or type: disagree (picked the 'BOTTLED FOR JEFFERSON'S' line). Alcohol content and Name and address: Not on the label. "
                        "Net contents: Look at this. Government warning: Doesn't follow the rule.",
    "woodford-reserve": "Class or type: disagree (picked 'THIS EXCEPTIONAL BOURBON HAS BEEN CRAFTED'). Alcohol content: Not on the label. "
                        "Net contents: Look at this. Government warning: Doesn't follow the rule.",
    "laurel-glen": "Class or type: disagree (picked '2023 RED WINE BLEND'). Government warning: Doesn't follow the rule.",
    "common-roots": "Brand name: disagree. Name and address: Not on the label. Government warning: Doesn't follow the rule.",
}
import json  # noqa: E402

from app.models import Application  # noqa: E402
from app.pipeline import check_label  # noqa: E402

real = ROOT / "labels" / "real-cola"
cases = json.loads((real / "cases.json").read_text(encoding="utf-8"))
lines += [
    "## Five real approved labels (Public COLA Registry)",
    "",
    "TTB approved these, so any \"Doesn't follow the rule\" or disagreement is a false alarm. \"After\" types only what each record's "
    "application page holds (product type, source, brand, fanciful name; the form has no class, alcohol or net contents box), "
    "see `labels/real-cola/SOURCES.md`. \"Before\" is the live app on 2026-10-11, before the changes to the warning, class and "
    "net contents checks; that run also typed class, alcohol and net contents values that were guessed, not taken from the record.",
    "",
    "\"After\" is run with the hosted settings (`OCR_DET_MAX_SIDE=1280`), so it shows what the public URL returns.",
    "",
    "| Label | Before (non-matching rows) | After (non-matching rows) |",
    "|---|---|---|",
]
for name, c in cases.items():
    files = [(f, (real / f).read_bytes()) for f in c["images"]]
    out = check_label(Application(**c["application"]), files)
    after = "; ".join(f"{r.item}: {r.status_text}" for r in out.results if r.status.name not in ("MATCH", "INFO"))
    lines.append(f"| {name} | {BEFORE[name]} | {after or 'all rows Match'} |")
lines += [
    "",
    "Known limits seen on these labels: the Jefferson's and Woodford pictures in the record carry no alcohol statement at all "
    "(it is on a panel or strip that is not in those two images), so \"Not on the label\" is the correct answer for the pictures "
    "given. The net contents row is Look at this when the amount is molded into the glass. "
    "Where the warning has a letter or two the reader isn't sure of, the row is Look at this with the crop and the word shown.",
    "",
]
(ROOT / "docs" / "results.md").write_text("\n".join(lines), encoding="utf-8")
print(f"{miss} rows missed")
