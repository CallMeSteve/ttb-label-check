# Approach

## The problem as I understood it

TTB agents check a label against an application by eye, using a printed checklist. They need a tool that does the checklist in about five seconds, shows its evidence, works for one label or three hundred, and runs where the network blocks outside services. It has to be usable by someone who has never used it, and it must not make the decision for them.

## Requirements and where each is met

| Need | Where it is met |
|---|---|
| Brand, ABV and warning checked | Single check, one row per item, in the order of the paper checklist |
| About 5 seconds | Measured, not promised. Every result shows its time. `docs/latency.md` holds the numbers and `scripts/measure_latency.py` makes them |
| Easy for a 73-year-old | One page, one button, 20 px type, words with a symbol and a color, crops beside each row, no zoom |
| Batch of 200 to 300 | Drop pictures or a zip. No spreadsheet needed. An optional CSV adds comparisons |
| Blocked outside network | One origin, no outside calls, a test with outbound connections blocked |
| STONE'S THROW is the same as Stone's Throw | Matched on the words with capitals and punctuation removed, citing the rule |
| Prints his emails | A Print button and a print stylesheet |
| Exact warning wording, caps | Word by word comparison to 27 CFR 16.21 and a capitals check on the first two words |
| Smaller font, tricks | Not measured. See limits |
| Bad angles and glare | EXIF rotation and the reader's angle classifier. Low confidence moves a row to "Look at this" and never to "Matches" |
| Standalone, no COLA | No integration |
| Little stored data | Nothing written to disk. Pictures are dropped after the crops are cut. Batch results stay in memory for 24 hours |
| Azure shop | The same container runs on Azure Container Apps or App Service |

## Where the AI is, and where it isn't

The text reading is a neural OCR model, RapidOCR running the PP-OCR family on ONNX Runtime, inside the app. Everything after that is rule checks against regulation text. I chose rules for the decisions because they have to give the same answer every time and say which rule they applied. A language model would add a call that can't be explained row by row, and a network path this agency blocks.

Where a vision-language model would help next is badly photographed labels, where the reader returns low confidence. It would run inside the agency's Azure tenant, and it would only suggest text for a row. It would not set a status.

## How each check works

**Folding.** Case is removed, apostrophes and periods are deleted, other punctuation becomes a space, `&` becomes AND, and spaces are collapsed. Stone's Throw and STONE'S THROW both become STONES THROW. I made one change from my first plan: a hyphen becomes a space instead of being deleted, so SINGLE-BARREL and SINGLE BARREL fold the same.

**Brand name.** The app searches the label for the typed name. Lines that start a "Bottled by" statement are left out of the search, because the producer's name in the address is not the brand on the front. An exact fold match is Matches. If every difference is a shape the reader confuses (0 and O, 1 and I, rn and m, at most one per five letters), the row is Look at this. Anything else is a disagreement, and the row also shows the biggest text on the label.

**Class or type.** Every typed word must be on the label, with whisky and whiskey treated as one word. A word with legal meaning (straight, blended, bottled in bond, light, flavored, imitation) that is on one side only is a disagreement, with a sentence saying so.

**Alcohol content.** The app finds percent statements and checks their form against the three word orders in the rule. "ABV" is not on the list of short forms, so it gets Look at this and not a failure, because I could not confirm agency practice. Proof must equal twice the percent. A class such as rum or bourbon needs at least 40 percent. Table wine can't be over 14 percent. A typed value is compared exactly, because the rule's tolerances are for lab tests.

**Net contents.** Amounts are converted to mL. Spirits need a metric statement from the approved list, and 700 mL is on it. Wine has its own list and whole liters above 3 L. Beer needs U.S. units, and metric alone fails. A missing statement is Look at this, because it can be molded into the glass.

**Name and address.** The app checks that a "Bottled by" or similar statement is there, and for imports an "Imported by" statement.

**Government warning.** The canonical text is stored as one paragraph and compared word by word with the label's lines. Each difference is either "the reader may have misread" (confusable shapes, a changed capital, a missing mark) or "the wording is different" (an added, missing or changed word, or a missing colon). The first two words must be capitals, judged on the raw reader output. Text after the end of the warning is ignored. Low confidence can't produce Matches.

**Bold.** I did not build a bold detector. I planned one that compared stroke width in the header with the rest of the line. Then I decided against shipping a measurement that could say "bold confirmed" on a blurry photo. The rule also requires that the rest of the warning is not bold, and a check that gets one direction right and the other wrong is worse than none. So the warning row always shows the crop and asks the agent to confirm both. I set the headline so a clean label still reads "Nothing for you to look at" and a line under it points to the one check by eye.

## Assumptions

- The agent types or uploads the application values.
- Labels are in English.
- Up to 4 pictures per application, and up to 300 applications per batch.
- One product type per batch unless the spreadsheet says otherwise.
- Pictures are not stored.
- Pictures are JPG, PNG or WEBP and under 15 MB each. A batch is under 400 MB.

## Trade-offs and limits

- Bold is left to the agent, as above.
- Type size is not measured. TTB doesn't routinely measure it either.
- Glare and steep angles lower the reader's confidence and send rows to Look at this. My degraded set is mild, and the app has not been tested on real phone photos of bottles.
- The batch store is in memory and does not survive a restart. A restart also drops running batches.
- Memory: each batch worker loads its own copy of the models. Four workers plus the web process need a few gigabytes. `BATCH_WORKERS` sets the pool size.
- Batch throughput is limited by CPU. On my PC, 150 applications took 165 s with 4 workers.
- Rendered labels are clean by construction. They show the rules work. They do not show the reader works on every label in the world.

## Latency work

I measured the reader on my PC before building the pages. A two-picture check took 2.5 s on one ONNX thread, 1.8 s on two, 1.5 s on four and 1.3 s on eight. Shrinking text detection to 1280 px on the long edge saved about 10 percent and kept all rendered cases correct, so it is off by default and available as `OCR_DET_MAX_SIDE`. The batch workers use one thread each, because the pool already supplies parallel work. The engine loads once at start-up and runs a warm-up read, so the first request is not the slow one.

## Test labels

Labels are drawn in code with DejaVu Sans, DejaVu Sans Bold and Liberation Serif, so the exact wording, case and weight are known. The 25 cases include the traps from the regulations: a 700 mL spirits bottle that must not be flagged, beer in mL only, table wine at 15 percent, "ABV" written out, and rum at 35 percent. Degraded copies of two cases test that a worse picture never turns a non-match into Matches.

| Degradation | Result |
|---|---|
| rotate 8 degrees | all 6 rows unchanged on both labels |
| perspective | all 6 rows unchanged on both labels |
| glare | all 6 rows unchanged on both labels |
| blur (radius 1.5) | all 6 rows unchanged on both labels |
| JPEG quality 40 | all 6 rows unchanged on both labels |
