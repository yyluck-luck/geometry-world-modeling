# S58 C2 V9 readback supervisor — source draft

Status: `SOURCE_PREPARATION_ONLY_AWAITING_ACTUAL_GENERATION_TERMINAL`.
This adapts S45 C1 supervisor SHA
`825396fc5ac69ac210a6fc6021171543c830c6906bf2f9d0cf6e44ef75c23d78`.
The monitor remains a reversible label-only derivation of the S40 v3.3 supervisor,
SHA `f04b9bcd4a0e2908d2bc3ead9a732e16d4f4ef651a60541a87f37a7b37f2b238`.
Its process handling, limits, output verification and failure retention are unchanged.
C2-specific source/terminal validators and a close check supplement that monitor.
The complete supervisor, including those added validators, needs independent review;
the AST proof covers the inherited monitor, not those new validators.

## Source records retained from S45

`preparation_receipt.json` uses schema `s58-c2-readback-preparation-v1`, the status
above, author `/root/negative_result_question_triage`, exact six source/protocol/
S40-parent identities, fixed C2 manifest SHA, `terminal_binding_created=false`,
and zero C2 payload reads, decoded pixels, mapped arrays, readback/model runs.
This author receipt is not an execution review.

The inherited review files remain `SOURCE_REVIEW_PRIMARY.json`,
`SOURCE_REVIEW_ADVERSARIAL.json`, and `SUPERVISOR_SOURCE_REVIEW.json`.
Worker reviews use schema `s58-c2-readback-source-review-v1`, kinds primary and
adversarial, status `PASS_S58_C2_READBACK_SOURCE_REVIEW`, verdict
`PASS_SOURCE_NOT_EXECUTED`. They bind readback.py, PROTOCOL.md, the S40 reader and
preparation receipt. Supervisor review uses schema
`s58-c2-readback-supervisor-source-review-v1`, status
`PASS_S58_C2_READBACK_SUPERVISOR_SOURCE_REVIEW`, verdict
`PASS_SUPERVISOR_NOT_EXECUTED`, binding supervisor/protocol, S40 supervisor,
worker/protocol, preparation and both worker reviews. All require `executed=false`,
zero C2 payload reads/pixels/arrays and empty blocking_findings. Three distinct
reviewer roles must differ from the actual author above. These are the existing
S45 review slots, not added execution stages. None is supplied by this preparation.

## Required actual future terminal binding

Only after actual generation termination and terminal reviews, root may create
`terminal_binding_01.json`: schema `s58-c2-terminal-binding-v1`, status
`FROZEN_C2_TERMINAL_SUCCESS_AND_FULL_ARCHIVE_BINDING`, row C2,
`placeholder_hashes=0`, `created_after_terminal=true`, and real UTC `created_utc`.
Every reference below requires canonical absolute `path` plus actual SHA-256.
No future hash has a value in this draft.

| Binding block | Exact path relative to project |
|---|---|
| manifest | work/S47B_c2_confirmation_generation_v9/review_attachment_01/manifest.json |
| external_started | work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/started.json |
| external_receipt | work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/receipt.json |
| parent_receipt | work/S47B_c2_confirmation_generation_v9/execution_01/receipt.json |
| worker_receipt | work/S47B_c2_confirmation_generation_v9/execution_01/worker_receipt.json |
| terminal_commit | work/S47B_c2_confirmation_generation_v9/execution_01/supervisor_terminal_commit.json |
| watchdog_receipt | work/S47B_c2_confirmation_generation_v9/execution_01/watchdog_receipt.json |
| full_resource_gate | work/S47B_c2_confirmation_generation_v9/execution_01/full_resource_gate.json |
| runtime_loading | results/S47B_C2_confirmation_generation_v9/runtime_loading.json |
| observation_summary | results/S47B_C2_confirmation_generation_v9/observation_summary.json |
| archive_manifest | results/S47B_C2_confirmation_generation_v9/archive/manifest.json |
| trace_events | results/S47B_C2_confirmation_generation_v9/trace/events.jsonl |

The known start SHA is
`9eb4eaab88ff1dc7fb2c06b1fd482ff12bad8d8b1ae97ccc25f00ddbc52ef968`.
The fixed outer observer source SHA is
`5eb013808104d4baea95c25ed91c85fc18732c9523b744263679977c6d376ccf`.
The internal parent is passed to the inherited reader's launch-receipt argument
for its existing trace/archive checks. It is **not** treated as V9's outer return.
The supervisor separately requires and seals the actual external receipt.

## Fields actually checked at runtime

1. Outer receipt: `EXTERNALLY_OBSERVED_RETURN_PENDING_INDEPENDENT_TERMINAL_REVIEW`,
   integer returncode 0, external_timeout false; argv, PID and started_utc equal
   the pinned real start. Argv must be the fixed V9 launcher/manifest/execution
   invocation. Actual stdout/stderr hashes must equal those in the outer receipt.
