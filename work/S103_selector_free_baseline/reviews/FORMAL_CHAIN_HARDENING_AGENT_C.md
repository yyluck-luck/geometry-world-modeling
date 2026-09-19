# S103 formal-chain minimum hardening closure

Author: `codex-agent-adversarial-review-20260916`  
Scope: read-only repair design for findings C-001, C-003, and C-004. No code change, GPU/model execution, or future-payload access was performed.

## Required invariant

The reviewed protocol must be the only root of trust. Every executable that can authorize, launch, seal, score, or accept the run must be named by an exact `{path, bytes, sha256}` descriptor in that protocol. A later artifact may add run-specific facts, but it must not introduce a new executable identity. Before opening any future payload, the scorer must be able to trace the prediction through this exact chain:

`reviewed protocol -> PRE_RUN_READY validator receipt -> frozen dispatch manifest -> launch-guard receipt -> trusted sealer -> prediction seal -> scorer -> independent recompute -> post-run validator`

Any missing link, stale SHA, wrong schema/status, false/absent safety flag, or cross-bundle path must fail closed.

## 1. Protocol bindings

Add one frozen `protocol.formal_execution` object. The minimum fields are:

```json
{
  "bundle_root": "/home/yliutz/gwm_formal_bundle_s103_scene13_w001_v4",
  "bundle_preparer_ref": {"path": ".../prepare_formal_bundle_s103.py", "bytes": 0, "sha256": "..."},
  "validator_ref": {"path": ".../validate_gate0_v2.py", "bytes": 0, "sha256": "..."},
  "predictor_ref": {"path": ".../predictor_s103.py", "bytes": 0, "sha256": "..."},
  "sealer_ref": {"path": ".../seal_predictions_s103.py", "bytes": 0, "sha256": "..."},
  "sbatch_ref": {"path": ".../run_s103_vmem_base.slurm", "bytes": 0, "sha256": "..."},
  "launch_guard_ref": {"path": ".../launch_gate0_v2_in_tmux.sh", "bytes": 0, "sha256": "..."},
  "generic_launcher_ref": {"path": ".../launch_slurm_in_tmux.sh", "bytes": 0, "sha256": "..."},
  "formal_chain_regression_receipt_ref": {"path": ".../FORMAL_CHAIN_SOFTWARE_RECEIPT.json", "bytes": 0, "sha256": "..."}
}
```

The zeroes and ellipses above are placeholders; the frozen contract must contain actual values. Keep the existing top-level `predictor_wrapper_ref`, `scorer_ref`, `verifier_ref`, `runtime_binding_ref`, and isolation receipt, but require the predictor descriptor to equal `formal_execution.predictor_ref`. Move or duplicate the existing `validator_ref` into `formal_execution` only with an explicit equality check; there must not be two independently mutable validator identities.

The software regression receipt must be code-only: it binds the exact preparer, validator, predictor, sealer, Slurm script, launch guard, generic launcher, scorer, verifier, and negative-test source hashes and reports their results. It must not embed the current contract or protocol hash, because the protocol binds the receipt and that would create a hash cycle. Candidate-specific negative-control output belongs in a later readiness or dispatch artifact, not inside the protocol-bound software receipt.

The protocol reviewer must review the final adapter-bound protocol after all these refs are present. Changing any executable afterward necessarily changes the protocol SHA and invalidates the review.

## 2. `prepare_formal_bundle_s103.py`

Before executing any supplied program or creating the target directory, the preparer must:

1. Load the contract; require contract schema `gwm-gate0-staged-v2`, protocol status `FROZEN`, and a non-null protocol review descriptor.
2. Hash its own `__file__` and require path/bytes/SHA equality with `formal_execution.bundle_preparer_ref`.
3. Resolve every supplied `--validator`, `--predictor`, `--sealer`, and `--sbatch` path and require exact path/bytes/SHA equality with the matching protocol ref. Merely recording a caller-selected SHA is forbidden.
4. Resolve the launch guard, generic launcher, software receipt, scorer, verifier, runtime binding, and isolation receipt from protocol refs and verify their bytes/SHA even if they are not copied into the prediction bundle.
5. Require `--target` to equal the canonical, non-symlink `formal_execution.bundle_root`; require it not to exist.
6. Run only the now-verified validator.

The validator receipt is acceptable only if all of these hold:

- schema is `gwm-gate0-staged-v2`;
- `stage == "pre-run"`;
- `status == "PRE_RUN_READY"`;
- `pre_run_ready is true`;
- `errors == []`;
- `opens_future_outcome_files is false`;
- receipt `run_id`, `scope`, and canonical `protocol_sha256` equal the contract;
- the process exits zero.

