# Next

Things I left out on purpose (amended spec) or noticed and did not build.

- Real approved labels from the Public COLA Registry as a false-alarm set.
- Name and address matching against form item 8. The single-check form has no field for it.
- A shared cache for a back label that repeats across a batch.
- Same-field-of-vision check for spirits (27 CFR 5.63(a)).
- Separate-and-apart, second-warning, and size advisories for the warning.
- Bold detection from stroke width. Only worth building if a test set shows it separates bold from regular on photos.
- Batch upload memory: the whole upload is held in memory until each application is read. A 400 MB cap is set in `app/batch.py`. Streaming to the workers would lift it.
- Batch results keep crops as data URIs in memory. About 50 MB for 300 applications. Regenerating them on demand would cut that.
- A favicon and a social preview image.
- Country of origin wording is shown only as a note on imports.
