"""Batch checking: group pictures into applications, run them in a process pool, keep results in memory."""
from __future__ import annotations

import csv
import io
import multiprocessing
import os
import re
import secrets
import threading
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

from .models import PRODUCT_TYPES, Application, CheckResult
from .pipeline import check_label

MAX_APPLICATIONS = 300
MAX_PER_APPLICATION = 4
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_TOTAL_BYTES = 400 * 1024 * 1024
EXPIRY_SECONDS = 24 * 3600
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
_SUFFIX = re.compile(r"^(?P<id>.+)_(?P<part>front|back|neck|side)\.[^.]+$", re.I)
_PART_ORDER = {"front": 0, "back": 1, "neck": 2, "side": 3}
CSV_COLUMNS = ["application_id", "images", "product_type", "source", "brand_name", "fanciful_name",
               "class_type", "alcohol_content", "net_contents"]


@dataclass
class Item:
    index: int
    app_id: str
    application: Application
    filenames: list[str]
    state: str = "waiting"  # waiting, done, error
    results: list[CheckResult] = field(default_factory=list)
    seconds: float = 0.0
    error: str = ""

    @property
    def looks(self) -> int:
        return sum(1 for r in self.results if r.needs_look)


@dataclass
class Job:
    id: str
    created: float
    items: list[Item]
    notes: list[str]
    picture_count: int

    @property
    def done(self) -> int:
        return sum(1 for i in self.items if i.state != "waiting")

    @property
    def finished(self) -> bool:
        return self.done == len(self.items)

    @property
    def to_look(self) -> int:
        return sum(1 for i in self.items if i.state == "error" or i.looks)


JOBS: dict[str, Job] = {}
_lock = threading.Lock()
_pool: ProcessPoolExecutor | None = None


def _init_worker() -> None:
    from .ocr import get_engine

    get_engine()


def _work(app_fields: dict, files: list[tuple[str, bytes]]):
    out = check_label(Application(**app_fields), files)
    return out.results, out.seconds


def get_pool() -> ProcessPoolExecutor:
    global _pool
    with _lock:
        if _pool is None:
            workers = int(os.environ.get("BATCH_WORKERS", min(os.cpu_count() or 1, 4)))
            _pool = ProcessPoolExecutor(max_workers=max(1, workers), mp_context=multiprocessing.get_context("spawn"),
                                        initializer=_init_worker)
        return _pool


def shutdown_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.shutdown(wait=False, cancel_futures=True)
        _pool = None


def purge() -> None:
    cutoff = time.time() - EXPIRY_SECONDS
    with _lock:
        for k in [k for k, j in JOBS.items() if j.created < cutoff]:
            del JOBS[k]


def get_job(job_id: str) -> Job | None:
    purge()
    return JOBS.get(job_id)


class UploadError(Exception):
    pass


def collect_pictures(uploads: list[tuple[str, bytes]]) -> dict[str, bytes]:
    """Plain files and the contents of zip files, flattened to picture name -> bytes."""
    pictures: dict[str, bytes] = {}
    total = 0

    def add(name: str, data: bytes) -> None:
        nonlocal total
        base = name.replace("\\", "/").split("/")[-1]
        if not base or base.startswith(".") or not base.lower().endswith(IMAGE_EXT):
            return
        if len(data) > MAX_IMAGE_BYTES:
            raise UploadError(f"{base} is too large ({len(data) // (1024 * 1024)} MB). Pictures under 15 MB work.")
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise UploadError("That is more than 400 MB of pictures. Split it into two batches.")
        key = base
        n = 2
        while key in pictures:
            key = f"{n}_{base}"
            n += 1
        pictures[key] = data

    for name, data in uploads:
        if name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for info in zf.infolist():
                        if info.is_dir() or "__MACOSX" in info.filename:
                            continue
                        if info.file_size > MAX_IMAGE_BYTES:
                            raise UploadError(f"{info.filename} is too large. Pictures under 15 MB work.")
                        add(info.filename, zf.read(info))
            except zipfile.BadZipFile:
                raise UploadError(f"{name} is not a readable zip file.") from None
        else:
            add(name, data)
    return pictures


def _product(value: str, default: str) -> str:
    v = (value or "").strip().lower()
    if v.startswith(("spirit", "distilled")):
        return "spirits"
    if v.startswith("wine"):
        return "wine"
    if v.startswith(("malt", "beer")):
        return "malt"
    return default


def _group_without_csv(names: list[str]) -> list[tuple[str, list[str]]]:
    groups: dict[str, list[tuple[int, str]]] = {}
    for name in sorted(names):
        m = _SUFFIX.match(name)
        if m:
            groups.setdefault(m.group("id"), []).append((_PART_ORDER[m.group("part").lower()], name))
        else:
            groups.setdefault(name.rsplit(".", 1)[0], []).append((0, name))
    return [(k, [n for _, n in sorted(v)]) for k, v in groups.items()]


