from __future__ import annotations

from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import fold_whisky, ocr_confusable, squash_ws
from ..rules_data import NAME_ADDRESS_PHRASES, SIGNIFICANT_WORDS
from .common import by_image, detect_class

RULE = "27 CFR 5.143(b)"


def _sig(text: str) -> set[str]:
    padded = f" {text} "
    return {w for w in SIGNIFICANT_WORDS if f" {w} " in padded}


def _present(word: str, tokens: list[str]) -> str:
    """'yes', 'unsure' or 'no'."""
    if word in tokens:
        return "yes"
    if any(ocr_confusable(word, t) for t in tokens):
        return "unsure"
    return "no"


def _without_address(lines: list[Line]) -> list[Line]:
    """Drop each 'Bottled by ...' line and the city and state line under it. They are not the class."""
    drop: set[int] = set()
    for i, ln in enumerate(lines):
        low = " ".join(ln.text.lower().split())
        if any(p in low for p in NAME_ADDRESS_PHRASES):
            drop.update((i, i + 1))
    return [ln for i, ln in enumerate(lines) if i not in drop]


def check_class(app: Application, all_lines: list[Line]) -> CheckResult:
    lines = _without_address(all_lines)
    given = app.class_type.strip()
    if not given:
        key, ln = detect_class(lines, app.product_type)
        if ln is None:
            part = Part(Status.INFO, "No class or type designation was recognised on the label.")
            return combine("Class or type", [part], None, None)
        part = Part(Status.INFO, "Class or type found on the label. No application value to compare.", None, [ln])
        return combine("Class or type", [part], None, ln.text)

    words = fold_whisky(given).split()
    app_sig = _sig(" ".join(words))
    best: tuple[tuple[int, int], list[Line], list[str]] | None = None
    for img_lines in by_image(lines).values():
        for i in range(len(img_lines)):
            for span in (img_lines[i:i + 1], img_lines[i:i + 2]):
                toks = fold_whisky(" ".join(ln.text for ln in span)).split()
                score = sum(1 for w in words if _present(w, toks) != "no")
                key = (score, -len(toks))
                if best is None or key > best[0]:
                    best = (key, span, toks)
    if best is None or best[0][0] * 2 < len(words):
        # No line holds most of the typed words. Report the label's own class if there is one.
        found = None
        for kind in (app.product_type, "spirits", "wine", "malt"):  # the picked product type may be wrong
            _, found = detect_class(lines, kind)
            if found is not None:
                break
        if found is not None:
            reason = f"Application says '{given}', label says '{squash_ws(found.text)}'."
            return combine("Class or type", [Part(Status.DISAGREE, reason, RULE, [found])], given, squash_ws(found.text))
        reason = "Couldn't find a class or type on the label. Look at the picture."
        return combine("Class or type", [Part(Status.LOOK, reason)], given, None)
    _, span, toks = best
    label_text = squash_ws(" ".join(ln.text for ln in span))
    states = [_present(w, toks) for w in words]
    missing = [w for w, s in zip(words, states) if s == "no"]
    if missing:
        legal = [w for w in missing if w in {s.split()[0] for s in SIGNIFICANT_WORDS}]
        if legal:
            reason = (f"Application says '{given}', label says '{label_text}'. "
                      f"'{legal[0].title()}' has a legal meaning.")
        else:
            reason = f"Application says '{given}', label says '{label_text}'."
        return combine("Class or type", [Part(Status.DISAGREE, reason, RULE, span)], given, label_text)
    added = _sig(" ".join(toks)) - app_sig
    if added:
        word = sorted(added)[0].title()
        reason = (f"Application says '{given}', label says '{label_text}'. "
                  f"'{word}' has a legal meaning.")
        return combine("Class or type", [Part(Status.DISAGREE, reason, RULE, span)], given, label_text)
    if "unsure" in states:
        return combine("Class or type", [Part(Status.LOOK, "Probably the same; the reader wasn't sure of a letter.",
                                              None, span)], given, label_text)
    reason = "Same class and type."
    if squash_ws(given) not in label_text:
        reason = "Same class and type. Capitals, punctuation and whisky/whiskey spelling don't matter."
    return combine("Class or type", [Part(Status.MATCH, reason, RULE if "spelling" in reason else None, span)],
                   given, label_text)
