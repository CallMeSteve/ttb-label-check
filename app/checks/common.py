from __future__ import annotations

from ..models import Line
from ..normalize import fold_whisky
from ..rules_data import CLASS_MINIMUMS, MALT_CLASSES, SPIRITS_CLASSES, WINE_CLASSES


def by_image(lines: list[Line]) -> dict[int, list[Line]]:
    out: dict[int, list[Line]] = {}
    for ln in lines:
        out.setdefault(ln.image_index, []).append(ln)
    return out


def joined_text(lines: list[Line]) -> tuple[str, list[tuple[int, int, Line]]]:
    """One string for the lines of one image, plus (start, end, line) offsets."""
    parts: list[str] = []
    spans: list[tuple[int, int, Line]] = []
    pos = 0
    for ln in lines:
        text = ln.text.strip()
        spans.append((pos, pos + len(text), ln))
        parts.append(text)
        pos += len(text) + 1
    return " ".join(parts), spans


def lines_in(spans: list[tuple[int, int, Line]], start: int, end: int) -> list[Line]:
    return [ln for s, e, ln in spans if s < end and e > start]


def biggest_text(lines: list[Line]) -> Line | None:
    """The tallest line, looking at the first picture that has any text."""
    groups = by_image(lines)
    if not groups:
        return None
    first = [ln for ln in groups[min(groups)] if sum(c.isalpha() for c in ln.text) >= 3]  # not a barcode
    return max(first, key=lambda ln: ln.box.height) if first else None


def detect_class(lines: list[Line], product_type: str) -> tuple[str | None, Line | None]:
    """Find a class keyword on the label. Returns (keyword, the line it was on)."""
    table = {"spirits": SPIRITS_CLASSES, "wine": WINE_CLASSES, "malt": MALT_CLASSES}[product_type]
    seen = []
    for ln in lines:
        seen.append((" " + fold_whisky(ln.text) + " ", ln))
    for key in table:
        for text, ln in seen:
            if f" {key} " in text:
                return key, ln
    return None, None


def class_minimum(key: str | None, lines: list[Line]) -> float | None:
    from ..rules_data import FLAVORED_MINIMUM

    if key is None or key not in CLASS_MINIMUMS:
        return None
    # A liqueur or cordial named after a base spirit ("Bourbon Cream Liqueur") has no 40% minimum.
    folded = [" " + fold_whisky(ln.text) + " " for ln in lines]
    if any(" LIQUEUR " in t or " CORDIAL " in t for t in folded):
        return None
    if any(" FLAVORED " in " " + fold_whisky(ln.text) + " " for ln in lines):
        return FLAVORED_MINIMUM
    return CLASS_MINIMUMS[key]
