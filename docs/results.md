# Results on the test labels

Every rendered case, what I expected, and what the app returned on this run. A row marked MISS is a failure.

Known limit: the app does not decide whether GOVERNMENT WARNING: is bold and the rest is not. The warning row always asks the agent to confirm that by eye, so `warn_header_regular` and `warn_all_bold` are expected to say Matches on wording and capitals and are not flagged for weight.

| Case | Row | Expected | Got | |
|---|---|---|---|---|
| old_tom_clean | Brand name | MATCH | MATCH | ok |
| old_tom_clean | Class or type | MATCH | MATCH | ok |
| old_tom_clean | Alcohol content | MATCH | MATCH | ok |
| old_tom_clean | Net contents | MATCH | MATCH | ok |
| old_tom_clean | Name and address | MATCH | MATCH | ok |
| old_tom_clean | Government warning | MATCH | MATCH | ok |
| old_tom_clean_rot8 | Brand name | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_rot8 | Class or type | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_rot8 | Alcohol content | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_rot8 | Net contents | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_rot8 | Name and address | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_rot8 | Government warning | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Brand name | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Class or type | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Alcohol content | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Net contents | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Name and address | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_persp | Government warning | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Brand name | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Class or type | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Alcohol content | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Net contents | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Name and address | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_glare | Government warning | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Brand name | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Class or type | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Alcohol content | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Net contents | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Name and address | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_blur | Government warning | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Brand name | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Class or type | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Alcohol content | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Net contents | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Name and address | MATCH (same as clean) | MATCH | ok |
| old_tom_clean_jpeg40 | Government warning | MATCH (same as clean) | MATCH | ok |
| stones_throw_case | Brand name | MATCH | MATCH | ok |
| stones_throw_curly | Brand name | MATCH | MATCH | ok |
| brand_extra_letter | Brand name | DISAGREE | DISAGREE | ok |
| warn_title_case | Government warning | DISAGREE | DISAGREE | ok |
| warn_title_case_rot8 | Brand name | MATCH (same as clean) | MATCH | ok |
| warn_title_case_rot8 | Class or type | INFO (same as clean) | INFO | ok |
| warn_title_case_rot8 | Alcohol content | MATCH (same as clean) | MATCH | ok |
| warn_title_case_rot8 | Net contents | MATCH (same as clean) | MATCH | ok |
| warn_title_case_rot8 | Name and address | MATCH (same as clean) | MATCH | ok |
| warn_title_case_rot8 | Government warning | DISAGREE (same as clean) | DISAGREE | ok |
| warn_title_case_persp | Brand name | MATCH (same as clean) | MATCH | ok |
| warn_title_case_persp | Class or type | INFO (same as clean) | INFO | ok |
| warn_title_case_persp | Alcohol content | MATCH (same as clean) | MATCH | ok |
| warn_title_case_persp | Net contents | MATCH (same as clean) | MATCH | ok |
| warn_title_case_persp | Name and address | MATCH (same as clean) | MATCH | ok |
| warn_title_case_persp | Government warning | DISAGREE (same as clean) | DISAGREE | ok |
| warn_title_case_glare | Brand name | MATCH (same as clean) | MATCH | ok |
| warn_title_case_glare | Class or type | INFO (same as clean) | INFO | ok |
| warn_title_case_glare | Alcohol content | MATCH (same as clean) | MATCH | ok |
| warn_title_case_glare | Net contents | MATCH (same as clean) | MATCH | ok |
| warn_title_case_glare | Name and address | MATCH (same as clean) | MATCH | ok |
| warn_title_case_glare | Government warning | DISAGREE (same as clean) | DISAGREE | ok |
| warn_title_case_blur | Brand name | MATCH (same as clean) | MATCH | ok |
| warn_title_case_blur | Class or type | INFO (same as clean) | INFO | ok |
| warn_title_case_blur | Alcohol content | MATCH (same as clean) | MATCH | ok |
| warn_title_case_blur | Net contents | MATCH (same as clean) | MATCH | ok |
| warn_title_case_blur | Name and address | MATCH (same as clean) | MATCH | ok |
| warn_title_case_blur | Government warning | DISAGREE (same as clean) | DISAGREE | ok |
| warn_title_case_jpeg40 | Brand name | MATCH (same as clean) | MATCH | ok |
| warn_title_case_jpeg40 | Class or type | INFO (same as clean) | INFO | ok |
| warn_title_case_jpeg40 | Alcohol content | MATCH (same as clean) | MATCH | ok |
| warn_title_case_jpeg40 | Net contents | MATCH (same as clean) | MATCH | ok |
| warn_title_case_jpeg40 | Name and address | MATCH (same as clean) | MATCH | ok |
| warn_title_case_jpeg40 | Government warning | DISAGREE (same as clean) | DISAGREE | ok |
| warn_reworded | Government warning | DISAGREE | DISAGREE | ok |
| warn_missing_2 | Government warning | DISAGREE | DISAGREE | ok |
| warn_header_regular | Government warning | MATCH | MATCH | ok |
| warn_all_bold | Government warning | MATCH | MATCH | ok |
| warn_missing | Government warning | MISSING | MISSING | ok |
| proof_mismatch | Alcohol content | DISAGREE | DISAGREE | ok |
| abv_app_mismatch | Alcohol content | DISAGREE | DISAGREE | ok |
| abv_written_ABV | Alcohol content | LOOK | LOOK | ok |
| rum_35 | Alcohol content | DISAGREE | DISAGREE | ok |
| whisky_spelling | Class or type | MATCH | MATCH | ok |
| class_drops_straight | Class or type | DISAGREE | DISAGREE | ok |
| spirits_700ml | Net contents | MATCH | MATCH | ok |
| spirits_600ml | Net contents | DISAGREE | DISAGREE | ok |
| spirits_floz_only | Net contents | DISAGREE | DISAGREE | ok |
| beer_ml_only | Net contents | DISAGREE | DISAGREE | ok |
| beer_12oz_no_abv | Net contents | MATCH | MATCH | ok |
| beer_12oz_no_abv | Alcohol content | MATCH | MATCH | ok |
| table_wine_15 | Alcohol content | DISAGREE | DISAGREE | ok |
| table_wine_no_abv | Alcohol content | MATCH | MATCH | ok |
| net_missing | Net contents | LOOK | LOOK | ok |
| import_no_importer | Name and address | LOOK | LOOK | ok |