2. Commit: schema `s47-c2-external-supervisor-terminal-commit-v2`, status
   `COMMIT_CANDIDATE_REQUIRES_OUTER_RETURN_AND_NO_ROOT_FAILURE`, outcome_status
   `RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`, standalone_success false, integer
   parent_returncode 0. Manifest/launcher, PID, parent/worker/watchdog hashes,
   execution/output paths and identities must agree with actual files.
3. Watchdog: schema `s47-c2-worker-watchdog-v2`, status
   `WATCHDOG_CONFIRMED_REGISTERED_DESCENDANTS_GONE`; cleanup_complete,
   all_registered_descendants_gone, supervisor_completed_protocol and
   canonical_execution_identity_at_close true; supervisor_liveness_lost false.
   Integer worker_returncode is 0, worker PID matches the parent's recorded child
   PID; supervisor PID, manifest/launcher and directory identities agree with commit.
4. Both exact root entries must be absent, including broken symlinks:
   `work/S47B_c2_confirmation_generation_v9/.execution_01.supervisor_failure.json`
   and `.execution_01.watchdog_failure.json` in that same directory. The binding's
   `failure_paths_required_absent` must list those two absolute paths in that order.
   Absence and execution/output/control identities are rechecked at readback close.
5. The existing V9 gate's read-only `open_launch_control_lease` calls read_frozen,
   require_published_attachment, require_launch_authorization, their successful
   prepare/authorization-attempt checks, and LaunchControlLease.validate. Its
   current prepare/attachment/authorization identities must equal the commit.
   No full resource gate, model loader, creator, launch or authorization is run.
6. Internal parent: schema `s47-c2-confirmation-launch-v1`, status
   `C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`, clean zero
   return, worker_spawned and source_unchanged_at_close true, exact worker hash,
   no limit_exceeded/unexpected_live_descendants fields. Trace boundary must close
   two batches with retained IDs [1,2,3,4] then [5,6,7,8], no failure/pending bytes.
7. Worker: schema `s47-c2-confirmation-worker-v1`, status
   `C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`, exact manifest/source,
   source_unchanged_at_close true, runtime_factory_calls=1, full_resource_checks=1;
   summary/trace/archive hashes bound. scientific_consumption_binding must equal
   the commit's, with all_required_resources_consumed true and output_identity
   equal the actual terminal output directory.
8. Resource gate: schema `s47-c2-generation-resource-gate-v1`, status
   `PASS_C2_DECLARED_GENERATION_RESOURCE_GATE`, correct manifest. Loading status
   `PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY`, matching manifest/variant,
   nonempty state_dict_loads with no missing/unexpected keys. Summary has batches.
   Archive is ARCHIVE_COMPLETE, recorded_execution, matching manifest/source set,
   zero failed captures and no missing names; actual archive/trace files match hashes.

The timestamp chain must satisfy actual start < parent completion ≤ watchdog
completion ≤ commit completion ≤ actual outer completion < each terminal review
≤ binding creation. All parsed timestamps must be timezone-aware UTC.
A provisional receipt or commit alone cannot satisfy this gate.

`terminal_reviews.external_execution` and `.archive_trace_metadata` each name
actual path/SHA. Both use `s47-c2-terminal-evidence-review-v1`, respective statuses
`PASS_S47_C2_TERMINAL_EXECUTION_EVIDENCE_REVIEW` and
`PASS_S47_C2_ARCHIVE_TRACE_METADATA_REVIEW`. Their exact `bindings` keys are
manifest_sha256, parent_receipt_sha256, external_receipt_sha256,
external_started_sha256, terminal_commit_sha256, watchdog_receipt_sha256,
worker_receipt_sha256, archive_manifest_sha256 and trace_events_sha256.
Require distinct non-root reviewer roles, executed false, empty blocking_findings,
quality_status and method_or_novelty_status NOT_EVALUATED. These reviews must be
conducted after the actual outer completion; source-only preparation cannot supply them.

## Future invocation and output boundary

The inherited CLI requires actual SHA arguments: supervisor-sha256,
preparation-receipt-sha256, worker-review-primary-sha256,
worker-review-adversarial-sha256, supervisor-review-sha256, terminal-binding-sha256;
plus absolute execution-directory and out. No runnable command with invented
hashes is emitted. `formal_readback_paths` must name direct children of this
S58 directory: supervision=supervision_01, readback_output=executed_01.
Both must be absent, including broken symlinks, until successful preflight.
Preflight failure preserves a unique non-authoritative receipt. A consumed formal
attempt is never removed or retried. The monitor fixes one numerical thread,
300-second wall time, 2 GiB sampled tree RSS and 10 GiB free disk.
All bound files are byte/stat checked at start and close.

The strongest eventual status is
`C2_READBACK_RETURNED_PENDING_INDEPENDENT_RESULT_REVIEW`.
It remains subject to result review and establishes only saved identity/cache
consumption. This draft does not certify actual generation, image quality,
rendered camera obedience, C2 metric outcome, full cohort completion or novelty.
