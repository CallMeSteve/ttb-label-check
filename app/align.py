from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .models import Line
from .normalize import fold, ocr_confusable

OCR_UNSURE = "OCR_UNSURE"
WORDING = "WORDING"


@dataclass
class Diff:
    kind: str
    expected: str
    found: str
    after: str = ""  # one following word, for context in messages


@dataclass
class Span:
    kind: str  # "exact", "unsure", "near", "none"
    lines: list[Line] = field(default_factory=list)
    found: str = ""
    diffs: list[Diff] = field(default_factory=list)


def line_tokens(lines: list[Line]) -> list[tuple[str, int]]:
    """(folded token, index of its line in `lines`)."""
    out: list[tuple[str, int]] = []
    for i, ln in enumerate(lines):
        for t in fold(ln.text).split():
            out.append((t, i))
    return out


def classify_diffs(expected: list[str], found: list[str]) -> list[Diff]:
    """Each difference is either the OCR possibly misreading, or different wording."""
    diffs: list[Diff] = []
    sm = SequenceMatcher(a=expected, b=found, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        e, f = expected[i1:i2], found[j1:j2]
        after = found[j2] if j2 < len(found) else ""
        kind = WORDING
        if op == "replace":
            if len(e) == len(f) and all(ocr_confusable(x, y) for x, y in zip(e, f)):
                kind = OCR_UNSURE
            elif ocr_confusable("".join(e), "".join(f)):
                kind = OCR_UNSURE
        diffs.append(Diff(kind, " ".join(e), " ".join(f), after))
    return diffs


def _same_words(a: list[str], b: list[str]) -> bool:
    return a == b or "".join(a) == "".join(b)


def find_span(expected: str, lines: list[Line]) -> Span:
    """Find `expected` in the OCR lines. Windows cover up to two adjacent lines of one image."""
    exp = fold(expected).split()
    if not exp:
        return Span("none")
    best: tuple[float, Span] | None = None
    by_image: dict[int, list[Line]] = {}
    for ln in lines:
        by_image.setdefault(ln.image_index, []).append(ln)
    for img_lines in by_image.values():
        toks = line_tokens(img_lines)
        for n in {max(1, len(exp) - 1), len(exp), len(exp) + 1}:
            for s in range(0, max(0, len(toks) - n) + 1):
                window = toks[s:s + n]
                if len(window) < n:
                    continue
                idxs = sorted({i for _, i in window})
                if len(idxs) > 2 or (len(idxs) == 2 and idxs[1] - idxs[0] != 1):
                    continue
                words = [t for t, _ in window]
                if _same_words(exp, words):
                    return Span("exact", [img_lines[i] for i in idxs], " ".join(words))
                ratio = SequenceMatcher(a=exp, b=words, autojunk=False).ratio()
                if best is None or ratio > best[0]:
                    diffs = classify_diffs(exp, words)
                    kind = "unsure" if diffs and all(d.kind == OCR_UNSURE for d in diffs) else "near"
                    best = (ratio, Span(kind, [img_lines[i] for i in idxs], " ".join(words), diffs))
    if best is None or best[0] < 0.4:
        return Span("none")
    return best[1]
