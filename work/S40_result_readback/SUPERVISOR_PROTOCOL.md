# S40 saved-output readback external-supervision protocol (attempt02 rebind)

This protocol covers only the external process supervisor for the independently
double-reviewed `readback.py` v3.3 repair.  The first supervised readback is preserved in
`supervision_01/executed_01`: it failed because the first batch stored
`context_time_indices` as a Python list while the old reader required a tensor descriptor.
That failure is a readback implementation failure, not a generation or scientific
failure.  This rebind does not rerun S40 generation, import a model, run geometry
alignment, run a gate, or score or view images.  The rebound supervisor source and this
protocol must receive a different-author source review before the one fresh attempt02.

## Accepted invocation

`supervise_readback.py` accepts the six run bindings below plus two frozen-source
identity tokens: `--supervisor-sha256` and `--supervisor-review-sha256`.  The first must
identify the exact supervisor version reviewed by a different role.  The second binds
the fixed local `supervisor_source_review_v2.json`, whose PASS record names that supervisor
SHA and this protocol SHA.  Both files are checked before spawn and again at close.

1. the final attached S40 manifest absolute path and file SHA-256;
2. the completed S40 generation external `receipt.json` absolute path and file SHA-256;
3. one fresh supervisor evidence directory; and
4. one separate fresh readback output directory.

The supervisor evidence directory is fixed to the absent direct child `supervision_02`;
the worker output is fixed to the separate absent direct child `executed_02`.  Neither
basename can be replaced by a caller-selected name.  They must not overlap each other,
the S40 generation output, or the S40 generation execution directory.  The manifest must be a final
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
  --supervisor-review-sha256 '<supervisor_source_review_v2.json SHA-256>' \
  --manifest '<final attached S40 manifest absolute path>' \
  --manifest-sha256 '<actual manifest file SHA-256>' \
  --s40-execution-receipt '<actual S40 execution_01/receipt.json absolute path>' \
  --s40-execution-receipt-sha256 '<actual generation receipt file SHA-256>' \
  --execution-directory "$S40_ROOT/work/S40_result_readback/supervision_02" \
  --out "$S40_ROOT/work/S40_result_readback/executed_02"
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

- `readback.py`: `d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933`
- `PROTOCOL_DRAFT.md`: `257e1b7583b000e907cde8baf3e4e3fcefb9f2c81037ed98887d0f6367483163`
- primary `source_review_v3_3.json`: `70d4c48a6940778247763c901637e18e231b926f4733ac8edb64923ef0240484`
- adversarial `source_review_v3_3_adversarial.json`: `8ca313e712eec18d275122c95181aff987ae1ff5ceb04a880af61bb41b5a3ec7`
- `revision_v3_3_receipt.json`: `bebc80b8fccf6e8699d4768f6ffab097bcc75f6bca4a7f101ef53e827b0e2e9d`
- failed outer attempt01 receipt: `f269dc2486478e65176c38445ab97251f31a5a4ac6c9f50cbd344a73daefd5da`
- failed worker attempt01 receipt: `4b762c3061d395a6767f319a553e681dbea8fe4d90bd49e5ac8a563d36bf35c6`
- S40 `launch_generation.py`: `8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860`

The caller-supplied supervisor and source-review SHA-256 values are mandatory; a
supervisor does not establish its own review merely by hashing itself.  The review must
declare distinct author and reviewer roles, zero blocking findings, no execution, the
exact supervisor/protocol pair, the full v3.3 readback review bundle, and both preserved
attempt01 receipt identities.  The supervisor independently validates both worker
reviews, the v3.3 revision receipt, and the exact technical attempt01 failure before it
can spawn.  It also requires `executed_01/report.json` to remain absent.  The exact
protocol SHA-256 is pinned in the supervisor source.  The launch ticket records every
bound identity, and the supervisor rehashes them at close.  The manifest and both
generation receipts are rehash-checked at close as well.  Any mismatch or drift forces
a failed supervisor status.

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

The fresh `supervision_02` directory contains `launch_ticket.json`, `monitor.jsonl`,
`worker.stdout.txt`, `worker.stderr.txt`, and one final `receipt.json`.  Monitor rows and
the launch ticket are flushed and fsynced.  `readback.py` exclusively creates the separate
`executed_02` directory and preserves its own `report.json` and terminal `receipt.json`,
including partial failure information.

The external success status is limited to
`S40_READBACK_RETURNED_PENDING_INDEPENDENT_REVIEW`.  It requires child return code zero,
no resource limit, no live descendant, an unchanged source/input set, and a worker status
of `PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY` whose receipt identities and
report together bind the same manifest and generation receipt.  After the worker seals every file it read, the outer
supervisor validates and rechecks the complete identity set by size, mtime, ctime, device,
and inode.  It deliberately does not reread saved tensor bodies; their hashes are checked
by the fixed worker inside the bounded child.  Attempt01 had already stream-hashed 5,916
files and 244,804,717 bytes, including 1,951 tensor `.bin` bodies and 9 PNG bodies, before
its representation error.  It had zero successful NumPy comparisons, zero image decodes
or human views, and zero quality scores.  Attempt02 is therefore a fresh technical retry
of the repaired reader, not a claim that payload bodies were never read.  Any returned
PASS remains pending a different-author result review.
It does not certify model mathematics, visual quality, long-term consistency, exact
original-SD2.1 equivalence, or novelty.

Once the supervisor evidence directory has been created and is writable, later failures
are handled inside the terminal-receipt boundary and preserve every artifact created so
far.  A malformed command line, invalid/uncreatable supervisor directory, sudden host
loss, or failure of the final filesystem write cannot promise a receipt.  The readback
output directory may remain absent when preflight fails because only `readback.py` creates
it.  There is no retry, cleanup, directory reuse, budget increase, or fallback command in
this supervisor.