The frozen dispatch manifest must contain `bundle_root`, contract and canonical protocol SHA, validator-receipt SHA, and the SHA of every formal-execution ref listed above. It must also bind the runtime binding, isolation receipt, run ID, scope, and execution-boundary ID. Copy only the exact contract, predictor, sealer, and Slurm files just verified; copying the validator too is recommended for reproducibility. After copying, recompute each destination SHA and compare it to both the protocol and dispatch manifest before atomically renaming the directory.

## 3. Launch guard and Slurm binding

The launch guard must independently repeat the full contract-to-file comparison; it must not trust hashes merely because the preparer wrote them into the manifest.

It must verify:

- its own path/bytes/SHA against `formal_execution.launch_guard_ref`;
- the generic launcher's identity against `generic_launcher_ref`;
- the actual validator against `validator_ref`, even when `GWM_GATE0_V2_VALIDATOR` is set;
- the submitted Slurm script against `sbatch_ref`;
- contract, manifest, predictor, sealer, and optional copied validator all reside under the same canonical `bundle_root` and match the protocol and dispatch manifest;
- manifest schema/status/stage are `gwm-gate0-v2-dispatch-manifest-v1`, `FROZEN`, and `pre-run`;
- the embedded validator receipt and a fresh validator execution both meet the PRE_RUN_READY conditions above and bind the same protocol SHA;
- contract, manifest, validator, Slurm, guard, and generic-launcher hashes remain unchanged immediately before submission.

The Slurm script should derive `FORMAL_BUNDLE` from its own canonical directory, rather than a separately hard-coded path. The guard must submit the exact script inside that directory. This removes the current split-binding possibility where the checked contract/manifest and the bundle mounted by Slurm can be different directories.

The launch-guard receipt must use schema `gwm-formal-launch-guard-receipt-v1`, status `PASS`, and bind the exact contract, protocol, dispatch manifest, validator receipt, validator, predictor, sealer, Slurm, launch guard, generic launcher, bundle root, run ID, scope, and execution-boundary SHA/values. Write it atomically and never overwrite it.

## 4. `seal_predictions_s103.py`

The trusted sealer must verify before creating a success seal:

- its own bytes/SHA equal both `protocol.formal_execution.sealer_ref` and `dispatch_manifest.sealer_sha256`;
- contract schema is `gwm-gate0-staged-v2` and protocol status is `FROZEN`;
- dispatch schema/status/stage are correct;
- actual contract SHA, canonical protocol SHA, predictor SHA, Slurm SHA, validator SHA, bundle-preparer SHA, runtime-binding SHA, and execution-boundary ID equal both protocol and dispatch bindings;
- predictor receipt schema/status are `s103-vmem-development-prediction-v1` and `PREDICTION_COMPLETE`;
- predictor exit code is zero;
- predictor receipt run ID, protocol/contract identity if added, and execution boundary match;
- `future_outcome_files_opened is false`, `future_gt_opened is false`, and `unauthorized_input_reads == 0`;
- exactly the required prediction arrays and prediction receipt are present; required array shapes, dtypes, finiteness, bytes, and SHA match the predictor receipt. Unexpected output files must either be rejected or explicitly allowlisted and typed.

The success seal must include its own schema/status, `future_scoring_permitted: true`, `prediction_complete: true`, `future_outcome_files_opened: false`, `future_gt_opened: false`, `unauthorized_input_reads: 0`, and exact SHA bindings for contract, protocol, dispatch manifest, predictor receipt, predictor, sealer, Slurm, validator, execution boundary, and every sealed output. A failed predictor may receive an immutable failure seal, but it must set `future_scoring_permitted: false` and can never satisfy scorer admission.

## 5. `scorer_s103.py`

Add required inputs for the dispatch manifest and launch-guard receipt, each accompanied by an expected SHA or supplied as already hashed descriptors. Before calculating `outcomes_first_opened_at_utc` or resolving/reading a future record, the scorer must verify:

1. Its own identity equals `protocol.scorer_ref`.
2. Contract schema/status and canonical protocol SHA are correct.
3. Dispatch schema/status/stage are correct and its SHA equals the seal's `dispatch_manifest_sha256`.
4. Every dispatch component SHA equals the corresponding reviewed protocol ref, including validator, predictor, sealer, Slurm, preparer, launch guard, generic launcher, runtime binding, and software receipt.
5. Launch receipt schema/status are `gwm-formal-launch-guard-receipt-v1` and `PASS`; its contract, protocol, dispatch, validator receipt, component hashes, bundle root, run ID, scope, and execution boundary equal the contract and dispatch manifest.
6. Seal schema/status are `s103-prediction-seal-v1` and `PREDICTION_SEALED`; `prediction_complete` and `future_scoring_permitted` are true; both future-open flags are false; unauthorized reads are zero; predictor exit code is zero.
7. Seal contract/protocol/dispatch/predictor/sealer/validator/Slurm and execution-boundary bindings agree transitively with the protocol, dispatch, and launch receipt.
8. The sealed prediction path is under the declared job output root, has the exact sealed bytes/SHA, and has the frozen shape/dtype/finiteness.
9. All relevant timestamps are timezone-aware and ordered: launch guard no later than predictor completion, predictor completion no later than seal, and seal strictly before the first future open.

