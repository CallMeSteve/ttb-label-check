from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    MATCH = "Matches"
    LOOK = "Look at this"
    DISAGREE = "Label and application disagree"
    MISSING = "Not on the label"
    INFO = "For your information"


# Higher wins when several findings feed one row.
SEVERITY = {Status.INFO: 0, Status.MATCH: 1, Status.LOOK: 2, Status.DISAGREE: 3, Status.MISSING: 3}

PRODUCT_TYPES = ("spirits", "wine", "malt")
PRODUCT_LABELS = {"spirits": "Distilled spirits", "wine": "Wine", "malt": "Malt beverage"}


@dataclass(frozen=True)
class Box:
    image_index: int
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass
class Line:
    text: str
    conf: float
    box: Box

    @property
    def image_index(self) -> int:
        return self.box.image_index


FIELD_LIMIT = 200


@dataclass
class Application:
    product_type: str = "spirits"
    source: str = "domestic"
    brand_name: str = ""
    fanciful_name: str = ""
    class_type: str = ""
    alcohol_content: str = ""
    net_contents: str = ""

    def __post_init__(self):
        # No real entry is this long, and the matching work grows with the number of typed words.
        for name in ("brand_name", "fanciful_name", "class_type", "alcohol_content", "net_contents"):
            setattr(self, name, str(getattr(self, name))[:FIELD_LIMIT])


@dataclass
class CheckResult:
    item: str
    status: Status
    application_says: str | None
    label_says: str | None
    reason: str
    rule: str | None = None
    evidence: list[Box] = field(default_factory=list)
    confirm: str | None = None
    # Warning row only: list of (required words, label words) pairs for the differing spots.
    diff_view: list[tuple[str, str]] | None = None
    crops: list[str] = field(default_factory=list)
    # True when the label breaks a rule by itself, even if an application value was typed.
    rule_only: bool = False

    @property
    def status_text(self) -> str:
        if self.status is Status.DISAGREE and (not self.application_says or self.rule_only):
            return "Doesn't follow the rule"
        return self.status.value

    @property
    def symbol(self) -> str:
        return {
            Status.MATCH: "✓",
            Status.LOOK: "◎",
            Status.DISAGREE: "✗",
            Status.MISSING: "?",
            Status.INFO: "i",
        }[self.status]

    @property
    def css(self) -> str:
        return {
            Status.MATCH: "ok",
            Status.LOOK: "look",
            Status.DISAGREE: "bad",
            Status.MISSING: "bad",
            Status.INFO: "info",
        }[self.status]

    @property
    def needs_look(self) -> bool:
        return self.status in (Status.LOOK, Status.DISAGREE, Status.MISSING)


@dataclass
class Part:
    """One finding inside a row that combines several rules."""

    status: Status
    reason: str
    rule: str | None = None
    lines: list[Line] = field(default_factory=list)


LOW_CONFIDENCE = 0.6


def combine(item: str, parts: list[Part], application_says: str | None,
            label_says: str | None, **extra) -> CheckResult:
    """Worst status wins; every non-matching reason is listed."""
    worst = max(parts, key=lambda p: SEVERITY[p.status])
    shown = [p for p in parts if p.status not in (Status.MATCH, Status.INFO)] or parts
    reason = " ".join(p.reason for p in shown)
    rules: list[str] = []
    for p in shown:
        if p.rule and p.rule not in rules:
            rules.append(p.rule)
    evidence: list[Box] = []
    used: list[Line] = []
    for p in parts:
        for ln in p.lines:
            if ln.box not in evidence:
                evidence.append(ln.box)
                used.append(ln)
    status = worst.status
    if status is Status.MATCH and used and sum(ln.conf for ln in used) / len(used) < LOW_CONFIDENCE:
        status = Status.LOOK
        reason = "Hard to read here. " + reason
    return CheckResult(
        item=item, status=status, application_says=application_says,
        label_says=label_says, reason=reason, rule="; ".join(rules) or None,
        evidence=evidence, **extra,
    )
