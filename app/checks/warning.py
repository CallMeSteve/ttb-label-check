from __future__ import annotations

import re
from difflib import SequenceMatcher

from ..align import OCR_UNSURE, WORDING, Diff
from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import ocr_confusable
from ..rules_data import WARNING_CAPS_RULE, WARNING_RULE, WARNING_TEXT

CANON = WARNING_TEXT.split()
_HEADER = re.compile(r"government\s*warning", re.I)
CONFIRM = ("Confirm by eye that GOVERNMENT WARNING: is bold and the rest of the warning is not bold. "
           "A reading tool can't tell this reliably from a photo, so this tool doesn't guess.")


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


def _diff_words(expected: list[str], found: list[str]) -> tuple[list[Diff], int]:
    """Word differences, ignoring extra words after the last matched word. Returns (diffs, found words used)."""
    sm = SequenceMatcher(a=expected, b=found, autojunk=False)
    ops = sm.get_opcodes()
    while ops and ops[-1][0] == "insert":
        ops = ops[:-1]
    used = ops[-1][4] if ops else 0
    diffs: list[Diff] = []
    for op, i1, i2, j1, j2 in ops:
        if op == "equal":
            continue
        e, f = expected[i1:i2], found[j1:j2]
        after = found[j2] if j2 < len(found) else ""
        kind = WORDING
        if op == "replace" and len(e) == len(f) and all(ocr_confusable(x, y) for x, y in zip(e, f)):
            kind = OCR_UNSURE
        diffs.append(Diff(kind, " ".join(e), " ".join(f), after))
    return diffs, used


def check_warning(app: Application, lines: list[Line]) -> CheckResult:
    anchor = _anchor(lines)
    if anchor is None:
        part = Part(Status.MISSING, "No government warning found on any picture.", WARNING_RULE)
        return combine("Government warning", [part], None, None)
    li, off, header_found = anchor
    start = lines[li]
    same_image = [ln for ln in lines[li:] if ln.image_index == start.image_index]
    tokens: list[tuple[str, Line]] = []
    cap = int(len(CANON) * 1.6) + 12
    for k, ln in enumerate(same_image):
        text = ln.text[off:] if k == 0 else ln.text
        for tok in text.split():
            tokens.append((tok, ln))
        if len(tokens) >= cap:
            break

    parts: list[Part] = []
    raw_words = [t for t, _ in tokens]
    found_words = list(raw_words)

    colon_ok = True
    caps_ok = True
    if header_found:
        m = _HEADER.search(start.text)
        caps_ok = m.group(0) == m.group(0).upper()
        tail = start.text[m.end():].lstrip()
        colon_ok = tail.startswith(":")
        # Rebuild the first two words as GOVERNMENT WARNING: so caps and colon are judged on their own.
        first_two = 0
        joined = ""
        for t in raw_words:
            first_two += 1
            joined += t
            if len(re.sub(r"[^A-Za-z]", "", joined)) >= len("GOVERNMENTWARNING"):
                break
        found_words = ["GOVERNMENT", "WARNING:"] + raw_words[first_two:]
        if not colon_ok and found_words[2:3] == [":"]:
            found_words = found_words[:2] + found_words[3:]
    else:
        found_words = raw_words

    diffs, used = _diff_words(CANON, found_words)
    used_lines: list[Line] = []
    for _, ln in tokens[:max(used, 2)]:
        if ln not in used_lines:
            used_lines.append(ln)
    label_text = " ".join(raw_words[:max(used, 2)])

    if not header_found:
        parts.append(Part(Status.DISAGREE, "The warning text is there, but the heading GOVERNMENT WARNING: is not.",
                          WARNING_CAPS_RULE, used_lines))
    elif not caps_ok:
        parts.append(Part(Status.DISAGREE, "The first two words must be in capital letters: GOVERNMENT WARNING.",
                          WARNING_CAPS_RULE, used_lines))
    if header_found and not colon_ok:
        diffs.insert(0, Diff(WORDING, "WARNING:", "WARNING", ""))

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
