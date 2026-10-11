from __future__ import annotations

import re

from ..models import Application, CheckResult, Line, Part, Status, combine
from ..rules_data import NAME_ADDRESS_PHRASES, NAME_ADDRESS_RULES

_ORIGIN = re.compile(r"\b(?:product|produce|made|distilled|bottled|brewed)\s+(?:of|in)\s+([A-Z][A-Za-z ]{2,30})", re.I)


def _starts_with_phrase(text: str, phrases: tuple[str, ...]) -> str | None:
    low = re.sub(r"\s+", " ", text.lower())
    for p in phrases:
        if re.search(rf"\b{re.escape(p)}\b", low):
            return p
    return None


def check_name_address(app: Application, lines: list[Line]) -> CheckResult:
    rule = NAME_ADDRESS_RULES[app.product_type]
    hits = [(ln, _starts_with_phrase(ln.text, NAME_ADDRESS_PHRASES)) for ln in lines]
    hits = [(ln, p) for ln, p in hits if p]
    if not hits:
        part = Part(Status.MISSING, "No 'Bottled by', 'Produced by' or similar statement with a name and address.", rule)
        return combine("Name and address", [part], None, None)
    parts: list[Part] = []
    first = hits[0][0]
    idx = lines.index(first)
    shown = lines[idx:idx + 2]
    label_says = " ".join(ln.text for ln in shown)
    parts.append(Part(Status.MATCH, "A name and address statement is present.", None, shown))
    if app.source == "imported" and not any(p == "imported by" for _, p in hits):
        parts.append(Part(Status.LOOK, "Imported products need an 'Imported by' statement.",
                          "27 CFR 5.68(b)" if app.product_type == "spirits" else None, shown))
    if app.source == "imported":
        for ln in lines:
            m = _ORIGIN.search(ln.text)
            if m:
                parts.append(Part(Status.INFO, "Country of origin marking is a Customs rule (19 CFR 134), not TTB.",
                                  None, [ln]))
                break
    return combine("Name and address", parts, None, label_says)
