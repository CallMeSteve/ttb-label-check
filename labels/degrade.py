"""Photo-like degradations made with Pillow and NumPy only."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageFilter

CREAM = (245, 238, 220)


def rot8(im: Image.Image) -> Image.Image:
    return im.rotate(8, resample=Image.BICUBIC, expand=True, fillcolor=CREAM)


def persp(im: Image.Image) -> Image.Image:
    w, h = im.size
    shift = 0.07 * w
    src = [(shift, 0.03 * h), (w - 0.02 * w, 0), (w, h), (0, h - 0.03 * h)]
    # Map the output rectangle onto a skewed quadrilateral of the source (coefficients solved below).
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    return im.transform(im.size, Image.PERSPECTIVE, _coeffs(dst, src), Image.BICUBIC, fillcolor=CREAM)


def _coeffs(dst, src):
    a = []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for p in src for c in p]
    return np.linalg.solve(np.array(a, dtype=float), np.array(b, dtype=float)).tolist()


def glare(im: Image.Image) -> Image.Image:
    w, h = im.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy, r = 0.68 * w, 0.42 * h, 0.28 * w
    alpha = np.clip(1 - np.hypot(xx - cx, yy - cy) / r, 0, 1) ** 1.5 * 0.85
    arr = np.asarray(im).astype(float)
    out = arr * (1 - alpha[..., None]) + 255 * alpha[..., None]
    return Image.fromarray(out.astype("uint8"))


def blur(im: Image.Image) -> Image.Image:
    return im.filter(ImageFilter.GaussianBlur(1.5))


def jpeg40(im: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=40)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def degrade(im: Image.Image, kind: str) -> Image.Image:
    return {"rot8": rot8, "persp": persp, "glare": glare, "blur": blur, "jpeg40": jpeg40}[kind](im)