Only after every check passes may the scorer set the first-open timestamp and read a future RGB byte. Every rejection test must prove that zero future bytes were opened.

## 6. Post-run validator

The post-run contract must add descriptors for the dispatch manifest, launch-guard receipt, prediction seal, scoring receipt, metrics, and independent recompute. The validator must verify artifacts and cross-bindings without relying on filenames alone.

Minimum post-run checks are:

- all pre-run checks still pass against unchanged protocol refs;
- dispatch and launch receipts meet the same schema/status/SHA checks required by the scorer;
- seal meets the same schema/status/flags and transitive provenance checks required by the scorer;
- scoring receipt schema/status are `s103-post-seal-rgb-scoring-receipt-v1` and `RGB_SCORE_COMPLETE_PENDING_INDEPENDENT_RECOMPUTE`;
- scoring receipt binds the exact seal, dispatch, launch receipt, scorer SHA, protocol SHA, metrics SHA, run ID, and first-open timestamp;
- first-open timestamp is after the sealed timestamp, and the seal binds a predictor completion time no later than sealing;
- independent recompute schema/status are `s103-independent-rgb-recompute-v1` and `METRICS_RECOMPUTED_MATCH`, verifier SHA equals `protocol.verifier_ref`, reviewer independence passes, and recompute binds the exact metrics and scoring receipt;
- acceptance is `POST_RUN_ACCEPTED` only when every error list is empty. Otherwise status is `BLOCKED`.

The validator may hash declared output and receipt artifacts, but pre-run mode must continue to avoid opening future payloads.

## 7. Required negative tests

All tests below are CPU/software-only. Scoring tests must use a future-payload canary that records or raises on first read, and every expected rejection must assert that the canary was not touched.

1. **Fake validator:** a caller-supplied validator emits perfect PRE_RUN_READY JSON but its SHA differs from `protocol.validator_ref`; preparer rejects and creates no target.
2. **Modified trusted validator:** one-byte change after contract review; preparer and launch guard both reject.
3. **Modified sealer:** one-byte change or alternate `--sealer`; preparer rejects before bundle creation.
4. **Modified Slurm:** one-byte change or altered mount; preparer rejects, and launch guard independently rejects a tampered bundled copy.
5. **Validator environment override:** `GWM_GATE0_V2_VALIDATOR` points to a fake validator; launch guard rejects despite valid-looking output.
6. **Modified launch guard/generic launcher:** self-hash or paired-launcher mismatch rejects before tmux/Slurm creation.
7. **Cross-bundle mix:** valid contract/manifest from bundle A with Slurm, predictor, sealer, or mounted root from bundle B; launch guard rejects.
8. **Manifest tamper:** alter any component SHA, bundle root, run ID, scope, boundary ID, or embedded validator receipt; launch guard, sealer, and scorer reject.
9. **Stale PRE_RUN_READY:** validator receipt binds an older protocol SHA or validator SHA; preparer and guard reject.
10. **Forged seal:** manually create a seal with correct run ID/protocol SHA but no trusted dispatch/launch/sealer bindings; scorer rejects before future access.
11. **Seal flag matrix:** wrong/missing schema or status; `future_scoring_permitted` false/missing; `prediction_complete` false/missing; either future-open flag true/missing; unauthorized reads nonzero/missing; predictor exit nonzero. Every case rejects before future access.
12. **Prediction mutation:** modify, replace, symlink, truncate, or relocate the prediction after sealing; scorer rejects before future access.
13. **Timestamp forgery/order:** naive timestamps or launch/predict/ seal/open timestamps out of order; scorer and post-run validator reject.
14. **Post-run provenance omission:** remove or mismatch dispatch, launch, sealer, scorer, verifier, metrics, or recompute bindings; post-run validator returns `BLOCKED`.
15. **Stale software receipt:** protocol points to a receipt containing an old Slurm SHA or a candidate-specific v5 negative control; pre-run validator rejects the receipt/component mismatch.
16. **Positive closure:** exact reviewed components create one bundle; guard accepts it; trusted sealer creates a valid synthetic seal; scorer admission reaches the future-open boundary only after all provenance checks; independent recompute and post-run validation accept matching synthetic metrics.

## Acceptance condition

C-001 is closed only when fake validator/sealer/Slurm/launcher artifacts cannot create or launch a bundle, even if they emit syntactically valid receipts. C-003 is closed only when a fabricated seal cannot reach the first future byte. C-004 is closed only when the protocol-bound software receipt records the exact current component hashes, contains no stale candidate-specific assertion, and its stale-receipt negative test passes.
