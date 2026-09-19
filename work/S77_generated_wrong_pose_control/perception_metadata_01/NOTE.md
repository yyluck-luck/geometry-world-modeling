# Perception Test annotation-only access and schema screen

**Outcome: official sample URL and documented schema confirmed; actual sample download blocked by two TLS failures. No annotation body or video was received. No eligibility decision is supported yet.**

## Exact official route and size limits

- [Sample annotations](https://storage.googleapis.com/dm-perception-test/zip_data/sample_annotations.zip): official README labels this as **3 MB**, a ZIP archive containing JSON annotations. This is a documentation size, not verified Content-Length. Exact archive bytes, member list, compression method and expanded size remain unknown because neither attempt reached an HTTP body.
- Smaller documented annotation route: [multiple-choice training annotations](https://storage.googleapis.com/dm-perception-test/zip_data/mc_question_train_annotations.zip), **85 kB according to README**. This is another ZIP, not a direct JSON route. It supplies a task subset and cannot replace sample object tracks, temporal links or full annotations. Not downloaded here.
- Verified existing direct JSON route: [training cut-frame mapping](https://storage.googleapis.com/dm-perception-test/misc/cut_frame_mapping_train.json), previously fetched39,498 bytes and2,185 keys (prior metadata receipt). This is only a cutoff map, not question/object/action annotations. Its train-split scope must be joined to actual sample IDs/splits; the existing count discrepancy remains unresolved.
- The inspected official README does **not** document a smaller remote direct-JSON equivalent of complete sample annotations. No undocumented endpoint or archive-internal URL was guessed or probed.

## Actual attempts

Attempt01 used Python HTTPS with default certificate verification and a4,999,999-byte body bound. It failed with SSL UNEXPECTED_EOF_WHILE_READING. Attempt02 used curl HTTP/1.1, default TLS, zero retry,35-second cap and the same4,999,999-byte limit; it returned35 and zero body bytes. Both are preserved separately. No certificate bypass, retry escalation, video request or third network attempt occurred.

## Schema evidence and interpretation

SCHEMA_REPORT.json contains only the official documentation's field names and whole-dataset counts, **not observed sample structure**. Relevant keys include object IDs, parent_objects, frame_ids, timestamps, is_masked, video frame_rate/num_frames, split and is_cup_game. Question fields include answer_id/answers; their values were not requested, inspected or copied. Documentation categories must not be assumed to be top-level JSON keys. Sample record counts, split coverage, object-action linkage, cutoffs and temporal eligibility remain unverified.

## Smallest subsequent safe-inspection plan

1. On a later authorized access attempt, fetch the same documented sample ZIP only, strict TLS, one bounded attempt, total<5MB. Record actual headers, bytes and SHA before parsing. No video, model or new scientific metric. Do not manufacture success if TLS remains broken.
2. Inspect the central directory without extracting. Reject absolute paths, traversal components and symbolic links; bound each member<=80MB and total expansion<=100MB before opening. Require expected JSON/text member types; do not execute archive content. Prefer in-memory access to avoid filesystem extraction entirely.
3. Produce schema keys, value types and collection counts only. Treat **all semantic leaves as opaque**, specifically question, options, answer_id, answers, label, label_id, bounding-box/state/track values and future suffix contents. Do not dump representative rows. Parse tree traversal may count containers but must never print their leaf values.
4. Have root freeze the exact non-outcome metadata eligibility fields and split/cutoff-join rules before any value-level screening or future inspection. Availability of IDs alone does not certify a persistent-state task, distracting interval, genuinely held-out future or a qualified consumer. A later explicit screen may find zero eligible sample cases; preserve that outcome.

This is metadata feasibility preparation, not a dataset experiment, scientific validation or a completed download. Source: the locally saved [official README](https://github.com/google-deepmind/perception_test), SHA in SCHEMA_REPORT.json.
