# Build log

- 2026-10-11 10:30 ET: scaffold, fonts, models, normalize, align, rules_data, brand and alcohol checks written. Tests 0 so far. No Docker on this PC (cannot run docker build here).
- 2026-10-11 11:00 ET: §14 row 2 done (all checks + rule tests). 55 tests passing.
- 2026-10-11 12:00 ET: §14 row 3 done (label generator, 35 rendered cases, end-to-end + degraded tests). 117 tests passing. OCR warm ~1.0-1.6 s per two-image check on this PC (see docs/latency.md later).
- 2026-10-11 13:30 ET: §14 rows 4-5 done (UI, crops, result/help/print, batch with pool, status polling, CSV export). Dockerfile, ci.yml, image.yml written (Docker itself not runnable on this PC). 129 tests passing incl. no-network test.
- 2026-10-11 15:30 ET: §14 rows 6-8 done (bold detection cut per amendment; degraded set; latency measured locally p50 1.22 s / p95 1.31 s; browser click-through of single and batch OK; README, APPROACH, NEXT drafted; voice grep clean). 129 tests passing.
