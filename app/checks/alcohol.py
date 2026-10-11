from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import fold, parse_abv, to_float
from ..rules_data import CLASS_MINIMUM_RULE
from .common import by_image, class_minimum, detect_class, joined_text, lines_in

_NUM = r"(\d{1,3}(?:[.,]\d+)?)"
_PCT = re.compile(rf"{_NUM}\s*(?:%|percent)", re.I)
_RANGE = re.compile(r"alcohol\s+(\d{1,2})\s*%?\s+to\s+(\d{1,2})\s*%\s+by\s+vol", re.I)
_PROOF = re.compile(r"(\d+(?:\.\d+)?)\s*(?:°\s*)?proof", re.I)
_NOT_ALCOHOL = re.compile(r"^\s*(agave|natural|grain|neutral|fruit|malt|juice|barley|corn|rye|wheat|whisk|spirits)", re.I)

CITES = {
    "spirits": ("27 CFR 5.63(a)(3)", "27 CFR 5.65(b)(3)"),
    "wine": ("27 CFR 4.36(a)", "27 CFR 4.36(b)"),
    "malt": ("27 CFR 7.63(a)(3)", "27 CFR 7.65(b)(4)"),
}


@dataclass
class AbvFound:
    value: float
    form: str  # "standard", "abv", "bare"
    text: str
    lines: list[Line]


def find_abv(lines: list[Line]) -> AbvFound | None:
    found: list[AbvFound] = []
    for img_lines in by_image(lines).values():
        text, spans = joined_text(img_lines)
        for m in _RANGE.finditer(text):
            found.append(AbvFound(float(m.group(2)), "standard", m.group(0), lines_in(spans, m.start(), m.end())))
        for m in _PCT.finditer(text):
            before = text[max(0, m.start() - 22):m.start()].lower()
            after = text[m.end():m.end() + 24].lower()
            context = before + " " + after
            has_std = "alc" in context or "vol" in context
            has_abv = bool(re.search(r"\babv\b", context))
            # "100% Agave", "51% corn" and the like describe ingredients, even when Alc./Vol. sits close by.
            if _NOT_ALCOHOL.match(text[m.end():m.end() + 14]):
                continue
            form = "abv" if has_abv and not has_std else "standard" if has_std else "bare"
            start = max(0, m.start() - 22) if has_std else m.start()
            found.append(AbvFound(to_float(m.group(1)), form, text[m.start():m.end()],
                                  lines_in(spans, start, m.end() + 14 if has_std else m.end())))
    for want in ("standard", "abv", "bare"):
        for f in found:
            if f.form == want:
                return f
    return None


def find_proof(lines: list[Line]) -> tuple[float, list[Line]] | None:
    for img_lines in by_image(lines).values():
        text, spans = joined_text(img_lines)
        m = _PROOF.search(text)
        if m:
            return float(m.group(1)), lines_in(spans, m.start(), m.end())
    return None


def _num(x: float) -> str:
    return f"{x:g}"


def check_alcohol(app: Application, lines: list[Line]) -> CheckResult:
    pt = app.product_type
    cite_missing, cite_format = CITES[pt]
    parts: list[Part] = []
    app_val = parse_abv(app.alcohol_content) if app.alcohol_content.strip() else None
    app_says = app.alcohol_content.strip() or "not given"
    folded_all = " " + " ".join(fold(ln.text) for ln in lines) + " "
    table_wine = pt == "wine" and (" TABLE WINE " in folded_all or " LIGHT WINE " in folded_all)

    abv = find_abv(lines)
    if abv is None:
        if pt == "spirits":
            parts.append(Part(Status.MISSING, "No alcohol content found on the label.", cite_missing))
        elif pt == "wine":
            if table_wine:
                parts.append(Part(Status.MATCH, "Not required for table wine at 14% or less.", "27 CFR 4.36(a)"))
            else:
                parts.append(Part(Status.LOOK, "No alcohol content found. Required if over 14%.", "27 CFR 4.36(a)"))
        else:
            parts.append(Part(Status.MATCH,
                              "Not required on most beers; required only when alcohol comes from added flavors.",
                              cite_missing))
        if app_val is not None and pt != "spirits":
            parts.append(Part(Status.LOOK, f"Application says {_num(app_val)}%, but no alcohol content was found."))
        return combine("Alcohol content", parts, app_says, None)

    label_says = abv.text
    ev = abv.lines
    if abv.form == "abv":
        parts.append(Part(Status.LOOK, "Written as 'ABV'. The rule lists alc, %, /, and vol as the allowed short forms.",
                          cite_format, ev))
    elif abv.form == "bare":
        parts.append(Part(Status.LOOK, "The percent sign stands alone. The rule wants 'Alc.' and 'Vol.' with it, "
                          "for example 45% Alc./Vol.", cite_format, ev))

    if pt == "spirits":
        proof = find_proof(lines)
        if proof is not None:
            label_says += f" ({_num(proof[0])} Proof)"
            ev = ev + [ln for ln in proof[1] if ln not in ev]
            if abs(proof[0] - 2 * abv.value) > 0.1:
                parts.append(Part(
                    Status.DISAGREE,
                    f"The label contradicts itself: {_num(abv.value)}% Alc./Vol. is {_num(2 * abv.value)} proof, "
                    f"but the label says {_num(proof[0])} Proof.", "27 CFR 5.1, 5.65(b)(1)(i)", ev))
        key, class_line = detect_class(lines, "spirits")
        minimum = class_minimum(key, lines)
        if minimum is not None and abv.value < minimum and class_line is not None:
            word = {"WHISKY": "Whisky", "AGAVE": "Agave spirits"}.get(key, key.title())
            parts.append(Part(Status.DISAGREE,
                              f"A label that says {word} must be at least {_num(minimum)}% alcohol.",
                              CLASS_MINIMUM_RULE, ev + [class_line]))
    if table_wine and abv.value > 14:
        parts.append(Part(Status.DISAGREE, "Table wine and light wine can't be over 14% alcohol.",
                          "27 CFR 4.21(a)(5), 4.36(a)", ev))
    rule_failed = any(p.status is Status.DISAGREE for p in parts)
    app_differs = app_val is not None and app_val != abv.value
    if app_differs:
        parts.append(Part(Status.DISAGREE,
                          f"Application says {_num(app_val)}%, label says {_num(abv.value)}%.", None, ev))

    if not parts:
        reason = f"{_num(abv.value)}% alcohol by volume."
        if app_val is None:
            reason += " Application: not given, so only the rules were checked."
        parts.append(Part(Status.MATCH, reason, None, ev))
    result = combine("Alcohol content", parts, app_says, label_says)
    result.rule_only = rule_failed or not app_differs
    return result
