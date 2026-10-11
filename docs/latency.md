# Latency

Measured 2026-10-11 15:04 against https://treasurylabels.abdullah-sarwar.com (Google Cloud Run us-central1: front 4 vCPU/8 GiB billed per request; batch 4 vCPU/8 GiB with 4 workers, sleeps when idle).

Single check, front and back picture, wall time as the browser would see it (1-clean-label, Old Tom example values).

| Checks | p50 | p95 | max |
|---|---|---|---|
| 10 | 2.20 s | 2.49 s | 2.49 s |

Batch: 150 applications in 266 s (1.77 s each).
File: batch_300.zip with batch_300.csv.
