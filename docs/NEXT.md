# Next

Things I left out on purpose or noticed and did not build.

- More real approved labels from the Public COLA Registry, including every panel of each record, and real phone photos of bottles.
- Name and address matching against form item 8. The single-check form has no field for it.
- A shared cache for a back label that repeats across a batch.
- Same-field-of-vision check for spirits (27 CFR 5.63(a)).
- Separate-and-apart, second-warning, and size advisories for the warning.
- Bold check by comparison: flag a warning whose heading measures the same stroke weight as the text after it. Both regular and both bold break the rule, so it needs no absolute bold threshold. Only worth shipping if it holds on real phone photos.
- Batch upload memory: the whole upload is held in memory until each application is read. A 400 MB cap is set in `app/batch.py`. Streaming to the workers would lift it.
- Batch results keep crops as data URIs in memory. About 50 MB for 300 applications. Regenerating them on demand would cut that.
- A favicon and a social preview image.
- Country of origin wording is shown only as a note on imports.
- Keep batch results past the batch service's idle sleep (about 15 minutes) with a small shared store, such as a storage bucket with a 24-hour expiry.
- Send very large photo batches in several uploads behind the scenes. Today the browser shrinks big photos, and one upload takes up to 30 MB (about 60 phone photos, or a few hundred label image files).
