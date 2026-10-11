from __future__ import annotations

import time
from dataclasses import dataclass, field

from .checks.run import headline, run_checks
from .crops import attach_crops
from .models import Application, CheckResult
from .ocr import load_image, read_lines


@dataclass
class Outcome:
    results: list[CheckResult]
    seconds: float
    filenames: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return headline(self.results)[0]

    @property
    def look_count(self) -> int:
        return headline(self.results)[1]


def check_label(app: Application, files: list[tuple[str, bytes]]) -> Outcome:
    """Read the pictures, run the checks, cut the evidence crops. Pictures are not kept."""
    t0 = time.perf_counter()
    images = [load_image(data) for _, data in files]
    lines = []
    for i, im in enumerate(images):
        lines.extend(read_lines(im, i))
    results = run_checks(app, lines)
    attach_crops(results, images)
    return Outcome(results, time.perf_counter() - t0, [name for name, _ in files])
