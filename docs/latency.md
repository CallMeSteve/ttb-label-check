# Latency

Measured 2026-10-12 05:20 against https://treasurylabels.abdullah-sarwar.com (Google Cloud Run us-central1: front 4 vCPU/8 GiB billed per request; batch 4 vCPU/8 GiB, sleeps when idle).

Single check, front and back picture, wall time as the browser would see it: each of the 25 rendered test cases posted 40 times, one request at a time.

| Checks | p50 | p95 | max |
|---|---|---|---|
| 1000 | 1.17 s | 1.31 s | 1.44 s |

Batch, measured 2026-10-11 15:04 on the same setup with 4 workers: 150 applications in 266 s (1.77 s each).
File: batch_300.zip with batch_300.csv.
