# Build log

- 2026-10-11 10:30 ET: scaffold, fonts, models, normalize, align, rules_data, brand and alcohol checks written. Tests 0 so far. No Docker on this PC (cannot run docker build here).
- 2026-10-11 11:00 ET: §14 row 2 done (all checks + rule tests). 55 tests passing.
- 2026-10-11 12:00 ET: §14 row 3 done (label generator, 35 rendered cases, end-to-end + degraded tests). 117 tests passing. OCR warm ~1.0-1.6 s per two-image check on this PC (see docs/latency.md later).
- 2026-10-11 13:30 ET: §14 rows 4-5 done (UI, crops, result/help/print, batch with pool, status polling, CSV export). Dockerfile, ci.yml, image.yml written (Docker itself not runnable on this PC). 129 tests passing incl. no-network test.
- 2026-10-11 15:30 ET: §14 rows 6-8 done (bold detection cut per amendment; degraded set; latency measured locally p50 1.22 s / p95 1.31 s; browser click-through of single and batch OK; README, APPROACH, NEXT drafted; voice grep clean). 129 tests passing.
- 2026-10-11 evening: fixed live HTTP 400s (10 s time limit was returning 400 and the abandoned OCR thread kept the lock, so later checks queued and also timed out); now 503, CHECK_TIME_LIMIT env; added /health alias. Cloud Run check takes 7-8 s, over budget.
- class/type row no longer matches the bottler address lines; shows the label's own class or asks for a look. 139 tests.
- 2026-10-11 late: Cloud Run split into a front service (4 vCPU, billed per request, one instance) and a batch service (4 workers, sleeps when idle). Public URL single check p50 2.20 s, worst 4.60 s across all 40 samples; 300-picture batch 266 s. Browser shrinks photos to fit the 30 MB upload cap. Pre-submission review fixes: ingredient percents, liqueurs, partly-read fanciful names. 171 tests.
