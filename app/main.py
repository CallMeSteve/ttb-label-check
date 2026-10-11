from __future__ import annotations

import asyncio
import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

from . import batch, ocr
from .models import PRODUCT_LABELS, PRODUCT_TYPES, Application
from .pipeline import check_label

BASE = Path(__file__).parent
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGES = 4
ALLOWED = (".jpg", ".jpeg", ".png", ".webp")
TIME_LIMIT = float(os.environ.get("CHECK_TIME_LIMIT", "10"))
log = logging.getLogger("label-check")

state: dict = {"warm_seconds": None}


@asynccontextmanager
async def lifespan(_: FastAPI):
    state["warm_seconds"] = await run_in_threadpool(ocr.warm_up)
    yield
    batch.shutdown_pool()


app = FastAPI(title="Label Check", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(PRODUCT_LABELS=PRODUCT_LABELS)

EXAMPLE = dict(product_type="spirits", source="domestic", brand_name="OLD TOM DISTILLERY",
               class_type="Kentucky Straight Bourbon Whisky", alcohol_content="45% Alc./Vol. (90 Proof)",
               net_contents="750 mL")


def render(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def ext_of(filename: str) -> str:
    return Path(filename or "").suffix.lower()


async def read_pictures(uploads: list[UploadFile], limit: int | None = MAX_IMAGES) -> tuple[list[tuple[str, bytes]], str | None]:
    uploads = [u for u in uploads if u.filename]
    if not uploads:
        return [], "Add at least one picture of the label."
    if limit and len(uploads) > limit:
        return [], "Up to 4 pictures per label. For more, use Check many labels."
    files: list[tuple[str, bytes]] = []
    for u in uploads:
        ext = ext_of(u.filename)
        if ext not in ALLOWED:
            return [], f"That file is a {ext or 'file with no type'}. Use a JPG, PNG, or WEBP picture of the label."
        data = await u.read()
        if len(data) > MAX_IMAGE_BYTES:
            return [], f"That picture is too large ({len(data) // (1024 * 1024)} MB). Pictures under 15 MB work."
        try:
            Image.open(io.BytesIO(data)).verify()
        except Exception:
            return [], f"{u.filename} could not be opened as a picture. Use a JPG, PNG, or WEBP picture of the label."
        files.append((u.filename, data))
    return files, None


@app.get("/", response_class=HTMLResponse)
def index(request: Request, product_type: str = "spirits", source: str = "domestic"):
    form = dict(product_type=product_type if product_type in PRODUCT_TYPES else "spirits",
                source=source if source in ("domestic", "imported") else "domestic")
    return render(request, "index.html", form=form, error=None, field_error=None, example=EXAMPLE)


@app.post("/check", response_class=HTMLResponse)
async def check(request: Request):
    form = await request.form()
    values = {k: str(form.get(k, "")).strip() for k in
              ("product_type", "source", "brand_name", "fanciful_name", "class_type", "alcohol_content", "net_contents")}
    if values["product_type"] not in PRODUCT_TYPES:
        values["product_type"] = "spirits"
    if values["source"] not in ("domestic", "imported"):
        values["source"] = "domestic"
    uploads = [v for v in form.getlist("images") if hasattr(v, "filename")]

    def again(error=None, field_error=None, code=400):
        return render(request, "index.html", code, form=values, error=error, field_error=field_error, example=EXAMPLE)

    if not values["brand_name"]:
        return again(field_error="Type the brand name from the application.")
    files, error = await read_pictures(uploads)
    if error:
        return again(error=error)
    application = Application(**values)
    try:
        outcome = await asyncio.wait_for(run_in_threadpool(check_label, application, files), TIME_LIMIT)
    except TimeoutError:
        return again(error="This one is taking too long. Try a smaller or sharper picture.", code=503)
    except Exception:
        log.exception("check failed")
        return again(error="Something went wrong on our side. Your picture wasn't saved. Try again.", code=500)
    return render(request, "result.html", outcome=outcome, application=application, batch_link=None)


@app.get("/batch", response_class=HTMLResponse)
def batch_page(request: Request):
    return render(request, "batch.html", error=None, form=dict(product_type="spirits", source="domestic"))


@app.post("/batch")
async def batch_start(request: Request):
    form = await request.form()
    product_type = str(form.get("product_type", "spirits"))
    source = str(form.get("source", "domestic"))
    pics = [v for v in form.getlist("images") if hasattr(v, "filename") and v.filename]
    sheet = form.get("spreadsheet")
    uploads: list[tuple[str, bytes]] = []
    for u in pics:
        uploads.append((u.filename, await u.read()))
    csv_bytes = await sheet.read() if sheet is not None and getattr(sheet, "filename", "") else None

    def again(msg):
        return render(request, "batch.html", 400, error=msg, form=dict(product_type=product_type, source=source))

    if not uploads:
        return again("Add the pictures, or a zip file of them.")
    try:
        job = await run_in_threadpool(batch.start_job, uploads, csv_bytes, product_type, source)
    except batch.UploadError as exc:
        return again(str(exc))
    except Exception:
        log.exception("batch failed to start")
        return again("Something went wrong on our side. Nothing was saved. Try again.")
    return RedirectResponse(f"/batch/{job.id}", status_code=303)


def _batch_json(job: batch.Job) -> dict:
    return {
        "done": job.done, "total": len(job.items), "to_look": job.to_look, "finished": job.finished,
        "notes": job.notes,
        "items": [{"n": i.index, "id": i.app_id, "files": ", ".join(i.filenames), "state": i.state,
                   "summary": batch.summary(i), "looks": i.looks, "error": i.state == "error"} for i in job.items],
    }


@app.get("/batch/template.csv")
def batch_template():
    return Response(batch.csv_template(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="label-check-template.csv"'})


@app.get("/batch/{job_id}.json")
def batch_json(job_id: str):
    job = batch.get_job(job_id)
    if job is None:
        return JSONResponse({"missing": True}, status_code=404)
    return _batch_json(job)


@app.get("/batch/{job_id}.csv")
def batch_csv(job_id: str):
    job = batch.get_job(job_id)
    if job is None:
        return PlainTextResponse("This batch is gone.", status_code=404)
    return Response(batch.export_csv(job), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="label-check-{job_id}.csv"'})


@app.get("/batch/{job_id}", response_class=HTMLResponse)
def batch_status(request: Request, job_id: str):
    job = batch.get_job(job_id)
    if job is None:
        return render(request, "batch_gone.html", 404)
    return render(request, "batch_status.html", job=job, data=_batch_json(job))


@app.get("/batch/{job_id}/item/{n}", response_class=HTMLResponse)
def batch_item(request: Request, job_id: str, n: int):
    job = batch.get_job(job_id)
    if job is None:
        return render(request, "batch_gone.html", 404)
    item = next((i for i in job.items if i.index == n), None)
    if item is None:
        return render(request, "batch_gone.html", 404)
    if item.state == "waiting":
        return RedirectResponse(f"/batch/{job_id}", status_code=303)

    looks = item.looks
    shown = SimpleNamespace(
        results=item.results, seconds=item.seconds, filenames=item.filenames, look_count=looks,
        title="Nothing for you to look at" if not looks else f"{looks} thing{'s' if looks != 1 else ''} to look at")

    return render(request, "result.html", outcome=shown, application=item.application,
                  batch_link=f"/batch/{job_id}", item=item)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return render(request, "help.html")


@app.get("/health")
@app.get("/healthz")
def healthz(run: int = 0):
    seconds = state["warm_seconds"]
    if run:
        seconds = ocr.warm_up()
    return {"ok": seconds is not None, "ocr_warm_up_seconds": seconds}
