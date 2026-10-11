from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import to_float
from ..rules_data import (
    METRIC_UNITS, SPIRITS_FILL_RULE, SPIRITS_FILLS_ML, UNIT_ML, WINE_FILL_RULE, WINE_FILLS_ML,
)
from .common import by_image, joined_text, lines_in

_UNIT = (r"(fl(?:uid)?\.?\s*oz\.?|ounces?|oz\.?|milliliters?|millilitres?|ml\.?|centiliters?|centilitres?|"
         r"cl\.?|liters?|litres?|ltr\.?|l\b|pints?|pt\.?|quarts?|qt\.?|gallons?|gal\.?)")
_AMOUNT = re.compile(rf"(\d+(?:[.,]\d+)?)\s*{_UNIT}", re.I)


@dataclass
class Amount:
    ml: float
    kind: str  # "metric" or "us"
    text: str
    lines: list[Line]


def _unit_key(u: str) -> str:
    u = u.lower().replace(" ", "")
    if u.startswith(("fl", "oz", "ounce")):
        return "floz"
    if u.startswith(("milli", "ml")):
        return "ml"
    if u.startswith(("centi", "cl")):
        return "cl"
    if u.startswith(("lit", "ltr", "l")):
        return "l"
    if u.startswith("pi") or u.startswith("pt"):
        return "pint"
    if u.startswith(("qu", "qt")):
        return "quart"
    return "gallon"


def parse_amounts(text: str) -> list[tuple[float, str, str]]:
    out = []
    for m in _AMOUNT.finditer(text):
        key = _unit_key(m.group(2))
        out.append((to_float(m.group(1)) * UNIT_ML[key], "metric" if key in METRIC_UNITS else "us", m.group(0)))
    return out


def find_amounts(lines: list[Line]) -> list[Amount]:
    found: list[Amount] = []
    for img_lines in by_image(lines).values():
        text, spans = joined_text(img_lines)
        for m in _AMOUNT.finditer(text):
            key = _unit_key(m.group(2))
            found.append(Amount(to_float(m.group(1)) * UNIT_ML[key],
                                "metric" if key in METRIC_UNITS else "us", m.group(0),
                                lines_in(spans, m.start(), m.end())))
    return found


def _close(a: float, b: float, tol: float = 0.5) -> bool:
    return abs(a - b) <= tol


def check_net(app: Application, lines: list[Line]) -> CheckResult:
    pt = app.product_type
    amounts = find_amounts(lines)
    app_says = app.net_contents.strip() or "not given"
    if not amounts:
        part = Part(Status.LOOK, "Not found on the label image. It can be molded into the glass; "
                    "check item 15 of the application.",
                    "27 CFR 5.61(a)(2), 5.63(b)(2)" if pt == "spirits" else
                    "27 CFR 4.32(b)(2)" if pt == "wine" else "27 CFR 7.63(a)(5)")
        return combine("Net contents", [part], app_says, None)

    metric = [a for a in amounts if a.kind == "metric"]
    us = [a for a in amounts if a.kind == "us"]
    ev = [ln for a in amounts for ln in a.lines]
    label_says = " / ".join(a.text.strip() for a in amounts[:3])
    parts: list[Part] = []

    def raw(a: Amount) -> str:
        return a.text.strip()

    if pt == "spirits":
        if not metric:
            parts.append(Part(Status.DISAGREE, "Spirits need a metric statement (mL or L). "
                              "U.S. units can be added but can't replace it.", "27 CFR 5.70(a)", ev))
        elif not any(any(_close(a.ml, f) for f in SPIRITS_FILLS_ML) for a in metric):
            bad = metric[0]
            parts.append(Part(Status.DISAGREE, f"{raw(bad)} is not an approved bottle size for spirits.",
                              SPIRITS_FILL_RULE, bad.lines))
    elif pt == "wine":
        def ok_wine(ml: float) -> bool:
            return any(_close(ml, f) for f in WINE_FILLS_ML) or (ml > 3000 and _close(ml % 1000, 0, 0.5))
        if not metric:
            parts.append(Part(Status.DISAGREE, "Wine needs a metric statement (mL or L).", "27 CFR 4.37(a)", ev))
        elif not any(ok_wine(a.ml) for a in metric):
            bad = metric[0]
            parts.append(Part(Status.DISAGREE, f"{raw(bad)} is not an approved bottle size for wine.",
                              WINE_FILL_RULE, bad.lines))
    else:
        if not us:
            parts.append(Part(Status.DISAGREE,
                              "Beer must show fluid ounces (or pints/quarts/gallons). "
                              "Milliliters can be added but can't replace them.", "27 CFR 7.70(a), (c)", ev))

    if app.net_contents.strip():
        want = parse_amounts(app.net_contents)
        if not want:
            parts.append(Part(Status.LOOK, f"Couldn't understand '{app.net_contents.strip()}' as an amount. "
                              "Try something like 750 mL.", None, ev))
        elif not any(_close(w[0], a.ml) for w in want for a in amounts):
            parts.append(Part(Status.DISAGREE,
                              f"Application says {app.net_contents.strip()}, label says {label_says}.", None, ev))
    if not parts:
        reason = f"{label_says}."
        if not app.net_contents.strip():
            reason += " Application: not given, so only the rules were checked."
        parts.append(Part(Status.MATCH, reason, None, ev))
    return combine("Net contents", parts, app_says, label_says)