def plan_job(pictures: dict[str, bytes], csv_bytes: bytes | None, product_type: str,
             source: str) -> tuple[list[tuple[Item, list[str]]], list[str]]:
    """Returns ([(item, filenames)], notes)."""
    notes: list[str] = []
    plan: list[tuple[str, Application, list[str]]] = []
    if csv_bytes:
        text = csv_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        lower = {n.lower(): n for n in pictures}
        used: set[str] = set()
        missing: list[str] = []
        bad_rows = 0
        for n, row in enumerate(reader, start=1):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            names = [x.strip() for x in row.get("images", "").split(";") if x.strip()]
            found = []
            for x in names:
                key = lower.get(x.lower())
                if key:
                    found.append(key)
                    used.add(key)
                else:
                    missing.append(x)
            if not found:
                bad_rows += 1
                continue
            app = Application(
                product_type=_product(row.get("product_type", ""), product_type),
                source="imported" if row.get("source", "").lower().startswith("imp") else
                ("domestic" if row.get("source") else source),
                brand_name=row.get("brand_name", ""), fanciful_name=row.get("fanciful_name", ""),
                class_type=row.get("class_type", ""), alcohol_content=row.get("alcohol_content", ""),
                net_contents=row.get("net_contents", ""),
            )
            plan.append((row.get("application_id") or f"row {n}", app, found[:MAX_PER_APPLICATION]))
        if missing:
            shown = ", ".join(missing[:8]) + (" and more" if len(missing) > 8 else "")
            notes.append(f"{len(missing)} picture name{'s' if len(missing) != 1 else ''} in the spreadsheet "
                         f"aren't in the upload: {shown}. The rest were checked.")
        if bad_rows:
            notes.append(f"{bad_rows} spreadsheet row{'s' if bad_rows != 1 else ''} had no pictures that "
                         "could be found and were skipped.")
        unused = [n for n in pictures if n not in used]
        if unused:
            notes.append(f"{len(unused)} picture{'s' if len(unused) != 1 else ''} not named in the spreadsheet "
                         "were skipped.")
    else:
        for app_id, names in _group_without_csv(list(pictures)):
            if len(names) > MAX_PER_APPLICATION:
                notes.append(f"{app_id} has more than 4 pictures. Only the first 4 were used.")
            plan.append((app_id, Application(product_type=product_type, source=source), names[:MAX_PER_APPLICATION]))
    if len(plan) > MAX_APPLICATIONS:
        notes.append(f"A batch holds up to {MAX_APPLICATIONS} applications. The first {MAX_APPLICATIONS} were "
                     f"checked and {len(plan) - MAX_APPLICATIONS} were left out.")
        plan = plan[:MAX_APPLICATIONS]
    out = []
    for i, (app_id, app, names) in enumerate(plan, start=1):
        out.append((Item(i, app_id, app, names), names))
    return out, notes


def start_job(uploads: list[tuple[str, bytes]], csv_bytes: bytes | None, product_type: str, source: str) -> Job:
    if product_type not in PRODUCT_TYPES:
        product_type = "spirits"
    pictures = collect_pictures([u for u in uploads if not u[0].lower().endswith(".csv")])
    if not pictures:
        raise UploadError("No pictures found. Add JPG, PNG or WEBP files, or a zip of them.")
    plan, notes = plan_job(pictures, csv_bytes, product_type, source)
    if not plan:
        raise UploadError("None of the rows in the spreadsheet matched a picture in the upload.")
    head = f"{len(pictures)} pictures, {len(plan)} applications."
    job = Job(secrets.token_urlsafe(8), time.time(), [i for i, _ in plan], [head] + notes, len(pictures))
    purge()
    with _lock:
        JOBS[job.id] = job
    pool = get_pool()
    for item, names in plan:
        files = [(n, pictures[n]) for n in names]
        fut = pool.submit(_work, item.application.__dict__.copy(), files)
        fut.add_done_callback(lambda f, it=item: _finish(it, f))
    return job


def _finish(item: Item, fut) -> None:
    try:
        results, seconds = fut.result()
        item.results, item.seconds, item.state = results, seconds, "done"
    except Exception:  # one bad picture must not stop the batch
        item.error = "This application couldn't be read. Check that its pictures are valid JPG, PNG or WEBP files."
        item.state = "error"
        item.results = []


def summary(item: Item) -> str:
    if item.state == "waiting":
        return "Waiting"
    if item.state == "error":
        return "Couldn't read"
    if item.looks:
        return f"{item.looks} to look at"
    return "Nothing to look at"


def _safe(cell: str) -> str:
    """Stop a spreadsheet program from running a cell that starts like a formula."""
    return "'" + cell if cell[:1] in ("=", "+", "-", "@") else cell


def export_csv(job: Job) -> str:
    items_order: list[str] = []
    for it in job.items:
        for r in it.results:
            if r.item not in items_order:
                items_order.append(r.item)
    buf = io.StringIO()
    w = csv.writer(buf)
    head = ["application_id", "pictures", "summary"]
    for name in items_order:
        head += [f"{name} status", f"{name} reason"]
    w.writerow(head)
    for it in job.items:
        by = {r.item: r for r in it.results}
        row = [_safe(it.app_id), _safe("; ".join(it.filenames)), summary(it)]
        for name in items_order:
            r = by.get(name)
            row += [r.status_text if r else "", r.reason if r else ""]
        w.writerow(row)
    return buf.getvalue()


def csv_template() -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    w.writerow(["A123", "old_tom_clean_front.png;old_tom_clean_back.png", "spirits", "domestic",
                "OLD TOM DISTILLERY", "", "Kentucky Straight Bourbon Whisky", "45% Alc./Vol. (90 Proof)", "750 mL"])
    return buf.getvalue()
