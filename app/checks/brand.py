from __future__ import annotations

from ..align import find_span
from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import squash_ws
from ..rules_data import BRAND_CASE_RULES, NAME_ADDRESS_PHRASES
from .common import biggest_text


def _is_producer_line(text: str) -> bool:
    low = " ".join(text.lower().split())
    return any(p in low for p in NAME_ADDRESS_PHRASES)


def _name_check(item: str, given: str, app: Application, lines: list[Line]) -> CheckResult:
    # The producer's own name in 'Bottled by ...' is not the brand on the front of the label.
    span = find_span(given, [ln for ln in lines if not _is_producer_line(ln.text)])
    big = biggest_text(lines)
    big_note = f" Biggest text on the label: '{big.text}'." if big else ""
    rule = BRAND_CASE_RULES[app.product_type]
    if span.kind == "exact":
        raw = squash_ws(" ".join(ln.text for ln in span.lines))
        reason = "Same name."
        if squash_ws(given) not in raw:
            reason = ("Same name, different capitals or punctuation. "
                      "Capitals don't matter on labels except in the warning.")
        part = Part(Status.MATCH, reason, rule if reason != "Same name." else None, span.lines)
        return combine(item, [part], given, span.found, )
    if span.kind == "unsure":
        part = Part(Status.LOOK, "Probably the same name; the reader wasn't sure of one letter.",
                    None, span.lines)
        return combine(item, [part], given, span.found)
    if span.kind == "near":
        lines_used = list(span.lines) + ([big] if big else [])
        part = Part(Status.DISAGREE, "The name on the label is different from the application." + big_note,
                    None, lines_used)
        return combine(item, [part], given, span.found)
    lines_used = [big] if big else []
    part = Part(Status.MISSING, f"Couldn't find '{given}' on the label." + big_note, None, lines_used)
    return combine(item, [part], given, None)


def check_brand(app: Application, lines: list[Line]) -> CheckResult:
    if not app.brand_name.strip():
        big = biggest_text(lines)
        if big is None:
            part = Part(Status.LOOK, "No large text could be read on the label.")
            return combine("Brand name", [part], None, None)
        part = Part(Status.INFO, "Biggest text on the label. No application brand name to compare.",
                    None, [big])
        return combine("Brand name", [part], None, big.text)
    return _name_check("Brand name", app.brand_name.strip(), app, lines)


def check_fanciful(app: Application, lines: list[Line]) -> CheckResult | None:
    if not app.fanciful_name.strip():
        return None
    return _name_check("Fanciful name", app.fanciful_name.strip(), app, lines)
