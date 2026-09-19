# S45 C1 readback external-supervision protocol

Status: source preparation only.  This protocol defines the only future execution route;
it is not a launch authorization and does not claim that C1 has completed.  The
supervisor is a reversible label-level derivation of the reviewed S40 v3.3 external
supervisor at `work/S40_result_readback/supervise_readback.py`, SHA-256
`f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238`,
with C1-specific source, terminal-binding and preflight validators installed before the
reviewed process monitor is invoked.

## Source-review gate

The following files are intentionally absent at preparation time and must be created by
three different non-author roles after reviewing the final candidate hashes:

- `SOURCE_REVIEW_PRIMARY.json`: schema `s45-c1-readback-source-review-v1`, kind
  `primary`, status `PASS_S45_C1_READBACK_SOURCE_REVIEW`;
- `SOURCE_REVIEW_ADVERSARIAL.json`: the same schema/status, kind `adversarial`;
- `SUPERVISOR_SOURCE_REVIEW.json`: schema
  `s45-c1-readback-supervisor-source-review-v1`, status
  `PASS_S45_C1_READBACK_SUPERVISOR_SOURCE_REVIEW`.

Both worker reviews must bind exact hashes for `readback.py`, `PROTOCOL.md`, the reviewed
S40 v3.3 parent, and `preparation_receipt.json`.  They must record `executed=false`,
`c1_payload_bytes_read=0`, `pixels_decoded=0`, `scientific_arrays_mapped=0`, empty
`blocking_findings`, distinct reviewer roles and
`author_role=/root/c1_readback_builder`.  The supervisor review must bind exact hashes
for `supervise_readback.py`,
`SUPERVISOR_PROTOCOL.md`, both reviewed S40 parent sources, the preparation receipt and
both worker reviews; it has the same zero-execution boundary and records
`author_role=/root`, because the root agent added the terminal timestamp validator.
All three reviewer roles must be distinct and may equal neither actual author role.
The eventual caller supplies each review file SHA and the supervisor rechecks every
field and file identity before touching terminal C1 evidence.

## Required `terminal_binding_01.json`

The binding is created once only after the C1 generation process has terminated and all
referenced files are stable.  It has schema `s45-c1-terminal-binding-v1`, status
`FROZEN_C1_TERMINAL_SUCCESS_AND_FULL_ARCHIVE_BINDING`, `row=C1`, and these exact blocks:

- `manifest`: canonical C1 manifest path and SHA;
- `external_receipt`: `execution_01/receipt.json` path and actual terminal SHA;
- `worker_receipt`: sibling path and SHA named by the external receipt;
- `full_resource_gate`: sibling path and SHA with the C1 resource-gate PASS;
- `runtime_loading`: C1 output path and SHA with the C1 component-loading PASS;
- `observation_summary`: C1 output path and SHA named by the worker receipt;
- `archive_manifest`: C1 `archive/manifest.json` path and SHA named by the worker
  receipt, with `ARCHIVE_COMPLETE`, no missing required names and zero failed captures;
- `trace_events`: C1 `trace/events.jsonl` path and SHA named by the worker receipt;
- `terminal_reviews.external_execution` and `terminal_reviews.archive_trace_metadata`,
  each with its actual path and SHA;
- `formal_readback_paths`: the exact absent `supervision_01` and `executed_01` paths.

The external terminal review uses schema `s44-c1-terminal-evidence-review-v1`, status
`PASS_S44_C1_TERMINAL_EXECUTION_EVIDENCE_REVIEW`.  The archive/trace review uses the same
schema and status `PASS_S44_C1_ARCHIVE_TRACE_METADATA_REVIEW`.  They must bind the same
manifest/external/worker/archive/trace SHA set, have distinct non-author reviewer roles,
empty blockers, and make no quality, scoring, method or novelty claim.  This metadata
review gate does not replace the eventual worker's full archive/body readback.

The supervisor parses the UTC timestamps rather than trusting a declaration flag.  It
requires the strict content order
`external_receipt.completed_utc < each terminal_review.reviewed_utc <=
terminal_binding.created_utc`; every timestamp must be timezone-aware ISO-8601.  The
binding field `created_after_terminal=true` remains a required declaration, but it is
not accepted as evidence of this order by itself.

The terminal binding must not contain placeholder hashes, `PENDING` identities, missing
files or inferred success.  Its SHA, and every SHA it names, is checked at both start and
close.  The supervisor validates the external receipt's clean zero-return terminal
status, its closed two-batch trace boundary, the worker receipt, resource gate,
component-loading receipt, archive manifest and trace hash before creating a formal
supervision directory.

## Accepted future command

The command below becomes meaningful only after the preparation and all five future
review/binding files exist with actual hashes.  Angle-bracket tokens are documentation,
not placeholder artifacts and must never be written into a JSON receipt.

```sh
PROJECT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
"$PROJECT/.venv-cut3r/bin/python" -B \
  "$PROJECT/work/S45_c1_result_readback/supervise_readback.py" \
  --supervisor-sha256 '<actual final supervisor source SHA>' \
  --preparation-receipt-sha256 '<actual preparation receipt SHA>' \
  --worker-review-primary-sha256 '<actual primary review SHA>' \
  --worker-review-adversarial-sha256 '<actual adversarial review SHA>' \
  --supervisor-review-sha256 '<actual supervisor review SHA>' \
  --terminal-binding-sha256 '<actual terminal binding SHA>' \
  --execution-directory "$PROJECT/work/S45_c1_result_readback/supervision_01" \
  --out "$PROJECT/work/S45_c1_result_readback/executed_01"
```

There is no arbitrary child command.  After all preflight checks, the inherited monitor
constructs only the fixed local scientific-Python command for `readback.py`, passing the
manifest and generation receipt obtained from the terminal binding.  It fixes
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`VECLIB_MAXIMUM_THREADS` and `NUMEXPR_NUM_THREADS` to 1; disables user-site and online
model access; applies a single 300-second total wall limit, 2 GiB sampled process-tree
RSS limit and 10 GiB free-disk floor; records and terminates descendants on failure; and
allows no retry.

Freshness uses `os.path.lexists` before resolution, so a file, directory, live symlink or
broken symlink occupies a reserved path.  Complete source, review, terminal and output
preflight occurs before `supervision_01` is created.  A preflight failure is preserved in
a unique `preflight_failure_*.json` file and does not burn the formal attempt.  Once the
formal directory exists, the reviewed S40 monitor's durable ticket, monitor, stdout,
stderr and terminal receipt rules apply; partial `executed_01` content is retained.

The strongest successful outer status is
`C1_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW`.  It means only that the bounded
saved-output reader returned its narrow identity/cache-consumption PASS and all bound
files remained stable.  A separate result review must still inspect the report and
receipts.  It cannot certify image quality, camera compliance, exact-original VMem
equivalence, C1 metric outcome, method gain, cohort completion or novelty.
