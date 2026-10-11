# Label Check

Label Check compares an alcohol label to its application and shows you where to look.

## Try it

Live app: https://treasurylabels.abdullah-sarwar.com.

The sample pictures are in `labels/try-these/`. Each numbered folder holds a front and back picture and a `WHAT-TO-DO.txt` that says what to type and what you should see:

1. `1-clean-label`: nothing to look at (apart from the by-eye check that the warning heading is bold).
2. `2-brand-in-capitals`: STONE'S THROW on the label against Stone's Throw on the application is a match.
3. `3-warning-not-in-capitals`: the warning row explains the capital letters and shows the cropped warning.
4. `4-proof-does-not-match`: 45% with 80 proof is flagged.
5. `5-bad-photo`: the clean label with glare added. It is a mild test, and the folder says so.
6. `6-many-labels-at-once`: 12 labels in a zip, no spreadsheet.

The full set of 25 rendered cases, with the degraded copies, lives in `labels/all-test-cases/`. Every case with its expected and actual result, misses included, is in `docs/results.md`. The bold-check limit is explained in "What I found in the regulations" and in `APPROACH.md`.

A free host would sleep when idle. This one is meant to stay awake, so checks should take a few seconds from the first request.

## What it checks

| Item | What it compares | Rule |
|---|---|---|
| Brand name | The typed name against the label, ignoring capitals and punctuation | [27 CFR 5.52(d)](https://www.ecfr.gov/current/title-27/section-5.52), [7.52(d)](https://www.ecfr.gov/current/title-27/section-7.52) |
| Class or type | Typed class against the label. "Straight" and similar words must match | [27 CFR 5.143](https://www.ecfr.gov/current/title-27/section-5.143) |
| Alcohol content | Format, proof arithmetic, class minimums, table wine limit, and the typed value if given | [27 CFR 5.65](https://www.ecfr.gov/current/title-27/section-5.65), [4.36](https://www.ecfr.gov/current/title-27/section-4.36), [7.65](https://www.ecfr.gov/current/title-27/section-7.65) |
| Net contents | Approved bottle sizes for spirits and wine, U.S. units for beer, and the typed value if given | [27 CFR 5.203](https://www.ecfr.gov/current/title-27/section-5.203), [4.72](https://www.ecfr.gov/current/title-27/section-4.72), [7.70](https://www.ecfr.gov/current/title-27/section-7.70) |
| Name and address | That a "Bottled by" style statement is there, and "Imported by" for imports | [27 CFR 5.66](https://www.ecfr.gov/current/title-27/section-5.66), [5.68](https://www.ecfr.gov/current/title-27/section-5.68) |
| Government warning | Exact wording, capital letters on the first two words, and a crop of the warning for the bold check | [27 CFR 16.21](https://www.ecfr.gov/current/title-27/section-16.21), [16.22](https://www.ecfr.gov/current/title-27/section-16.22) |

## What I found in the regulations, and what it changed

I started with the application form instead of the label. TTB's current Form 5100.31 doesn't have a box for alcohol content, net contents, or class and type. TTB took them out in 2016 because a producer can change those numbers on an approved label without asking again. So this app checks them against the rules every time, and against the application only if you type what it says.

Capital letters don't matter anywhere on a label except the first two words of the warning. TTB lists changes of case and punctuation as allowable revisions for every beverage type, and the spirits and beer rules say mandatory information may be in capitals, lower case, or mixed. Wine has no such sentence, so for wine the app cites the allowable revision. That is why STONE'S THROW and Stone's Throw are a match by rule, with a note saying so, and not a score above some threshold.

The warning has a rule that gets less attention: the first two words must be bold, and the remainder may not be. A reading tool can't tell bold from regular reliably in a photo, so the warning row always shows the crop and asks the agent to confirm it.

Beer must show fluid ounces. A beer label with only "355 mL" breaks the rule, while a spirits label must show metric. And 700 mL is a legal spirits size, so a checker with one fill list for everything would flag a valid bottle.

The alcohol tolerances in the rules (0.3 points for spirits and beer, 1 or 1.5 for wine) apply to lab tests of the product against its label. They don't apply when you compare a label to a form, so the app compares those two numbers exactly.

TTB also says about half of returned applications are wrong on the application side. So when the two disagree, the screen says "Label and application disagree" and shows both. It doesn't assume the label is the wrong one.

## Decisions I made

**Text reading runs inside the app, with RapidOCR on ONNX Runtime, instead of a cloud vision service.** The agency's network blocks calls to outside machine-learning services, so a hosted API would fail the way the scanning pilot did. RapidOCR uses the PP-OCR model family and runs on a CPU. The models are downloaded when the image is built.

**Names are matched on the exact words with capitals and punctuation removed, not on a similarity score.** A 90 percent score would pass OLD TOMS against OLD TOM, which are different brands. When the only difference is a shape the reader often confuses (0 for O, rn for m), the row says "Look at this" instead of failing.

**Evidence is a cropped picture next to each row, not a zoomable image.** Nobody has to pan or zoom to see what the tool saw.

**Batch works with no spreadsheet.** Drop a folder or a zip. Every check that needs no application value still runs. A spreadsheet is optional and adds the comparisons.

**There are no approve or reject buttons.** The decision stays with the agent and the COLA system. The headline is a count of things to look at.

**Pages are rendered on the server with Jinja2 and one small JavaScript file.** There is no build step and no single-page app. The Print button works because the pages are plain HTML.

**There is no language model in v1.** The decisions are rule checks on regulation text, so they give the same answer every time and can say which rule they used. The place a vision model would help is badly photographed labels, and I would run it inside the agency's Azure tenant.

## How fast it is

Measured with `scripts/measure_latency.py`, which writes `docs/latency.md`.

| Where | Single check (front and back), p50 / p95 / max | Batch |
|---|---|---|
| My Windows PC, 32 logical cores, 2026-10-11 | 1.22 s / 1.31 s / 1.89 s (75 checks) | 150 applications (300 pictures) in 165 s |
| Public URL | TODO(Abdullah): run `python scripts/measure_latency.py --url <public URL>` after deploy and paste the table | TODO(Abdullah): same run with `--batch labels/batch/batch_300.zip --csv labels/batch/batch_300.csv` |

On one thread a two-picture check takes about 2.5 s on my PC, and about 1.8 s on two threads. A small cloud container will land closer to the one and two thread numbers. `OCR_THREADS` sets the ONNX thread count and `OCR_DET_MAX_SIDE=1280` shrinks the text detection size if a host is slow.

## How well it reads

I rendered 25 labels in code with real regular and bold fonts, so the right answer for each is known. They hold 31 targeted rows, such as "title-case warning heading is flagged" and "700 mL is not flagged", and all 31 come out as expected. Rows the case does not target must not report a disagreement, and none do.

I also degraded the clean label and the title-case label five ways: rotated 8 degrees, perspective skew, glare, Gaussian blur at 1.5, and JPEG at quality 40. All 12 rows kept their result in every case. The test that matters is that a degraded picture never shows Matches where the clean one doesn't, and it passes. These degradations are mild. A phone photo with heavy glare over the warning would do worse, and the app would say "Look at this" or "couldn't read" before it said Matches.

I did not run real approved labels from the Public COLA Registry. That is the first thing I'd add.

## What I didn't build

- COLA integration. The brief says standalone.
- Approving or rejecting. That stays with the agent.
- Judging whether a brand name is misleading (27 CFR 5.64).
- Allergen, sulfite, aspartame and neutral-spirits statements.
- Type size in millimeters. TTB doesn't routinely measure it either.
- Bold detection. See "What I found".
- Matching the name and address against the application. The app only checks that the statement is there.
- Separate-and-apart, second-warning, and same-field-of-vision checks.
- A shared cache for the same back label across a batch.
- Non-English labels.
- User accounts and an audit log. Nothing is written to disk. Batch results sit in memory for 24 hours.

## Run it yourself

```
docker build -t label-check .
docker run -p 8000:8000 label-check
```

Then open http://localhost:8000. The container listens on `$PORT` if it is set. `/health` (also `/healthz`) reports the text reader's warm-up time. A check that runs past `CHECK_TIME_LIMIT` seconds (default 10) returns the "taking too long" message with status 503.

To run the tests:

```
pip install -r requirements-dev.txt
pytest
```

To regenerate the labels: `python labels/make_labels.py`, and the batch files: `python labels/make_batch.py`.

The same image runs on Azure App Service for Containers or Azure Container Apps. On Azure it stays one copy that does everything (`scripts/deploy_azure.ps1` deploys it). For App Service: `az webapp create --resource-group <group> --plan <plan> --name <app> --deployment-container-image-name ghcr.io/callmesteve/ttb-label-check:latest`, with the setting `WEBSITES_PORT=8000`.

Network use: the app talks to one address, the one you open it from. If your network lets you load the page, every feature works, because there is nothing else for it to reach. The text reading runs inside the app. A test in the repo runs a full check with outbound network access blocked.

Versions: Python 3.12, rapidocr 3.10.0, onnxruntime 1.31.0. Models: whatever RapidOCR 3.10.0 installs by default (PP-OCRv6 small detection and recognition).

Built on: Google Cloud Run in us-central1, as two services from one image, each 4 vCPU and 8 GiB. The front service handles single checks. The batch service runs as a single instance because batch jobs live in memory. The Azure Container Apps script, `scripts/deploy_azure.ps1`, runs the same image as one copy.

## Questions I'd ask next

- Sarah: which mismatches cause the most rejections today, so the first rows can match that order?
- Marcus: which Azure region, and is Azure OpenAI allowed in the agency tenant, for badly photographed labels?
- Dave and Jenny: which checklist items do you want to see first on the screen?
- Janet: what does an importer's batch look like on disk, and how are the front and back pictures named?
- Whoever owns the process: does the agency accept "ABV" as written on a label, or only the short forms in the rule?
