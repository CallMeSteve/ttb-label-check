"""Time two-picture checks at different ONNX thread counts, in separate processes.

  python scripts/ocr_threads.py 1 2 4
"""
import os
import subprocess
import sys
import time

CODE = """
import time, pathlib
from app.pipeline import check_label
from app.models import Application
from app.ocr import warm_up
warm_up()
d = pathlib.Path('labels/all-test-cases')
files = [(n, (d / n).read_bytes()) for n in ('old_tom_clean_front.png', 'old_tom_clean_back.png')]
t = time.perf_counter()
for _ in range(8):
    check_label(Application(brand_name='OLD TOM DISTILLERY'), files)
print((time.perf_counter() - t) / 8)
"""

for n in sys.argv[1:]:
    env = dict(os.environ, OCR_THREADS=n)
    t = time.perf_counter()
    out = subprocess.run([sys.executable, "-c", CODE], env=env, capture_output=True, text=True)
    print(f"threads={n}: {out.stdout.strip().splitlines()[-1]} s per check")
