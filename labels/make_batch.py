"""Build batch fixtures from the rendered cases.

labels/batch_sample.zip      12 applications, no spreadsheet (the "Try it" batch)
labels/batch/batch_300.zip   150 applications, 300 pictures, plus batch_300.csv (throughput test; not committed)

Run after make_labels.py:  python labels/make_batch.py
"""
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "all-test-cases"
BATCH = HERE / "batch"
COLUMNS = ["application_id", "images", "product_type", "source", "brand_name", "fanciful_name",
           "class_type", "alcohol_content", "net_contents"]


def main() -> None:
    expected = json.loads((OUT / "expected.json").read_text(encoding="utf-8"))
    cases = [k for k, v in expected.items() if "base" not in v]

    with zipfile.ZipFile(HERE / "batch_sample.zip", "w", zipfile.ZIP_STORED) as zf:
        for name in cases[:12]:
            for img in expected[name]["images"]:
                zf.write(OUT / img, img)

    BATCH.mkdir(exist_ok=True)
    rows = []
    with zipfile.ZipFile(BATCH / "batch_300.zip", "w", zipfile.ZIP_STORED) as zf:
        for n in range(150):
            case = cases[n % len(cases)]
            spec = expected[case]
            app_id = f"A{n + 1:03d}"
            names = []
            for img, part in zip(spec["images"], ("front", "back")):
                arc = f"{app_id}_{part}.png"
                zf.write(OUT / img, arc)
                names.append(arc)
            a = spec["application"]
            rows.append([app_id, ";".join(names), a.get("product_type", ""), a.get("source", ""),
                         a.get("brand_name", ""), a.get("fanciful_name", ""), a.get("class_type", ""),
                         a.get("alcohol_content", ""), a.get("net_contents", "")])
    with open(BATCH / "batch_300.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print("wrote labels/batch_sample.zip and labels/batch/batch_300.{zip,csv}")


if __name__ == "__main__":
    main()