0 rows missed.

## Five real approved labels (Public COLA Registry)

TTB approved these, so any "Doesn't follow the rule" or disagreement is a false alarm. "After" types only what each record's application page holds (product type, source, brand, fanciful name; the form has no class, alcohol or net contents box), see `labels/real-cola/SOURCES.md`. "Before" is the live app on 2026-10-11, before the changes to the warning, class and net contents checks; that run also typed class, alcohol and net contents values that were guessed, not taken from the record.

"After" is run with the hosted settings (`OCR_DET_MAX_SIDE=1280`), so it shows what the public URL returns.

| Label | Before (non-matching rows) | After (non-matching rows) |
|---|---|---|
| old-elk | Government warning: Doesn't follow the rule. Net contents: Look at this. | Fanciful name: Look at this; Net contents: Look at this |
| jeffersons-ocean | Class or type: disagree (picked the 'BOTTLED FOR JEFFERSON'S' line). Alcohol content and Name and address: Not on the label. Net contents: Look at this. Government warning: Doesn't follow the rule. | Alcohol content: Not on the label; Net contents: Look at this; Government warning: Look at this |
| woodford-reserve | Class or type: disagree (picked 'THIS EXCEPTIONAL BOURBON HAS BEEN CRAFTED'). Alcohol content: Not on the label. Net contents: Look at this. Government warning: Doesn't follow the rule. | Fanciful name: Look at this; Alcohol content: Not on the label; Net contents: Look at this |
| laurel-glen | Class or type: disagree (picked '2023 RED WINE BLEND'). Government warning: Doesn't follow the rule. | all rows Match |
| common-roots | Brand name: disagree. Name and address: Not on the label. Government warning: Doesn't follow the rule. | Brand name: Look at this; Government warning: Look at this |

Known limits seen on these labels: the Jefferson's and Woodford pictures in the record carry no alcohol statement at all (it is on a panel or strip that is not in those two images), so "Not on the label" is the correct answer for the pictures given. The net contents row is Look at this when the amount is molded into the glass. Where the warning has a letter or two the reader isn't sure of, the row is Look at this with the crop and the word shown.
