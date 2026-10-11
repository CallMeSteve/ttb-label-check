from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from ..align import OCR_UNSURE, WORDING, Diff
from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import levenshtein, ocr_confusable
from ..rules_data import WARNING_CAPS_RULE, WARNING_RULE, WARNING_TEXT

CANON = WARNING_TEXT.split()
_HEADER = re.compile(r"government\s*warning", re.I)
CONFIRM = ("Confirm by eye that GOVERNMENT WARNING: is bold and the rest of the warning is not bold. "
           "A reading tool can't tell this reliably from a photo, so this tool doesn't guess.")
MIN_OVERLAP = 0.25  # a line sharing less than this with the warning text is something else on the label


def _key(tok: str) -> str:
    """Case, accents and punctuation removed. Only the first two words of the warning must be capitals."""
    s = unicodedata.normalize("NFKD", tok)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]", "", s.upper())


CANON_KEYS = [_key(t) for t in CANON]
CANON_SET = set(CANON_KEYS)


def _same(a: str, b: str) -> bool:
    """Equal, or different only by what an OCR engine gets wrong inside a word."""
    if a == b:
        return True
    n = max(len(a), len(b))
    allow = 0 if n < 4 else 1 if n < 7 else 2 if n < 11 else 3
    return ocr_confusable(a, b) or (allow > 0 and levenshtein(a, b) <= allow)


def _short(s: str, n: int = 90) -> str:
    return s if len(s) <= n else s[:n - 3] + "..."


def _anchor(lines: list[Line]) -> tuple[int, int, bool] | None:
    """(line index, character offset, header found)."""
    for i, ln in enumerate(lines):
        m = _HEADER.search(ln.text)
        if m:
            return i, m.start(), True
    for i, ln in enumerate(lines):
        if re.search(r"surgeon\s*general|birth\s*defects", ln.text, re.I):
            return i, 0, False
    return None


def _belongs(line: Line) -> bool:
    keys = [k for k in (_key(t) for t in line.text.split()) if k]
    if not keys:
        return False
    hits = sum(1 for k in keys if k in CANON_SET or any(_same(k, c) for c in CANON_KEYS))
    return hits / len(keys) >= MIN_OVERLAP


def _collect(lines: list[Line], start: int, offset: int) -> list[tuple[str, Line]]:
    """Words of the warning in reading order. Lines that are other text on the label are left out,
    and a word split with a hyphen at the end of a line is joined."""
    first = lines[start]
    same_image = [ln for ln in lines[start:] if ln.image_index == first.image_index]
    cap = int(len(CANON) * 1.6) + 12
    words: list[tuple[str, Line]] = []
    carry = ""
    carry_line: Line | None = None
    for k, ln in enumerate(same_image):
        if k > 0 and not _belongs(ln):
            continue
        toks = (ln.text[offset:] if k == 0 else ln.text).split()
        for i, tok in enumerate(toks):
            if carry:
                tok, carry = carry + tok, ""
            if i == len(toks) - 1 and len(tok) > 2 and tok.endswith("-") and tok[:-1].isalpha():
                carry, carry_line = tok[:-1], ln
                continue
            words.append((tok, ln))
        if len(words) >= cap:
            break
    if carry and carry_line is not None:
        words.append((carry, carry_line))
    return words


def _diffs(found: list[tuple[str, str]]) -> tuple[list[Diff], int]:
    """found is (raw word, key). Word differences, ignoring extra words after the last matched word.
    Returns (diffs, number of found words used)."""
    keys = [k for _, k in found]
    sm = SequenceMatcher(a=CANON_KEYS, b=keys, autojunk=False)
    ops = sm.get_opcodes()
    while ops and ops[-1][0] == "insert":
        ops = ops[:-1]
    used = ops[-1][4] if ops else 0
    out: list[Diff] = []
    for op, i1, i2, j1, j2 in ops:
        if op == "equal":
            continue
        e_raw, f_raw = CANON[i1:i2], [w for w, _ in found[j1:j2]]
        e_key, f_key = CANON_KEYS[i1:i2], keys[j1:j2]
        after = found[j2][0] if j2 < len(found) else ""
        kind = WORDING
        if op == "replace":
            if len(e_key) == len(f_key) and all(_same(x, y) for x, y in zip(e_key, f_key)):
                kind = OCR_UNSURE
            elif _same("".join(e_key), "".join(f_key)):  # a space dropped or added inside a word
                kind = OCR_UNSURE
        out.append(Diff(kind, " ".join(e_raw), " ".join(f_raw), after))
    return out, used


