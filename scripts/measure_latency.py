"""Measure the single check (and optionally a batch) against a running copy of the app.

  python scripts/measure_latency.py --url http://localhost:8000 --host "my PC, 8 cores"
  python scripts/measure_latency.py --url https://example --batch labels/batch/batch_300.zip

Writes docs/latency.md. No number goes in the README that this script did not produce.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "labels" / "all-test-cases"


def pct(values: list[float], p: float) -> float:
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(p * (len(s) - 1))))
    return s[k]


def single(client: httpx.Client, url: str, repeats: int) -> list[float]:
    expected = json.loads((OUT / "expected.json").read_text(encoding="utf-8"))
    cases = [k for k, v in expected.items() if "base" not in v]
    times: list[float] = []
    for name in cases:
        spec = expected[name]
        files = [("images", (n, (OUT / n).read_bytes(), "image/png")) for n in spec["images"]]
        for _ in range(repeats):
            t = time.perf_counter()
            r = client.post(f"{url}/check", data=spec["application"], files=files)
            times.append(time.perf_counter() - t)
            if r.status_code != 200:
                msg = re.findall(r'class="error"[^>]*>([^<]*)<', r.text)
                sys.exit(f"{name}: HTTP {r.status_code} after {times[-1]:.1f} s: {msg or r.text[:200]}")
    return times


EXAMPLE = dict(product_type="spirits", source="domestic", brand_name="OLD TOM DISTILLERY",
               class_type="Kentucky Straight Bourbon Whisky", alcohol_content="45% Alc./Vol. (90 Proof)", net_contents="750 mL")


def one_case(client: httpx.Client, url: str, folder: Path, repeats: int) -> list[float]:
    """The same front and back pair, with the Old Tom example values, posted `repeats` times."""
    files = [("images", (n, (folder / n).read_bytes(), "image/png")) for n in ("front.png", "back.png")]
    times: list[float] = []
    for _ in range(repeats):
        t = time.perf_counter()
        r = client.post(f"{url}/check", data=EXAMPLE, files=files)
        times.append(time.perf_counter() - t)
        if r.status_code != 200 or "Nothing for you to look at" not in r.text:
            sys.exit(f"HTTP {r.status_code}, unexpected result after {times[-1]:.1f} s")
    return times


def batch(client: httpx.Client, url: str, zip_path: Path, csv_path: Path | None) -> tuple[float, int]:
    files = [("images", (zip_path.name, zip_path.read_bytes(), "application/zip"))]
    if csv_path:
        files.append(("spreadsheet", (csv_path.name, csv_path.read_bytes(), "text/csv")))
    t = time.perf_counter()
    r = client.post(f"{url}/batch", data={"product_type": "spirits", "source": "domestic"}, files=files,
                    follow_redirects=False)
    if r.status_code != 303:
        sys.exit(f"batch upload failed: HTTP {r.status_code}")
    job = r.headers["location"].rsplit("/", 1)[1]
    while True:
        d = client.get(f"{url}/batch/{job}.json").json()
        if d.get("missing"):
            sys.exit("The batch vanished while polling. If the host runs more than one instance, limit it to one.")
        if d["finished"]:
            return time.perf_counter() - t, d["total"]
        time.sleep(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--host", default="", help="short description of the machine, for the table")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--case", type=Path, help="a folder with front.png and back.png; measures only that pair")
    ap.add_argument("--batch", type=Path)
    ap.add_argument("--csv", type=Path)
    a = ap.parse_args()
    url = a.url.rstrip("/")
    with httpx.Client(timeout=300) as client:
        client.get(f"{url}/health")
        times = one_case(client, url, a.case, a.repeats) if a.case else single(client, url, a.repeats)
        lines = [
            "# Latency",
            "",
            f"Measured {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} against {url}"
            + (f" ({a.host})" if a.host else "") + ".",
            "",
            "Single check, front and back picture, wall time as the browser would see it"
            + (f" ({a.case.name}, Old Tom example values)." if a.case else "."),
            "",
            "| Checks | p50 | p95 | max |",
            "|---|---|---|---|",
            f"| {len(times)} | {statistics.median(times):.2f} s | {pct(times, .95):.2f} s | {max(times):.2f} s |",
        ]
        if a.batch:
            wall, n = batch(client, url, a.batch, a.csv)
            lines += ["", f"Batch: {n} applications in {wall:.0f} s ({wall / n:.2f} s each).",
                      f"File: {a.batch.name}" + (f" with {a.csv.name}" if a.csv else ", no spreadsheet") + "."]
    text = "\n".join(lines) + "\n"
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "latency.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
