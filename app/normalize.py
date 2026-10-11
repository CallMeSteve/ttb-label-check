from __future__ import annotations

import re
import unicodedata

_DELETE = "'’‘ʼ`“”\".,"


def fold(s: str) -> str:
    """Case, punctuation and spacing removed. Stone's Throw and STONE'S THROW both give STONES THROW."""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("&", " AND ")
    s = s.translate({ord(c): None for c in _DELETE})
    s = s.upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fold_whisky(s: str) -> str:
    """fold() with WHISKEY and WHISKY treated as one word (27 CFR 5.143(b))."""
    return " ".join("WHISKY" if t == "WHISKEY" else t for t in fold(s).split())


def squash_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# Pairs an OCR engine mixes up. Multi-character shapes first.
_MULTI = (("RN", "M"), ("CL", "D"), ("VV", "W"), ("II", "U"))
_SINGLE = str.maketrans({"0": "O", "1": "I", "L": "I", "5": "S", "8": "B", "2": "Z"})


def _canon(tok: str) -> str:
    t = tok.upper()
    for a, b in _MULTI:
        t = t.replace(a, b)
    return t.translate(_SINGLE)


def ocr_confusable(a: str, b: str) -> bool:
    """True when two tokens differ only by shapes an OCR engine confuses.

    At most one confusion per five characters. A missing or extra punctuation mark
    (or a capital that the engine may have read as lower case) also counts."""
    if a == b:
        return False
    ca, cb = a.upper(), b.upper()
    sa = re.sub(r"[^A-Z0-9]", "", ca)
    sb = re.sub(r"[^A-Z0-9]", "", cb)
    if sa == sb:
        return True
    if _canon(sa) != _canon(sb):
        return False
    longest = max(len(sa), len(sb))
    if len(sa) == len(sb):
        diffs = sum(1 for x, y in zip(sa, sb) if x != y)
    else:
        diffs = abs(len(sa) - len(sb))
    return 0 < diffs <= max(1, longest // 5)


_NUM = r"(\d+(?:[.,]\d+)?)"


def to_float(s: str) -> float:
    return float(s.replace(",", "."))


def parse_abv(text: str) -> float | None:
    """45, 45%, 45% Alc./Vol. (90 Proof) all give 45.0."""
    m = re.search(_NUM, text or "")
    return to_float(m.group(1)) if m else None
