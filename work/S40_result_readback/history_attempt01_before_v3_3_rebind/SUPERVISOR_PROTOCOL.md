# S40 saved-output readback external-supervision protocol

This protocol covers only the external process supervisor for the already reviewed
`readback.py`.  It does not execute S40 generation, import a model, read an archived
tensor, or certify video quality.  The supervisor source and this protocol must receive
a different-author source review before the first real readback launch.

## Accepted invocation

`supervise_readback.py` accepts the six run bindings below plus two frozen-source
identity tokens: `--supervisor-sha256` and `--supervisor-review-sha256`.  The first must
identify the exact supervisor version reviewed by a different role.  The second binds
the fixed local `supervisor_source_review.json`, whose PASS record names that supervisor
SHA and this protocol SHA.  Both files are checked before spawn and again at close.

1. the final attached S40 manifest absolute path and file SHA-256;
2. the completed S40 generation external `receipt.json` absolute path and file SHA-256;
3. one fresh supervisor evidence directory; and
4. one separate fresh readback output directory.

Both fresh directories must be direct children of `work/S40_result_readback`, must be
absent at entry, and must not overlap each other, the S40 generation output, or the S40
generation execution directory.  The manifest must be a final
`FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION` record.  The generation receipt must be a
terminal `DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW` record for
that same manifest, with return code zero, no limit or surviving-descendant field, two
closed trace batches, and the bound successful worker receipt.  These checks read small
JSON metadata only.

The command line is:

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
"$S40_ROOT/.venv-cut3r/bin/python" -B \
  "$S40_ROOT/work/S40_result_readback/supervise_readback.py" \
  --supervisor-sha256 '<different-author reviewed supervise_readback.py SHA-256>' \
  --supervisor-review-sha256 '<supervisor_source_review.json SHA-256>' \
  --manifest '<final attached S40 manifest absolute path>' \
  --manifest-sha256 '<actual manifest file SHA-256>' \
  --s40-execution-receipt '<actual S40 execution_01/receipt.json absolute path>' \
  --s40-execution-receipt-sha256 '<actual generation receipt file SHA-256>' \
  --execution-directory "$S40_ROOT/work/S40_result_readback/supervision_01" \
  --out "$S40_ROOT/work/S40_result_readback/executed_01"
```

There is no arbitrary-command option.  After preflight, the supervisor constructs only
this child command:

```text
<project>/.venv-cut3r/bin/python -B <project>/work/S40_result_readback/readback.py
  --manifest <bound manifest> --manifest-sha256 <bound manifest SHA-256>
  --execution-directory <parent of the bound S40 generation receipt>
  --launch-receipt-sha256 <bound S40 generation receipt SHA-256>
  --out <fresh readback output> --seconds 300
```

## Frozen source identities

The supervisor verifies these exact existing identities before spawn and again at close:

- `readback.py`: `4c7a4208c4a67b003bae7b5574b48ce44d6034797bf2e9c5ab021e4d04e4cbf6`
- `PROTOCOL_DRAFT.md`: `b4887316240bc511cfde2d4fec5d31989ffa1a854be4da56a973e28cca0d7b2c`
- `source_review_v2.json`: `ea599804589dc4c10b2ca65c972bbf1ae8a1c3c04c327f7605c5a45e2f08ec19`
- S40 `launch_generation.py`: `8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860`

The caller-supplied supervisor and source-review SHA-256 values are mandatory; a
supervisor does not establish its own review merely by hashing itself.  The review must
declare distinct author and reviewer roles, zero blocking findings, no execution, and
the exact supervisor/protocol pair.  The exact protocol SHA-256 is pinned in the
supervisor source.  It records these identities in the exclusive launch ticket and
rehashes them at close.  The manifest and both generation receipts are rehash-checked
at close as well.  Any mismatch or drift forces a failed supervisor status.

## Fixed resource boundary

The child starts in a new session with the five numerical-library thread variables fixed
to `1`: `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`VECLIB_MAXIMUM_THREADS`, and `NUMEXPR_NUM_THREADS`.  User-site imports are disabled and
Hugging Face/Transformers network access is put in offline mode.

The external monitor uses a fixed 0.5-second polling interval, records the actual maximum
poll gap, and applies one non-expandable budget to the direct child, its process group,
and descendants observed through `psutil`:

- total wall time from supervisor entry through final source/input/evidence seals,
  measured immediately before terminal-receipt serialization: 300 seconds;
- sampled process-tree RSS: 2,147,483,648 bytes;
- free disk floor: 10,737,418,240 bytes.

SIGINT and SIGTERM handlers only record a pending signal.  The supervisor checks that
flag before spawn, immediately after `Popen` has returned and the PID is recorded, and
on every monitor iteration.  Thus a signal delivered inside `Popen` cannot raise through
the child-creation assignment window or be inherited as a blocked child signal.  On a
limit, monitoring error, interruption, or
unexpected live descendant, the supervisor signals the new process group with TERM,
waits briefly, then uses KILL where required.  It also signals every previously observed
descendant by PID plus creation time and records all actions and survivors.  A 0.5-second
userspace monitor cannot prove that an unobserved sub-interval RSS spike never occurred,
or account for a process that both changes session and is reparented before its first
observation.  The fixed reviewed worker does not intentionally spawn such a process;
the receipt nevertheless limits its claim to the monitored process group and observed
descendants and calls the value `sampled_peak_process_tree_rss_bytes`.
The final receipt records `wall_seconds_before_terminal_receipt_write`; serialization and
the receipt's own fsync necessarily happen after that last measurable pre-receipt seal.

## Durable evidence and terminal interpretation

The fresh supervisor directory contains `launch_ticket.json`, `monitor.jsonl`,
`worker.stdout.txt`, `worker.stderr.txt`, and one final `receipt.json`.  Monitor rows and
the launch ticket are flushed and fsynced.  `readback.py` exclusively creates the separate
out directory and preserves its own `report.json` and terminal `receipt.json`, including
partial failure information.

The external success status is limited to
`S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW`.  It requires child return code zero,
no resource limit, no live descendant, an unchanged source/input set, and a worker status
of `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY` whose receipt identities and
report together bind the same manifest and generation receipt.  After the worker seals every file it read, the outer
supervisor validates and rechecks the complete identity set by size, mtime, ctime, device,
and inode.  It deliberately does not reread saved tensor bodies; their hashes are checked
by the fixed worker inside the bounded child.  It remains pending a different-author
result review.
It does not certify model mathematics, visual quality, long-term consistency, exact
original-SD2.1 equivalence, or novelty.

Once the supervisor evidence directory has been created and is writable, later failures
are handled inside the terminal-receipt boundary and preserve every artifact created so
far.  A malformed command line, invalid/uncreatable supervisor directory, sudden host
loss, or failure of the final filesystem write cannot promise a receipt.  The readback
output directory may remain absent when preflight fails because only `readback.py` creates
it.  There is no retry, cleanup, directory reuse, budget increase, or fallback command in
this supervisor.
