from __future__ import annotations

import io
import os
import threading

import numpy as np
from PIL import Image, ImageOps

from .models import Box, Line

MAX_EDGE = 1600
_engine = None
_lock = threading.Lock()


def get_engine():
    """One engine per process. OCR_THREADS and OCR_DET_MAX_SIDE tune speed on a slow host (defaults: off)."""
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR

        threads = int(os.environ.get("OCR_THREADS", "0"))
        params: dict = {}
        if threads > 0:
            params["EngineConfig.onnxruntime.intra_op_num_threads"] = threads
        # Spec section 9, step (a): a smaller detection size if the host is slow.
        side = int(os.environ.get("OCR_DET_MAX_SIDE", "0"))
        if side > 0:
            params.update({"Det.limit_type": "max", "Det.limit_side_len": side})
        _engine = RapidOCR(params=params or None)
    return _engine


def load_image(data: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(data))
    if im.format == "JPEG":
        im.draft("RGB", (MAX_EDGE * 2, MAX_EDGE * 2))
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def read_lines(im: Image.Image, image_index: int, max_edge: int = MAX_EDGE) -> list[Line]:
    """OCR one picture. Boxes come back in the coordinates of `im`."""
    scale = min(1.0, max_edge / max(im.size))
    small = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS) if scale < 1 else im
    with _lock:
        out = get_engine()(np.asarray(small)[:, :, ::-1])
    if out.txts is None or out.boxes is None:
        return []
    lines = []
    for txt, score, pts in zip(out.txts, out.scores, out.boxes):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        lines.append(Line(str(txt), float(score),
                          Box(image_index, min(xs) / scale, min(ys) / scale, max(xs) / scale, max(ys) / scale)))
    return sort_lines(lines)


def sort_lines(lines: list[Line]) -> list[Line]:
    """Reading order: picture, then top to bottom."""
    return sorted(lines, key=lambda ln: (ln.image_index, (ln.box.y0 + ln.box.y1) / 2, ln.box.x0))


def warm_up() -> float:
    """Run one inference so the first request is not the slow one. Returns seconds."""
    import time

    t = time.perf_counter()
    im = Image.new("RGB", (400, 120), "white")
    from PIL import ImageDraw

    ImageDraw.Draw(im).text((20, 40), "WARM UP 750 mL", fill="black")
    read_lines(im, 0)
    return time.perf_counter() - t
