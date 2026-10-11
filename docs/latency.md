# Latency

Measured 2026-10-11 10:53 against http://localhost:8000 (Windows PC, 32 logical cores, no container).

Single check, front and back picture, wall time as the browser would see it.

| Checks | p50 | p95 | max |
|---|---|---|---|
| 75 | 1.22 s | 1.31 s | 1.89 s |

Batch: 150 applications in 165 s (1.10 s each).
File: batch_300.zip with batch_300.csv.
