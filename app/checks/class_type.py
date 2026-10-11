from __future__ import annotations

from ..models import Application, CheckResult, Line, Part, Status, combine
from ..normalize import fold_whisky, ocr_confusable, squash_ws
from ..rules_data import SIGNIFICANT_WORDS
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


def check_class(app: Application, lines: list[Line]) -> CheckResult:
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
    if best is None or best[0][0] == 0:
        return combine("Class or type", [Part(Status.MISSING, f"Couldn't find '{given}' on the label.")], given, None)
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
