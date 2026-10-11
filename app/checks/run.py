from __future__ import annotations

from ..models import Application, CheckResult, Line, Part, Status, combine
from .alcohol import check_alcohol
from .brand import check_brand, check_fanciful
from .class_type import check_class
from .name_address import check_name_address
from .net_contents import check_net
from .warning import check_warning

UNREADABLE = ("We couldn't read this picture. A flatter, brighter photo usually fixes it.")


def is_unreadable(lines: list[Line]) -> bool:
    return sum(1 for ln in lines if ln.conf > 0.5) < 3


def run_checks(app: Application, lines: list[Line]) -> list[CheckResult]:
    """Rows in the order of the paper checklist."""
    if is_unreadable(lines):
        shown = " / ".join(ln.text for ln in lines[:6]) or None
        return [combine("Picture", [Part(Status.LOOK, UNREADABLE)], None, shown)]
    rows: list[CheckResult | None] = [
        check_brand(app, lines),
        check_fanciful(app, lines),
        check_class(app, lines),
        check_alcohol(app, lines),
        check_net(app, lines),
        check_name_address(app, lines),
        check_warning(app, lines),
    ]
    return [r for r in rows if r is not None]


def headline(results: list[CheckResult]) -> tuple[str, int]:
    n = sum(1 for r in results if r.needs_look)
    if n == 0:
        return "Nothing for you to look at", 0
    return (f"{n} thing{'s' if n != 1 else ''} to look at"), n
