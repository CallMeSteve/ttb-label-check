from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw

from .models import Box, CheckResult, Status

MAX_WIDTH = 600
PAD = 14
COLORS = {
    Status.MATCH: "#1b6e2d", Status.LOOK: "#8a5a00", Status.DISAGREE: "#b00020",
    Status.MISSING: "#b00020", Status.INFO: "#444444",
}


def _union(boxes: list[Box]) -> Box:
    return Box(boxes[0].image_index, min(b.x0 for b in boxes), min(b.y0 for b in boxes),
               max(b.x1 for b in boxes), max(b.y1 for b in boxes))


def crop_data_uri(im: Image.Image, box: Box, color: str) -> str:
    x0, y0 = max(0, int(box.x0) - PAD), max(0, int(box.y0) - PAD)
    x1, y1 = min(im.width, int(box.x1) + PAD), min(im.height, int(box.y1) + PAD)
    crop = im.crop((x0, y0, x1, y1)).copy()
    d = ImageDraw.Draw(crop)
    ox0, oy0 = int(box.x0) - x0 - 3, int(box.y0) - y0 - 3
    ox1, oy1 = int(box.x1) - x0 + 3, int(box.y1) - y0 + 3
    d.rectangle((ox0, oy0, ox1, oy1), outline=color, width=max(2, crop.width // 300))
    if crop.width > MAX_WIDTH:
        crop = crop.resize((MAX_WIDTH, max(1, round(crop.height * MAX_WIDTH / crop.width))), Image.LANCZOS)
    buf = io.BytesIO()
    crop.save(buf, "PNG", optimize=False)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def attach_crops(results: list[CheckResult], images: list[Image.Image]) -> None:
    for r in results:
        by_img: dict[int, list[Box]] = {}
        for b in r.evidence:
            by_img.setdefault(b.image_index, []).append(b)
        for idx in sorted(by_img)[:2]:
            if idx < len(images):
                r.crops.append(crop_data_uri(images[idx], _union(by_img[idx]), COLORS[r.status]))