def check_warning(app: Application, lines: list[Line]) -> CheckResult:
    anchor = _anchor(lines)
    if anchor is None:
        part = Part(Status.MISSING, "No government warning found on any picture.", WARNING_RULE)
        return combine("Government warning", [part], None, None)
    li, off, header_found = anchor
    start = lines[li]
    tokens = _collect(lines, li, off)
    raw_words = [t for t, _ in tokens]

    parts: list[Part] = []
    caps_ok = True
    colon_ok = True
    skip = 0
    if header_found:
        m = _HEADER.search(start.text)
        caps_ok = m.group(0) == m.group(0).upper()
        colon_ok = start.text[m.end():].lstrip().startswith(":")
        letters = ""
        for t in raw_words:  # GOVERNMENTWARNING may come as one word or two
            skip += 1
            letters += re.sub(r"[^A-Za-z]", "", t)
            if len(letters) >= len("GOVERNMENTWARNING"):
                break
        body = raw_words[skip:]
        if body and body[0] == ":":
            body = body[1:]
            skip += 1
        # The first two words are rebuilt here: capitals and colon are judged on their own.
        pairs = [("GOVERNMENT", "GOVERNMENT"), ("WARNING:", "WARNING")] + [(w, _key(w)) for w in body]
    else:
        pairs = [(w, _key(w)) for w in raw_words]
    pairs = [(w, k) for w, k in pairs if k]
    diffs, used = _diffs(pairs)
    shown = max(used + (skip - 2 if header_found else 0), 2)
    used_lines: list[Line] = []
    for _, ln in tokens[:shown]:
        if ln not in used_lines:
            used_lines.append(ln)
    label_text = " ".join(raw_words[:shown])

    if not header_found:
        parts.append(Part(Status.LOOK, "The heading GOVERNMENT WARNING: wasn't read on this label. "
                          "Look at the picture.", WARNING_CAPS_RULE, used_lines))
    elif not caps_ok:
        parts.append(Part(Status.DISAGREE, "The first two words must be in capital letters: GOVERNMENT WARNING.",
                          WARNING_CAPS_RULE, used_lines))
    if header_found and not colon_ok:
        parts.append(Part(Status.LOOK, "The colon after WARNING wasn't read. Look at the picture.",
                          WARNING_CAPS_RULE, used_lines))

    wording = [d for d in diffs if d.kind == WORDING]
    unsure = [d for d in diffs if d.kind == OCR_UNSURE]
    if wording:
        msgs = []
        for d in wording:
            if d.expected and d.found:
                msgs.append(f"Says '{_short((d.found + ' ' + d.after).strip())}', "
                            f"should say '{_short((d.expected + ' ' + d.after).strip())}'.")
            elif d.found:
                msgs.append(f"Says '{_short((d.found + ' ' + d.after).strip())}', "
                            f"should say '{_short(d.after) or 'nothing here'}'.")
            else:
                msgs.append(f"Missing: '{_short(d.expected)}'.")
        parts.append(Part(Status.DISAGREE, " ".join(msgs), WARNING_RULE, used_lines))
    elif unsure:
        n = len(unsure)
        parts.append(Part(Status.LOOK, f"The wording looks right, but the reader wasn't sure of {n} "
                          f"word{'s' if n != 1 else ''}. Check the highlighted words.", WARNING_RULE, used_lines))
    if not parts:
        parts.append(Part(Status.MATCH, "Wording and capital letters match the required text.", None, used_lines))

    view = [(d.expected or "(nothing)", d.found or "(nothing)") for d in diffs]
    res = combine("Government warning", parts, None, label_text, confirm=CONFIRM,
                  diff_view=view if view else None)
    res.rule = res.rule or WARNING_CAPS_RULE
    return res
