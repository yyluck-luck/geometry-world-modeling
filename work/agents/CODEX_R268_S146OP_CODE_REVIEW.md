# R268 — S146 operational implementation review

Local Mac checkout. Review completed 2026-10-11 UTC against the source snapshot in Appendix A. Read-only CPU review; the only authored file is this report. `new_method_validated=false`; `novelty_authorization=NONE`.

**Recommendation: HOLD the unchanged chain.** The main numerical path is substantially correct, but the chain does not yet implement Amendment 3 exactly. In particular, its namespace guard allows reuse, parity compares surfel counts rather than surfel state, the availability gate accepts mismatched execution identities, and no total remaining-compute cap is enforced. Binding pre-execution provenance and observer evidence also remain incomplete. No actual TACC file, GPU state, weight, job, or generated result was accessed or verified.

There is **no demonstrated KPS-count bug, native-package lookup bug, primary weighting bug, or S140 whole-image metric mismatch**. These should not be “fixed.” The evidence below distinguishes synthetic CPU counterexamples from unknown remote conditions. This is an implementation review, not a scientific result or a new experiment authorization.

Source abbreviations: **S** = `work/S146_fresh12/`; **H** = `work/S139_crossseq_revisit/`; **P** = `data/S134_tacc/vmem_src/modeling/pipeline.py`; **R267** = `work/agents/CODEX_R267_S146_PATH_DECISION.md`. Every abbreviated citation expands to that exact path. No literature claim is needed for this review; no external citation is asserted.

## Findings table

The patch column links to exact unified diffs below. Apply only after checking the recorded source hashes; several independent hunks touch the same file. Proposed patches were not applied to production source. The focused fixes do **not** resolve all of the broader missing evidence listed in the compliance section.

| Issue | Severity | Evidence and consequence | Exact patch |
|---|---|---|---|
| F1. Namespace is not atomically fresh | HIGH | S/s146op_chain.sh:6–7 rejects only directories containing a root-level `.json`. Existing parity/replay/generation subdirectories are accepted. S/gen_s141.py:164–165 skips an existing prediction without verifying it. Concurrent launches can also both pass the check. Synthetic shell witness in Appendix B. | [P1](#p1-atomic-namespace) |
| F2. Availability gate does not establish the declared execution identity | HIGH | S/pool_op_s146.py:32 collapses duplicate receipt IDs; :38–39 omits exact target list, bank length/uniqueness, initializer, convention, consumer mapping and construction probes. A CPU fixture accepts wrong targets/`mst`/`native` and a bank with an extra frame. This is a fail-closed gap, not proof the current remote receipts are stale. | [P5](#p5-pool-identity-and-rule-2-precision) |
| F3. “Identical surfels/scales” parity is weaker than its name | HIGH | S/s146op_chain.sh:16–19 compares only surfel count and rounded scale lists, with no nonempty construction-log requirement. The expression accepts empty logs and different scales. Equal counts do not prove equal geometry. S/PROTOCOL.md:74 requires identical contexts, surfels and scales. | [P6](#p6-parity-state-and-exact-scales) |
| F4. Total remaining GPU budget and peer cleanup are absent | HIGH | Only generation has a per-worker timeout (S/s146op_chain.sh:37); parity, retrieval and replay are unbounded. T0 is reported, never enforced (:9,48). Earlier S146 compute is not subtracted. A failed first `wait` exits immediately (:25,38), leaving the other worker alive; shell fixture witnesses this. R267:114 counts all these stages toward the cap. | [P3](#p3-bounded-chain-and-process-group-cleanup) |
| F5. Seal is prediction-only in important respects | HIGH for adopted evidence contract | S/s146op_chain.sh:39–42 counts filenames, then hashes predictions, pool, aggregate retrieval receipts and plans. It omits selection/window receipts, diagnostic NPZs, parity/replay receipts, generation logs, source/input manifests and convention/metadata receipts. R267:108 requires complete planned identities and all available receipts sealed before scoring. | [P7](#p7-complete-cell-check-and-seal) |
| F6. Rule 2 differs from S139 at float32 conversion | MEDIUM, inherited; secondary comparator | H/pose_arms_s139.py:22,49–50 rounds the target pose to float32 **before** quaternion normalization. S/pool_op_s146.py:33,43 normalizes in float64 first. A valid-pose synthetic counterexample changes selected IDs (Appendix E). Existing S/build_pool_s146.py:70,86 already had this discrepancy. Actual S146 impact is unknown. | [P5](#p5-pool-identity-and-rule-2-precision) |
| F7. Optional diagnostic preparation can invalidate a saved selection | MEDIUM, conditional failure path | S/run_retrieval_s146op.py:127–128 saves selection, but NPZ export and focal preparation at :131–135 lie outside the diagnostic try at :136–140. Their exception reaches :148–150 and marks the policy blocked. R267:98,106 excludes optional-diagnostic-only failures from policy availability. | [P8](#p8-retrieval-exception-boundary-and-status) |
| F8. Unavailable policies can be labeled complete | MEDIUM; downstream pool still rejects | S/run_retrieval_s146op.py:150 emits `POLICY_UNAVAILABLE`, but :152 counts only `BLOCKED`; :153 can therefore announce `MAPS_COMPLETE_NO_DIFFUSION` with unavailable policies. CPU witness in Appendix C. | [P8](#p8-retrieval-exception-boundary-and-status) |
| F9. Filtered output can cause false failure and loses diagnostic output | MEDIUM | All worker pipelines use `grep` under `pipefail` (S/s146op_chain.sh:13,24,31,37). No matches returns 1 even if Python succeeds; full logs are discarded. Fresh successful generation normally emits matching `[done]`, so this is conditional, especially with reused/skipped outputs. | [P2](#p2-preserve-logs-without-grep-status-coupling) |
| F10. Native absolute mean has a subset denominator | LOW; primary contrast unaffected | S/analyze_s146.py:123–125 includes `nat3` only for unmerged native packages, omitting those merged with rule 3 by S/pool_op_s146.py:51–53. A fixture reports a subset mean rather than the all-window native mean. Primary `pkg(native=True)` comparisons are correct. | [P9](#p9-native-descriptive-mean) |
| F12. SSIM blocks still contain a PSNR-threshold `gate` field | LOW, misleading diagnostic schema | S/analyze_s146.py:113–120 calls the same matrix helper for both metrics; :48 tests the PSNR threshold even for SSIM. DECISION correctly uses the separate SSIM decline test (:128–133), but the extra SSIM `gate` contradicts R267:157. | [P11](#p11-do-not-label-a-psnr-threshold-as-an-ssim-gate) |
| F11. Staging parses split position instead of labels | MEDIUM, latent input-validation defect | S/stage_12scenes_s146.py:32–33 ignores `sequence0/sequence1` labels and declared counts, unlike S/PROTOCOL.md:15–19. Reordered split text reverses H/C. Current remote inputs are unverified; this does not justify restaging valid existing data. | [P10](#p10-explicit-split-labels) |

**Deployment dependency, UNVERIFIED remotely:** `S/s141_common.py` is absent from this checkout, although S/gen_s141.py:111–113 imports it and S/s146op_chain.sh:35 hashes its remote S146 path. The intended source exists at `work/S141_finetune/s141_common.py`. This is not proof that the remote copy is missing. [P4](#p4-check-deployed-dependencies-before-model-startup) moves explicit dependency/source checks ahead of costly work.

## Amendment 3 compliance and verified non-bugs

1. **Order:** the chain does parity → per-room retrieval → availability/pool → plans → exposed replay → evaluation generation → seal → scoring → analysis (S/s146op_chain.sh:10–47). That broad order is correct. It never invokes a metadata/convention validation gate; the earlier CPU script's check is a separate process (S/s146_cpu_prep.sh:7–22), and the operational chain does not verify that process's receipts or their identity. It hardcodes `gl` in step A (:24) and pool construction (S/pool_op_s146.py:55).

2. **Binding requirements still missing; HOLD remains after the focused patches.**
   - R267:90 requires pre-execution binding of adopted protocol, diagnostic inputs, staged-data/metadata/manifest receipts, actual VMem/CUT3R/helper/config/weights, environment/numeric settings and commands. S/s146op_chain.sh:7 hashes S146 scripts and protocol only. P4 checks three concrete deployed source identities; it does not establish the full contract.
   - Existing convention producers record frames/results but not detector/input hashes (S/convention_check_s146.py:35–38; S/convention_check2_s146.py:34–37). A receipt's mere existence cannot prove the reuse condition in R267:90. The main agent must bind archived evidence to the original inputs/detector or rerun only the two fixed bank checks with the original detector, then enforce Amendment 1 agreement before step A.
   - R267:98,102–104 requires actual selection candidate/query/threshold traces, full-grid objective/profile, per-view residual/focal/support information, retained-depth and effective-focal provenance, and separate policy/strict-geometry statuses. The observer discards the full curve (S/kps_orig_obs.py:100), samples `SIGMA_GRID[::8]` for `grid_valid_any` (:101), and logs only the limited fields at :124–125. Selection receipts lack the actual candidate/NMS trace (S/run_retrieval_s146op.py:128). These requirements need implementation; no rushed instrumentation rewrite is represented here as verified.
   - New receipts still emit raw `Infinity/NaN` through default JSON serialization (S/kps_orig_obs.py:124–125; S/run_retrieval_s146op.py:128,146,153), contrary to R267:102's typed-null/status rule. CPU bad-depth evidence in Appendix C confirms this. Preserve the historical objective; change serialization and add status/reason fields rather than changing policy mathematics. Do not treat non-finite objective as operational unavailability.
   - P7 closes the omission of available files at seal time. A seal-time copy does not retroactively prove pre-execution identity. Snapshot/bind original manifests and execution provenance before any fresh policy call, and verify that binding again before scoring.

3. **Selector and observer:** local original `S/kps.py` has the required SHA (Appendix A); runner prepends its directory and imports `KPS_MODULE` at S/run_retrieval_s146op.py:53,97. The relevant multi-frame selector returns a Torch tensor (P:752–764); its single-frame list branch (P:631–632) is not used at the final bank. The validator at S/run_retrieval_s146op.py:121–126 rejects fractional, duplicate, short, negative, out-of-range and target-colliding outputs before indexing. Integral float tensors pass the adopted “integer-valued” wording; the pinned API actually constructs integer tensors. List/NumPy returns become recorded exceptions, not silent coerced selections. `SELECTION_RECEIPT` is before the optional render, subject to F7.

4. **KPS counts and observer noninterference:** `initialize()` only resets/encodes/stores the initial frame (P:149–189). Constructions are accumulated banks of 5, 20 and 32 frames (S/run_retrieval_s146op.py:103–117). Each calls reconstruction once (P:980–989); the observer iterates non-root views at S/kps_orig_obs.py:86–99. Thus `finite_at_best` lengths **[4,19,31] are correct**; `positive_depth_frac` includes the root and has [5,20,32] (:114–117). Original estimator/residual/grid functions are AST-identical; CPU mocked setters and Python/NumPy/Torch RNG are unchanged (Appendix C). This is mock evidence, not actual CUDA/CUT3R parity. Full state parity must still pass on the deployed environment.

5. **Pools/plans/analysis:** rule 4 retains float64 distance, the mean over all targets, stable tie selection and bank order (S/pool_op_s146.py:13–14,44–46). Native order merges only an identical ordered tuple (:47–53). Plans preserve every package's order (S/build_plans_s146.py:10–17). `table()` expects every set including `nat3`, rejects missing/duplicate/unexpected evaluation cells, and checks finite metrics (S/analyze_s146.py:17–26). `pkg(native=True)` handles explicit and merged native packages (:30–35). Matrix means give equal room/seed weight (:38–48), with eight windows per room checked in operational mode (:111). The PSNR gate and separate per-ordering SSIM blocks are correct (:127–133). The optional summaries also omit explicit room ranges, package-overlap summaries and per-rule history fractions from R267:112; those can be derived from the sealed pool/matrices without changing the primary. Non-evaluation score rows are ignored (:21); exact operational-only provenance should reject them before this generic analysis helper.

6. **Scorer/generator/replay:** S/score_gen_s146.py:10–24 duplicates the S140 reference/prediction/SSIM functions exactly; :29–31 matches S140's pooled whole-image SSE PSNR and target-mean SSIM (`work/S140_warp_guided/score_s140.py:32–45`). Synthetic CPU checks in Appendix F match. No warp is read by the operational scorer. S/gen_s141.py is byte-identical to the S141 copy, resets all four RNG families at :134–135, uses context RGB at :173–176 and target poses at :186–190; warp reads are B-only (:177–182). The replay hash in S/s146op_chain.sh:33 agrees with `work/S143_context_ranking/results/tacc/REPLAY_SHA256.txt:1–2`; this verifies archived receipt consistency, not a new GPU replay. Fresh generation uses only the declared evaluation seeds (:36); replay's exposed seed 3 is separate (:30). The unused warp path on the A branch is harmless.

7. **Shell details:** `set -euo pipefail` does catch worker errors through the current pipelines, and both `wait` statuses are explicitly tested; the problem is immediate exit without peer cleanup, not ignored exit status. The initial `[ -d ] && ...` list does not itself exit under `set -e` when the namespace is missing. The unquoted heredocs intentionally expand the fixed TACC paths and backslash-newline continuation; their current text parses correctly. Fixed paths contain no shell-special whitespace; no demonstrated current path-quoting corruption was found. Patches quote added paths. `bash -n` passes the current chain (Appendix A). GNU `timeout`, `sha256sum`, and `grep --line-buffered` belong to the Linux/TACC script; the review did not attempt to execute the chain on macOS.

## Exact proposed patches

These are focused corrections, not a claim that the revised full GPU workflow has been tested. The budget supervisor needs **actual remaining S146 GPU-seconds** from existing accounting; its input is not an additional human-authorization gate. It conservatively charges both reserved GPUs for all wall time, including CPU/idle phases.

### P1. Atomic namespace

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P2. Preserve logs without grep-status coupling

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P3. Bounded chain and process-group cleanup

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P4. Check deployed dependencies before model startup

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

P4 deliberately fails before loading models if the deployed helper is missing or different. It does not copy a helper, assume a remote package layout, or validate all weights/configuration. Stage the verified intended helper through the existing deployment process.

### P5. Pool identity and rule 2 precision

This checks receipts against the supplied manifests, not against an independently frozen manifest hash. Record the rule-2 change as an implementation correction before generation; the nearest-4 calculation remains float64.

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P6. Parity state and exact scales

The digest captures ordered surfel attributes, cached depths/focals/cameras and frame mapping, without changing policy arrays. It is enabled only for the exposed parity calls. Surfels have the four hashed attributes in `data/S134_tacc/vmem_src/utils/util.py:1277–1288`; construction stores arrays at P:899–904. This proposed stronger gate needs the actual exposed parity run; a CPU hash fixture cannot prove GPU determinism.

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P7. Complete-cell check and seal

This validates exact prediction names, shapes and finite contents before sealing every available namespace file. It preserves the source-at-start hash check. Copies taken here are explicitly **seal-time snapshots**; the pre-execution binding gap described above still requires work.

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P8. Retrieval exception boundary and status

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P9. Native descriptive mean

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P10. Explicit split labels

Correct the parser for future staging; validate already staged manifests against labeled metadata before deciding whether any restaging is necessary.

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

### P11. Do not label a PSNR threshold as an SSIM gate

See the corresponding file/hunk in the [consolidated unified diff](#consolidated-unified-diff).

## Consolidated unified diff

Apply this single combined patch to the source snapshot in Appendix A. Its hunks incorporate P1–P11 without conflicting context from independent patches. CPU fixtures verify existing defects; the combined candidate was checked in memory for exact original contexts, Python syntax, Bash syntax and quoted Python heredoc syntax. These syntax checks do not certify the proposed supervisor or GPU workflow at runtime.

```diff
--- a/work/S146_fresh12/s146op_chain.sh
+++ b/work/S146_fresh12/s146op_chain.sh
@@ -3,43 +3,124 @@
 set -euo pipefail
 R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s146; OP=$G/operational_v1; S=$R/src/s146; PY=$R/env/bin/python
 while tmux has-session -t s145chain 2>/dev/null || tmux has-session -t s144chain 2>/dev/null; do sleep 60; done
-[ -d $OP ] && ls $OP/*.json >/dev/null 2>&1 && { echo "[s146op] namespace not fresh"; exit 4; }
-mkdir -p $OP/logs; sha256sum $S/*.py $S/*.sh $S/PROTOCOL.md > $OP/CODE_SHA256.txt
+# Supply remaining GPU-seconds from the existing S146 accounting; no fresh 24 h reset.
+if [ "${S146_BUDGET_CHILD:-0}" != 1 ]; then
+  exec "$PY" - "$0" "${S146_REMAINING_GPU_SECONDS:?remaining S146 GPU-seconds required}" <<'BUDGET_PY'
+import math, os, signal, subprocess, sys
+remaining = float(sys.argv[2])
+if not math.isfinite(remaining) or not 0 < remaining <= 24 * 3600:
+    raise SystemExit("invalid remaining GPU budget")
+# Charge both reserved GPUs for the whole chain, including CPU/idle time.
+child_env = dict(os.environ, S146_BUDGET_CHILD="1")
+p = subprocess.Popen(["bash", sys.argv[1]], env=child_env, start_new_session=True)
+try:
+    try:
+        code = p.wait(timeout=remaining / 2.0)
+    except subprocess.TimeoutExpired:
+        print("[s146op] INCOMPLETE: remaining GPU budget exhausted", flush=True)
+        code = 124
+finally:
+    try:
+        os.killpg(p.pid, signal.SIGTERM)
+    except ProcessLookupError:
+        pass
+    try:
+        p.wait(timeout=5)
+    except subprocess.TimeoutExpired:
+        pass
+    try:
+        os.killpg(p.pid, signal.SIGKILL)
+    except ProcessLookupError:
+        pass
+    p.wait()
+raise SystemExit(code)
+BUDGET_PY
+fi
+mkdir "$OP" || { echo "[s146op] namespace exists or cannot be created"; exit 4; }
+mkdir "$OP/logs"; sha256sum $S/*.py $S/*.sh $S/PROTOCOL.md > $OP/CODE_SHA256.txt
 export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
 echo "[s146op] start $(date -u +%FT%TZ)"; T0=$(date +%s)
+# These must be the deployed files, not merely local mirror receipts.
+"$PY" - "$S" "$R/src/vmem" <<'SOURCE_PY'
+import hashlib, sys
+from pathlib import Path
+s, v = map(Path, sys.argv[1:])
+expected = {
+    s / "kps.py": "71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f",
+    s / "s141_common.py": "459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc",
+    v / "modeling/pipeline.py": "680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255",
+}
+for path, want in expected.items():
+    got = hashlib.sha256(path.read_bytes()).hexdigest()
+    if got != want:
+        raise SystemExit(f"execution source mismatch: {path}: {got}")
+SOURCE_PY
 # 1. observer parity on an exposed chess window (same GPU): plain original KPS vs observer module
 for m in kps kps_orig_obs; do mkdir -p $OP/parity_$m
-  CUDA_VISIBLE_DEVICES=3 KPS_MODULE=$m DATA_ROOT=$R/data/s139_stage ARM_OUT=$OP/parity_$m WINDOW_MANIFEST=$S/PARITY_MANIFEST_chess_w0.json INIT=kps POSE_CONVENTION=gl \
-    $PY $S/run_retrieval_s146op.py 2>&1 | grep --line-buffered -E 's146op|records|Traceback|Error'; done
+  CUDA_VISIBLE_DEVICES=3 CAPTURE_POLICY_STATE=1 KPS_MODULE=$m DATA_ROOT=$R/data/s139_stage ARM_OUT=$OP/parity_$m WINDOW_MANIFEST=$S/PARITY_MANIFEST_chess_w0.json INIT=kps POSE_CONVENTION=gl \
+    $PY $S/run_retrieval_s146op.py 2>&1 | tee "$OP/logs/parity_$m.log" | awk '/s146op|records|Traceback|Error/ {print; fflush()}'; done
 python3 - <<PY | tee $OP/PARITY.json
-import json, sys
+import json, math, sys
 a = json.load(open('$OP/parity_kps/RETRIEVAL_RECEIPT.json'))['records'][0]; b = json.load(open('$OP/parity_kps_orig_obs/RETRIEVAL_RECEIPT.json'))['records'][0]
 same = a['status'] == b['status'] == 'OK' and a['raw_contexts'] == b['raw_contexts'] and a['n_surfels'] == b['n_surfels'] and \
-       [round(l['sigma'], 12) for l in a['kps_log']] == [round(l['sigma'], 12) for l in b['kps_log']]
+       len(a['kps_log']) == len(b['kps_log']) == 3 and all(l.get('kps') == 'OK' and math.isfinite(l['sigma']) and l['sigma'] > 0 for r in (a,b) for l in r['kps_log']) and \
+       [l['sigma'] for l in a['kps_log']] == [l['sigma'] for l in b['kps_log']] and \
+       bool(a.get('parity_state_sha256')) and a['parity_state_sha256'] == b.get('parity_state_sha256')
 print(json.dumps({'parity': same, 'raw_plain': a['raw_contexts'], 'raw_observer': b['raw_contexts'], 'n_surfels': [a['n_surfels'], b['n_surfels']]}))
 sys.exit(0 if same else 3)
 PY
 # 2. step A per room with the pinned policy
 stepA() { mkdir -p $OP/stepA/$2; CUDA_VISIBLE_DEVICES=$1 KPS_MODULE=kps_orig_obs DATA_ROOT=$G/stage12 ARM_OUT=$OP/stepA/$2 WINDOW_MANIFEST=$G/manifests/WINDOW_MANIFEST_$2.json \
-  INIT=kps POSE_CONVENTION=gl $PY $S/run_retrieval_s146op.py 2>&1 | grep --line-buffered -E 's146op|records|Traceback|Error'; }
+  INIT=kps POSE_CONVENTION=gl $PY $S/run_retrieval_s146op.py 2>&1 | tee "$OP/logs/stepA_$2.log" | awk '/s146op|records|Traceback|Error/ {print; fflush()}'; }
 ( stepA 3 apt1_kitchen; stepA 3 office2_5a ) & P1=$!; stepA 4 apt2_luke & P2=$!; wait $P1 || exit 7; wait $P2 || exit 7
 # 3. global availability gate + pool
 $PY $S/pool_op_s146.py $G/stage12 $G/manifests $OP/stepA $OP/POOL_OP.json || { echo "[s146op] OPERATIONAL_PANEL_UNAVAILABLE"; exit 5; }
 $PY $S/build_plans_s146.py $OP/POOL_OP.json $OP
 # 4. exposed generator replay
 mkdir -p $OP/replay; CUDA_VISIBLE_DEVICES=3 VARIANT=A ADAPTER=NONE PLAN=$S/plan_s143_replay.json ARM_OUT=$OP/replay SEEDS=3 SHARD=0/1 \
-  DATA_ROOT=$R/data/s139_stage WARP_DIR=/mnt/gluster_dcpu/yiyangliu/gwm_s143/warps $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
+  DATA_ROOT=$R/data/s139_stage WARP_DIR=/mnt/gluster_dcpu/yiyangliu/gwm_s143/warps $PY $S/gen_s141.py 2>&1 | tee "$OP/logs/replay.log" | awk '/^\[|Traceback|Error/ {print; fflush()}' 
 K=$(python3 -c "import json; print(json.load(open('$S/plan_s143_replay.json'))['contexts'][0]['ctx_key'])")
 [ "$(sha256sum $OP/replay/${K}__s3.npy | cut -d' ' -f1)" = "913394e0f8d25b5f179aaffbdd6ba3d9ac7ed21d8f86dd393bf9235ccaf111bb" ] || { echo "[s146op] REPLAY FAILED"; exit 3; }
 # 5. evaluation-seed generation
 gen() { local out=$OP/gen_part$2; mkdir -p $out; sha256sum $S/gen_s141.py $S/s141_common.py $OP/plan_s146_part$2.json > $out/CODE_SHA256.txt
   CUDA_VISIBLE_DEVICES=$1 VARIANT=A ADAPTER=NONE PLAN=$OP/plan_s146_part$2.json ARM_OUT=$out SEEDS=42,7,1,2 SHARD=0/1 DATA_ROOT=$G/stage12 WARP_DIR=$G/warps \
-    timeout 10h $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[done\]|Traceback|Error|bad output'; }
+    timeout 10h $PY $S/gen_s141.py 2>&1 | tee "$OP/logs/gen_part$2.log" | awk '/^\[done\]|Traceback|Error|bad output/ {print; fflush()}'; }
 gen 3 0 & P1=$!; gen 4 1 & P2=$!; wait $P1 || exit 6; wait $P2 || exit 6
 for p in 0 1; do n=$(python3 -c "import json; print(4 * len(json.load(open('$OP/plan_s146_part$p.json'))['contexts']))")
   [ "$(ls $OP/gen_part$p | grep -cE '__s(42|7|1|2)\.npy$')" -eq "$n" ] || { echo "[s146op] part $p incomplete"; exit 6; }; done
 # 6. seal before any target scoring
-( cd $OP && sha256sum gen_part0/*.npy gen_part1/*.npy POOL_OP.json stepA/*/RETRIEVAL_RECEIPT.json plan_s146_part*.json > SEAL_SHA256.txt ); echo "[s146op] sealed $(wc -l < $OP/SEAL_SHA256.txt) $(date -u +%FT%TZ)"
+sha256sum -c "$OP/CODE_SHA256.txt"
+"$PY" - "$OP" "$S" "$G" <<'SEAL_PY'
+import hashlib, json, shutil, sys
+from pathlib import Path
+import numpy as np
+op, source, data = map(Path, sys.argv[1:])
+for part in (0, 1):
+    plan = json.loads((op / f"plan_s146_part{part}.json").read_text())["contexts"]
+    names = [f"{c['ctx_key']}__s{s}.npy" for c in plan for s in (42,7,1,2)]
+    assert len(names) == len(set(names)), "duplicate planned output"
+    assert all(len(c["ctx_refs"]) == len(c["target_refs"]) == 4 for c in plan)
+    actual = {p.name for p in (op / f"gen_part{part}").glob("*.npy")}
+    assert actual == set(names), ("output identity mismatch", part)
+    for name in names:
+        a = np.load(op / f"gen_part{part}" / name, mmap_mode="r", allow_pickle=False)
+        assert a.shape == (4,3,576,576) and np.isfinite(a).all(), name
+inputs = op / "sealed_input_receipts"
+inputs.mkdir()
+for path in [source / "PROTOCOL.md", source / "PARITY_MANIFEST_chess_w0.json",
+             source / "plan_s143_replay.json", data / "METADATA_RECEIPT.json",
+             data / "CONVENTION.json", data / "CONVENTION2.json",
+             *sorted((data / "manifests").glob("WINDOW_MANIFEST_*.json"))]:
+    shutil.copyfile(path, inputs / path.name)
+def digest(path):
+    h = hashlib.sha256()
+    with path.open("rb") as f:
+        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
+    return h.hexdigest()
+paths = sorted(p for p in op.rglob("*") if p.is_file() and p.name != "SEAL_SHA256.txt")
+(op / "SEAL_SHA256.txt").write_text("".join(f"{digest(p)}  {p.relative_to(op)}\n" for p in paths))
+print("[s146op] complete prediction identities and all available namespace receipts sealed")
+SEAL_PY
 # 7. score + analysis
 export OMP_NUM_THREADS=8
 for p in 0 1; do $PY $S/score_gen_s146.py $OP/gen_part$p $G/stage12 $OP/plan_s146_part$p.json 42,7,1,2 $OP/SCORES_part$p.json; done
--- a/work/S146_fresh12/pool_op_s146.py
+++ b/work/S146_fresh12/pool_op_s146.py
@@ -29,18 +29,27 @@
 rows, unavailable = [], []
 for room in ROOMS:
     M = json.loads((MD / f'WINDOW_MANIFEST_{room}.json').read_text()); root = STAGE / room
-    R = {r['window_id']: r for r in json.loads((SA / room / 'RETRIEVAL_RECEIPT.json').read_text())['records']}
+    recs = json.loads((SA / room / 'RETRIEVAL_RECEIPT.json').read_text())['records']
+    expected_ids = [w['window_id'] for w in M['windows']]
+    assert M['scene_dir'] == room and len(expected_ids) == len(set(expected_ids)) == 8, ('manifest identity', room)
+    assert [r['window_id'] for r in recs] == expected_ids, ('receipt panel/order mismatch', room)
+    R = {r['window_id']: r for r in recs}
     pose = lambda ref: np.loadtxt(root / ref.split('/')[0] / f"frame-{ref.split('/')[1]}.pose.txt").reshape(4, 4)
     for w in M['windows']:
         bank, tg = w['bank'], w['targets']; r = R.get(w['window_id'], {}); order = {x: i for i, x in enumerate(bank)}
         raw = (r.get('raw_contexts') or {}).get('memory_nms_on_clean', [])
         kl = r.get('kps_log', []); counts = [len(l.get('finite_at_best', [])) for l in kl]
-        ok = (r.get('status') == 'OK' and len(raw) == 4 and len(set(raw)) == 4 and all(x in order for x in raw) and not set(raw) & set(tg)
-              and r.get('bank') == bank and counts == [4, 19, 31])
+        ok = (r.get('status') == 'OK' and len(raw) == 4 and len(set(raw)) == 4 and all(x in order for x in raw)
+              and len(bank) == len(set(bank)) == 32 and len(tg) == len(set(tg)) == 4 and not set(bank) & set(tg)
+              and w.get('priming_chunks') == [15, 12] and r.get('bank') == bank and r.get('targets') == tg
+              and r.get('init') == 'kps' and r.get('convention') == 'gl'
+              and (r.get('consumer_contexts') or {}).get('memory_nms_on_clean') == raw
+              and counts == [4, 19, 31] and all(l.get('kps') == 'OK' and l.get('known_K') is False for l in kl)
+              and [len(p.get('conf_median', [])) for p in r.get('construct_probes', [])] == [5, 20, 32])
         if not ok: unavailable.append({'window_id': w['window_id'], 'status': r.get('status'), 'raw': raw, 'kps_counts': counts, 'error': r.get('error')}); continue
         bp = [pose(x) for x in bank]; tp = [pose(x) for x in tg]
         pw = sorted(geo32(bp[i], bp[j]) for i in range(5) for j in range(i + 1, 5)); thr = pw[int(len(pw) * 0.5)]
-        tq = tp[-1].copy(); tq[:3, :3] = Rot.from_quat(Rot.from_matrix(tq[:3, :3]).as_quat()).as_matrix()
+        tq = np.asarray(tp[-1], dtype=np.float32).copy(); tq[:3, :3] = Rot.from_quat(Rot.from_matrix(tq[:3, :3]).as_quat()).as_matrix()
         dist = [np.mean([geo64(b, t) for t in tp]) for b in bp]
         sets = {1: list(w['static_recent']), 2: [bank[i] for i in select(list(range(32)), bp, tq, thr)],
                 3: sorted(raw, key=lambda x: order[x]), 4: [bank[i] for i in sorted(np.argsort(np.array(dist), kind='stable')[:4])]}
--- a/work/S146_fresh12/run_retrieval_s146op.py
+++ b/work/S146_fresh12/run_retrieval_s146op.py
@@ -95,6 +95,23 @@
  f=root/'retrieval_maps.npz'; np.savez_compressed(f,**arrays); rec['retrieval_maps']=str(f)
 if INIT in ('kps','kpsK'):
  import importlib; kps=importlib.import_module(os.environ.get('KPS_MODULE','kps_orig_obs')); IIP.init_minimum_spanning_tree=_ORIG_INIT; kps.install(IIP,log=KPS_LOG,known_K=cut3r_K(K0.astype(np.float64)) if INIT=='kpsK' else None)
+def policy_state_sha256():
+ import hashlib
+ h=hashlib.sha256()
+ def add(v):
+  if isinstance(v,torch.Tensor): v=v.detach().cpu().numpy()
+  a=np.ascontiguousarray(v)
+  h.update(str((a.dtype.str,a.shape)).encode()); h.update(a.tobytes())
+ for surfel in pipe.surfels:
+  for name in ('position','normal','radius','color'):
+   value=getattr(surfel,name)
+   if value is None: h.update(b'None')
+   else: add(value)
+ for name in ('surfel_Ks','surfel_depths','c2ws','Ks'):
+  h.update(name.encode())
+  for value in getattr(pipe,name): add(value)
+ h.update(json.dumps({str(k):list(map(int,v)) for k,v in sorted(pipe.surfel_to_timestep.items())},sort_keys=True).encode())
+ return h.hexdigest()
 records=[]; T4=int(cfg.model.target_num_frames)
 for w in MANIFEST['windows']:
  reset(); PROBES.clear(); KPS_LOG.clear(); bank=w['bank']; targets=w['targets']; recbase={'window_id':w['window_id'],'pair':w['pair'],'start':w['start'],'bank':bank,'targets':targets}
@@ -124,22 +141,23 @@
   if not (okint and len(ids)==4 and len(set(ids))==4 and all(0<=i<len(bank) for i in ids) and not set(bank[i] for i in ids)&set(targets)):
    raise RuntimeError(f'POLICY_UNAVAILABLE: invalid selector output {rawt.tolist()}')
   raw=[bank[i] for i in ids]; consumer=list(raw)   # no repeat-fill (R267)
+  parity_sha=policy_state_sha256() if os.environ.get('CAPTURE_POLICY_STATE')=='1' else None
   wroot0=OUT/w['window_id']; wroot0.mkdir(parents=True,exist_ok=True)
   (wroot0/'SELECTION_RECEIPT.json').write_text(json.dumps({'window_id':w['window_id'],'raw_indices':ids,'raw_contexts':raw,'kps_log':list(KPS_LOG)},indent=1,default=str)+'\n')
   wroot=OUT/w['window_id']; wroot.mkdir(parents=True,exist_ok=True)
   s2t=pipe.surfel_to_timestep
-  s2t_keys=np.array(sorted(int(k) for k in s2t.keys()),dtype=np.int64)
-  s2t_vals=[list(s2t[k]) for k in s2t_keys.tolist()]
-  np.savez_compressed(wroot/'surfel_to_timestep.npz',keys=s2t_keys,lengths=np.array([len(v) for v in s2t_vals],dtype=np.int64),flat=np.array([int(x) for v in s2t_vals for x in v],dtype=np.int64))
-  target_K=float(np.mean(pipe.surfel_Ks)) if np.ndim(pipe.surfel_Ks[0])==0 else np.mean(pipe.surfel_Ks,axis=0)
-  tc=np.asarray(q[-1:].detach().cpu())[0]
   try:
+   s2t_keys=np.array(sorted(int(k) for k in s2t.keys()),dtype=np.int64)
+   s2t_vals=[list(s2t[k]) for k in s2t_keys.tolist()]
+   np.savez_compressed(wroot/'surfel_to_timestep.npz',keys=s2t_keys,lengths=np.array([len(v) for v in s2t_vals],dtype=np.int64),flat=np.array([int(x) for v in s2t_vals for x in v],dtype=np.int64))
+   target_K=float(np.mean(pipe.surfel_Ks)) if np.ndim(pipe.surfel_Ks[0])==0 else np.mean(pipe.surfel_Ks,axis=0)
+   tc=np.asarray(q[-1:].detach().cpu())[0]
    info=pipe.render_surfels_to_image(pipe.surfels,pipe.get_transformed_c2ws(tc),[target_K*0.65]*2,principal_points=(int(cfg.surfel.width/2),int(cfg.surfel.height/2)),image_width=int(cfg.surfel.width),image_height=int(cfg.surfel.height))
    rr={'target':targets[-1]}; save_map(rr,info,wroot); rr['frame_count']=pipe.process_retrieved_spatial_information(info)[1]
   except Exception as dexc:
    rr={'target':targets[-1],'diagnostic_render_failed':f'{type(dexc).__name__}: {dexc}'}
   wrec=dict(recbase,status='OK',raw_contexts={'memory_nms_on_clean':raw},consumer_contexts={'memory_nms_on_clean':consumer},
-            n_surfels=int(len(pipe.surfels)),memory_frames=sorted({bank[int(t)] for v in s2t.values() for t in v}),
+            n_surfels=int(len(pipe.surfels)),parity_state_sha256=parity_sha,memory_frames=sorted({bank[int(t)] for v in s2t.values() for t in v}),
             frac_history_in_context=sum(r.startswith(w['history_seq']) for r in consumer)/4.0,
             init=INIT,convention=CONVENTION,kps_log=list(KPS_LOG),construct_probes=list(PROBES),render_last_target=rr,
             seconds=round(time.time()-t0,1))
@@ -149,6 +167,6 @@
   import traceback
   records.append(dict(recbase,status=('POLICY_UNAVAILABLE' if 'POLICY_UNAVAILABLE' in str(exc) else 'BLOCKED'),error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc()[-2000:]))
   print(f"[s146op] {w['window_id']} BLOCKED {exc}",flush=True)
-blocked=sum(1 for r in records if r.get('status')=='BLOCKED')
+blocked=sum(1 for r in records if r.get('status')!='OK')
 (Path(OUT/'RETRIEVAL_RECEIPT.json')).write_text(json.dumps({'schema':'s139-retrieval-v1','convention':CONVENTION,'init':INIT,'status':'MAPS_COMPLETE_NO_DIFFUSION' if not blocked else 'PARTIAL','recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'records':records,'blocked_records':blocked,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2,default=str)+'\n')
 print(json.dumps({'records':len(records),'blocked':blocked}))
--- a/work/S146_fresh12/analyze_s146.py
+++ b/work/S146_fresh12/analyze_s146.py
@@ -118,10 +118,12 @@
                            ('nearest4 - mem_pose', lambda w: pkg(w, 4), lambda w: pkg(w, 2)),
                            ('mem_vmem native - sorted', lambda w: pkg(w, native=True), lambda w: pkg(w, 3))):
             blk[name] = matrix(P, t, a, b, EVAL)
+            if metric == 'ssim': blk[name].pop('gate')
         means = {}
         for w in P['windows']:
             for st in w['sets']:
-                for ru in (st['rules'] or ['nat3']): means.setdefault(str(ru), []).append(np.mean([t[(w['window_id'], st['set_id'], sd)] for sd in EVAL]))
+                for ru in st['rules']: means.setdefault(str(ru), []).append(np.mean([t[(w['window_id'], st['set_id'], sd)] for sd in EVAL]))
+            means.setdefault('nat3', []).append(np.mean([t[(w['window_id'], pkg(w, native=True), sd)] for sd in EVAL]))
         blk['per_rule_means'] = {k: float(np.mean(v)) for k, v in means.items()}
         res[metric] = blk
     ps, pn = res['psnr_db']['PRIMARY nearest4 - mem_vmem(sorted)'], res['psnr_db']['nearest4 - mem_vmem(native order)']
--- a/work/S146_fresh12/stage_12scenes_s146.py
+++ b/work/S146_fresh12/stage_12scenes_s146.py
@@ -29,8 +29,12 @@
     Kc = np.array([float(x) for x in inf['m_calibrationColorIntrinsic'].split()]).reshape(4, 4)[:3, :3]
     sx, sy = W / cw, H / ch
     K = np.array([[Kc[0, 0] * sx, 0, (Kc[0, 2] + 0.5) * sx - 0.5], [0, Kc[1, 1] * sy, (Kc[1, 2] + 0.5) * sy - 0.5], [0, 0, 1]])
-    seqs = [(int(a), int(b)) for a, b in re.findall(r'start=(\d+) ; end=(\d+)', (rdir / 'split.txt').read_text())]
-    (h0, h1), (c0, c1) = seqs[0], seqs[1]
+    rows = re.findall(r'(sequence[01])\s*\[frames=(\d+)\]\s*\[start=(\d+) ; end=(\d+)\]', (rdir / 'split.txt').read_text())
+    assert len(rows) == 2 and {x[0] for x in rows} == {'sequence0', 'sequence1'}, (key, 'split labels')
+    seqs = {name: (int(a), int(b), int(n)) for name, n, a, b in rows}
+    (h0, h1, nh), (c0, c1, nc) = seqs['sequence0'], seqs['sequence1']
+    assert h0 == 0 and h1 >= h0 and c1 >= c0 and c0 == h1 + 1, (key, 'split ranges')
+    assert nh == h1 - h0 + 1 and nc == c1 - c0 + 1, (key, 'split counts')
     out = STAGE / key; out.mkdir(parents=True, exist_ok=True)
     np.savetxt(out / 'camera-intrinsics.txt', K, fmt='%.6f')
     for sname, (a, b) in (('seq-00', (h0, h1)), ('seq-01', (c0, c1))):
```

## Evidence appendices

All commands below use the repository root as working directory. Numerical fixture outcomes are **MEASURED CPU/mock behavior**, recorded completely in this report; implications for code are **ANALYTICAL**. They are not fresh scene or GPU results. Read-only reviewers supplied the CPU fixtures; the parent checked source contracts and assembled the diffs. The current experiment artifacts and remote execution are **UNVERIFIED**. No repository-wide tests or linter were run: production source was unchanged and these targeted fixtures exercise the reviewed contracts. No S146-specific test suite or linter configuration was identified. The existing `.venv-cut3r` environment was reused; no packages were installed.

### Appendix A — Source snapshot and syntax

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
import hashlib, subprocess, json, sys, importlib.util
print('PYTHON',sys.version.split()[0])
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
paths=['PROTOCOL.md','s146op_chain.sh','run_retrieval_s146op.py','kps_orig_obs.py','kps.py','pool_op_s146.py','build_plans_s146.py','score_gen_s146.py','analyze_s146.py','gen_s141.py','s141_common.py','PARITY_MANIFEST_chess_w0.json','plan_s143_replay.json','stage_12scenes_s146.py']
for name in paths:
 p=Path('work/S146_fresh12')/name
 print('SHA256',str(p),hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'MISSING')
p=Path('work/S139_crossseq_revisit/kps.py'); print('SHA256',str(p),hashlib.sha256(p.read_bytes()).hexdigest())
for name in ('numpy','torch','PIL','skimage'): print('MODULE',name,bool(importlib.util.find_spec(name)))
p=subprocess.run(['bash','-n','work/S146_fresh12/s146op_chain.sh'],capture_output=True,text=True); print('BASH_SYNTAX',p.returncode,repr(p.stdout),repr(p.stderr))
for name in paths:
 if name.endswith('.py'):
  p=Path('work/S146_fresh12')/name
  if p.exists(): compile(p.read_text(),str(p),'exec')
print('PYTHON_SYNTAX PASS')
PY
```

Complete output (exit 0):

```text
PYTHON 3.14.7
HEAD 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c
SHA256 work/S146_fresh12/PROTOCOL.md d1840311b217a7db5423d5505a3e32f5ca3e4f052c959ed5cabde2be3ccfe0ca
SHA256 work/S146_fresh12/s146op_chain.sh d12e2629684293316963b5e04f41f9e04ba8b344f4fb6c3a8461c168a62b7248
SHA256 work/S146_fresh12/run_retrieval_s146op.py 573774e4c148819d33a6c4407d6da1080cc3be145455591d2896808ea5f487a1
SHA256 work/S146_fresh12/kps_orig_obs.py 82bd4d16a6cc20b80fae41e04f12969d721cffa52d60da7b2263e11e22a8b767
SHA256 work/S146_fresh12/kps.py 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f
SHA256 work/S146_fresh12/pool_op_s146.py 593f23a7f545953121f6ac61b0da399675a52276ea0bf5852ead544607796bce
SHA256 work/S146_fresh12/build_plans_s146.py 29ba2237a9328d9a36cf557683b668aba62a11f7af1ed2df4e9b87c16269b923
SHA256 work/S146_fresh12/score_gen_s146.py d8073d4856b2597b77cf44bcff902335ab4f260a7055f58a9cc085280a284057
SHA256 work/S146_fresh12/analyze_s146.py 2a1abba48b0c04cac272a348bcf8d4f65267253abc7b7287beb151512d4cfd0c
SHA256 work/S146_fresh12/gen_s141.py c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121
SHA256 work/S146_fresh12/s141_common.py MISSING
SHA256 work/S146_fresh12/PARITY_MANIFEST_chess_w0.json 750f8b4fd4066449497b8ef7d2b9ebd48f8d9edb1845c204c50cb944429f6e31
SHA256 work/S146_fresh12/plan_s143_replay.json 0553642aa1e9708091f8d4da6aee1d17ad0f5cd50f9e5f089205b6d6604ab468
SHA256 work/S146_fresh12/stage_12scenes_s146.py 2262a9b465abfe39aba80b13e415663cfac1da5ea4452be5b368fbd5dabc58f1
SHA256 work/S139_crossseq_revisit/kps.py 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f
MODULE numpy False
MODULE torch False
MODULE PIL False
MODULE skimage False
BASH_SYNTAX 0 '' ''
PYTHON_SYNTAX PASS
```

### Appendix B — Shell failure-path fixtures

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import subprocess
cases={
'namespace_missing': '''set -euo pipefail; OP=/dev/null/absent; [ -d $OP ] && ls $OP/*.json >/dev/null 2>&1 && { echo reject; exit 4; }; echo accepted''',
'namespace_existing_no_root_json': '''set -euo pipefail; OP=/dev; ls() { return 2; }; [ -d $OP ] && ls $OP/*.json >/dev/null 2>&1 && { echo reject; exit 4; }; echo accepted''',
'grep_hides_success': '''set -euo pipefail; printf '%s\\n' '{"jobs": 10}'; printf '%s\\n' '{"jobs": 10}' | grep -E '^\\[done\\]|Traceback|Error|bad output'; echo reached''',
'worker_failure_wait': '''set -euo pipefail; (false; echo unreachable) & P1=$!; wait $P1 || exit 7; echo reached''',
'failed_first_worker_leaves_peer': '''set -euo pipefail; (exit 1) & P1=$!; (sleep 0.2; echo peer_kept_running) & P2=$!; wait $P1 || exit 7; wait $P2 || exit 7''',
'quoted_heredoc_alternative': '''set -euo pipefail; OP=/example/path; cat <<PY2
p = '$OP/file'
same = True and \\
       False
PY2'''
}
for name, code in cases.items():
 r=subprocess.run(['bash','-c',code],text=True,capture_output=True)
 print(name, 'exit', r.returncode, 'stdout',repr(r.stdout),'stderr',repr(r.stderr))
PY
```

Complete output (exit 0):

```text
namespace_missing exit 0 stdout 'accepted\n' stderr ''
namespace_existing_no_root_json exit 0 stdout 'accepted\n' stderr ''
grep_hides_success exit 1 stdout '{"jobs": 10}\n' stderr ''
worker_failure_wait exit 7 stdout '' stderr ''
failed_first_worker_leaves_peer exit 7 stdout 'peer_kept_running\n' stderr ''
quoted_heredoc_alternative exit 0 stdout "p = '/example/path/file'\nsame = True and        False\n" stderr ''
```

### Appendix B2 — Existing parity expression

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
import ast, json
s=Path('work/S146_fresh12/s146op_chain.sh').read_text()
body=s.split('import json, sys\n',1)[1].split("print(json.dumps",1)[0]
expr=body[body.index('same ='):].replace('\\\n','')
a={'status':'OK','raw_contexts':{'memory_nms_on_clean':['a','b','c','d']},'n_surfels':9,'kps_log':[]}
b=json.loads(json.dumps(a)); ns={'a':a,'b':b}; exec(expr,ns)
print('PARITY_EMPTY_KPS_LOG_ACCEPTED',ns['same'])
a['kps_log']=[{'sigma':1.0}]*3; b['kps_log']=[{'sigma':1.0+1e-13}]*3; exec(expr,ns)
print('PARITY_DIFFERENT_SCALES_ACCEPTED',ns['same'])
print('PARITY_ONLY_SURFEL_FIELD', [n for n in ('n_surfels','surfel_sha256','surfel_state') if n in expr])
print('LOCAL_S141_COMMON_PRESENT',Path('work/S146_fresh12/s141_common.py').is_file())
PY
```

Complete output (exit 0):

```text
PARITY_EMPTY_KPS_LOG_ACCEPTED True
PARITY_DIFFERENT_SCALES_ACCEPTED True
PARITY_ONLY_SURFEL_FIELD ['n_surfels']
LOCAL_S141_COMMON_PRESENT False
```

### Appendix C — Observer and selector CPU mocks

Exact command (read-only reviewer; existing project Python):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
import ast, copy, hashlib, importlib.util, json, random
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
base=Path('work/S146_fresh12')
def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
orig=load('work/S139_crossseq_revisit/kps.py','review_orig')
obs=load(base/'kps_orig_obs.py','review_obs')
a=ast.parse(Path('work/S139_crossseq_revisit/kps.py').read_text()); b=ast.parse((base/'kps_orig_obs.py').read_text())
func=lambda tree: {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
print('FUNCTION_AST_EQUAL', {k:func(a)[k]==func(b)[k] for k in ['_proj_residual','estimate_sigma','pixel_grid']})
print('PLAIN_ORIGINAL_HASH_EQUAL',hashlib.sha256((base/'kps.py').read_bytes()).hexdigest()==hashlib.sha256(Path('work/S139_crossseq_revisit/kps.py').read_bytes()).hexdigest())
class State:
    def __init__(self,n,bad=False):
        self.n_imgs=n; self.device='cpu'; self.edges=[(0,j) for j in range(1,n)]; self.imshapes=[(8,8)]*n
        self.T=torch.eye(4,dtype=torch.float64).repeat(n,1,1); self.T[:,0,3]=torch.arange(n,dtype=torch.float64)*0.02
        pix=orig.pixel_grid(8,8); z=np.full((8,8),2.0); p=np.dstack([(pix[...,0]-4)/10*z,(pix[...,1]-4)/10*z,z])
        self.pts=[torch.tensor(p,dtype=torch.float32)+self.T[j,:3,3].float() for j in range(n)]
        if bad: self.pts[-1][...,2]=-2
        self.im_conf=[torch.full((8,8),4.0) for _ in range(n)]; self.pred_i={f'{i}_{j}':self.pts[i] for i,j in self.edges}; self.pred_j={f'{i}_{j}':self.pts[j] for i,j in self.edges}
        self.conf_i={f'{i}_{j}':self.im_conf[i] for i,j in self.edges}; self.conf_j={f'{i}_{j}':self.im_conf[j] for i,j in self.edges}
        self.min_conf_thr=3.; self.has_im_poses=True; self.verbose=False; self.pw_poses=None; self.saved={}
    def _set_pose(self,dst,e,R,t,scale): self.saved['pose'+str(e)]=(R.clone(),t.clone(),scale)
    def _set_depthmap(self,i,d): self.saved['depth'+str(i)]=d.clone()
    def _set_focal(self,i,f): self.saved['focal'+str(i)]=f

def run(mod,n,bad=False):
    st=State(n,bad); logs=[]
    IIP=SimpleNamespace(init_minimum_spanning_tree=lambda *a,**k:None,
        get_known_poses=lambda s:(s.n_imgs,None,s.T),
        minimum_spanning_tree=lambda *a,**k:(st.pts,None,[10.]*n,None),
        edge_str=lambda i,j:f'{i}_{j}',
        rigid_points_registration=lambda *a,**k:(1.,torch.eye(3),torch.zeros(3)),
        inv=torch.linalg.inv, geotrf=lambda T,p:p@T[:3,:3].T+T[:3,3])
    np.random.seed(19); torch.manual_seed(23); random.seed(29)
    before=(copy.deepcopy(np.random.get_state()),torch.random.get_rng_state().clone(),random.getstate())
    mod.install(IIP,log=logs,max_points=60)(st)
    after=(np.random.get_state(),torch.random.get_rng_state(),random.getstate())
    rng_equal=(all(np.array_equal(x,y) for x,y in zip(before[0],after[0])) and torch.equal(before[1],after[1]) and before[2]==after[2])
    return st.saved,logs,rng_equal

def same(a,b):
    if isinstance(a,dict): return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if isinstance(a,tuple): return all(same(x,y) for x,y in zip(a,b))
    if isinstance(a,torch.Tensor): return torch.equal(a,b)
    return a==b
for n,bad in [(5,False),(20,False),(32,False),(5,True)]:
    x,lx,rx=run(orig,n,bad); y,ly,ry=run(obs,n,bad)
    print('OBSERVER_CPU_MOCK',{'n_imgs':n,'bad_view':bad,'setters_identical':same(x,y),'original_rng_unchanged':rx,'observer_rng_unchanged':ry,'log_count':len(ly),'nonroot_count':len(ly[0]['finite_at_best']),'root_in_positive_depth_count':len(ly[0]['positive_depth_frac'])})
    if bad:
        text=json.dumps(ly)
        try: json.loads(text,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
        except ValueError as e: print('STRICT_JSON_REJECTED_OBSERVER_LOG',str(e))
source=(base/'run_retrieval_s146op.py').read_text().splitlines()
selector='\n'.join(line[2:] for line in source[120:126])
bank=[f'h/{i:06d}' for i in range(32)]; targets=['c/000060','c/000075','c/000090','c/000105']
for name,value in [('int_tensor',torch.tensor([0,2,5,31])),('integral_float_tensor',torch.tensor([0.,2.,5.,31.])),('fractional_tensor',torch.tensor([0.,2.,5.,30.5])),('duplicate_tensor',torch.tensor([0,2,5,5])),('short_tensor',torch.tensor([0,2,5])),('negative_tensor',torch.tensor([-1,2,5,31])),('out_of_range_tensor',torch.tensor([0,2,5,32])),('numpy_array',np.array([0,2,5,31])),('list',[0,2,5,31])]:
    env={'clean_ctx':{'context_time_indices':value},'bank':bank,'targets':targets,'np':np}
    try: exec(selector,env); result='OK'
    except Exception as e: result=('POLICY_UNAVAILABLE' if 'POLICY_UNAVAILABLE' in str(e) else 'BLOCKED')+':'+type(e).__name__
    print('SELECTOR_CASE',name,result)
env={'clean_ctx':{'context_time_indices':torch.tensor([0,2,5,31])},'bank':bank,'targets':[bank[2]],'np':np}
try: exec(selector,env)
except Exception as e: print('SELECTOR_TARGET_COLLISION',type(e).__name__,str(e))
records=[{'status':'POLICY_UNAVAILABLE'}]; blocked=sum(1 for r in records if r.get('status')=='BLOCKED')
print('ALL_UNAVAILABLE_TOP_LEVEL_STATUS','MAPS_COMPLETE_NO_DIFFUSION' if not blocked else 'PARTIAL','blocked_records',blocked)
PY
```

Complete output (exit 0):

```text
FUNCTION_AST_EQUAL {'_proj_residual': True, 'estimate_sigma': True, 'pixel_grid': True}
PLAIN_ORIGINAL_HASH_EQUAL True
OBSERVER_CPU_MOCK {'n_imgs': 5, 'bad_view': False, 'setters_identical': True, 'original_rng_unchanged': True, 'observer_rng_unchanged': True, 'log_count': 1, 'nonroot_count': 4, 'root_in_positive_depth_count': 5}
OBSERVER_CPU_MOCK {'n_imgs': 20, 'bad_view': False, 'setters_identical': True, 'original_rng_unchanged': True, 'observer_rng_unchanged': True, 'log_count': 1, 'nonroot_count': 19, 'root_in_positive_depth_count': 20}
OBSERVER_CPU_MOCK {'n_imgs': 32, 'bad_view': False, 'setters_identical': True, 'original_rng_unchanged': True, 'observer_rng_unchanged': True, 'log_count': 1, 'nonroot_count': 31, 'root_in_positive_depth_count': 32}
OBSERVER_CPU_MOCK {'n_imgs': 5, 'bad_view': True, 'setters_identical': True, 'original_rng_unchanged': True, 'observer_rng_unchanged': True, 'log_count': 1, 'nonroot_count': 4, 'root_in_positive_depth_count': 5}
STRICT_JSON_REJECTED_OBSERVER_LOG Infinity
SELECTOR_CASE int_tensor OK
SELECTOR_CASE integral_float_tensor OK
SELECTOR_CASE fractional_tensor POLICY_UNAVAILABLE:RuntimeError
SELECTOR_CASE duplicate_tensor POLICY_UNAVAILABLE:RuntimeError
SELECTOR_CASE short_tensor POLICY_UNAVAILABLE:RuntimeError
SELECTOR_CASE negative_tensor POLICY_UNAVAILABLE:RuntimeError
SELECTOR_CASE out_of_range_tensor POLICY_UNAVAILABLE:RuntimeError
SELECTOR_CASE numpy_array BLOCKED:AttributeError
SELECTOR_CASE list BLOCKED:AttributeError
SELECTOR_TARGET_COLLISION RuntimeError POLICY_UNAVAILABLE: invalid selector output [0, 2, 5, 31]
ALL_UNAVAILABLE_TOP_LEVEL_STATUS MAPS_COMPLETE_NO_DIFFUSION blocked_records 0
```

### Appendix D — Pool and analysis CPU fixtures

Exact command (read-only reviewer):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import ast, contextlib, io, json, math, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from scipy.spatial.transform import Rotation as Rot
BASE=Path('work/S146_fresh12')
def funcs(path, names):
 tree=ast.parse(Path(path).read_text())
 ns={'np':np,'torch':torch,'Rot':Rot,'math':math,'ROOMS':['apt1_kitchen','apt2_luke','office2_5a']}
 nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),ns)
 return ns
p=funcs(BASE/'pool_op_s146.py',{'geo32','geo64','select'})
q=funcs(BASE/'build_pool_s146.py',{'geo32','geo64','select'})
rng=np.random.default_rng(268)
for case in range(40):
 poses=[]
 for j in range(36):
  a=np.eye(4); a[:3,:3]=Rot.from_rotvec(rng.normal(size=3)).as_matrix(); a[:3,3]=rng.normal(size=3); poses.append(a)
 bp,tp=poses[:32],poses[32:]
 thr=sorted(p['geo32'](bp[i],bp[j]) for i in range(5) for j in range(i+1,5))[5]
 assert p['select'](list(range(32)),bp,tp[-1],thr)==q['select'](list(range(32)),bp,tp[-1],thr)
 assert [np.mean([p['geo64'](b,t) for t in tp]) for b in bp]==[np.mean([q['geo64'](b,t) for t in tp]) for b in bp]
print('PASS 40 CPU pose fixtures: rules 2 and 4 exactly match frozen S146 build_pool implementations')
tree=ast.parse((BASE/'pool_op_s146.py').read_text())
gate=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ok' for t in n.targets))
base={'status':'OK','bank':[f'b{i}' for i in range(32)],'targets':['WRONG'],'init':'mst','convention':'native'}
ns={'r':base,'bank':base['bank'],'tg':['t0','t1','t2','t3'],'raw':['b0','b1','b2','b3'],'order':{b:i for i,b in enumerate(base['bank'])},'counts':[4,19,31]}
exec(compile(ast.fix_missing_locations(ast.Module(body=[gate],type_ignores=[])),str(BASE/'pool_op_s146.py'),'exec'),ns)
print('WITNESSED pool accepts mismatched targets/init/convention:',ns['ok'])
ns['bank']=ns['r']['bank']=ns['bank']+['b32']; ns['order']={b:i for i,b in enumerate(ns['bank'])}
exec(compile(ast.fix_missing_locations(ast.Module(body=[gate],type_ignores=[])),str(BASE/'pool_op_s146.py'),'exec'),ns)
print('WITNESSED pool accepts 33-frame offered bank:',ns['ok'])
a=funcs(BASE/'analyze_s146.py',{'table','pkg','matrix'})
P={'n_windows':24,'unavailable':[],'windows':[]}; G={'runs':{}}
for ri,room in enumerate(a['ROOMS']):
 for i in range(8):
  wid=f'{room}_w{i}'
  sets=[{'set_id':f's{j}','rules':[j]} for j in (1,2,3,4)]
  if i%2: sets.append({'set_id':'nat3','rules':[],'native_order_of_rule':3})
  else: sets[2]['also_native_order']=True
  w={'window_id':wid,'room':room,'sets':sets,'stepA':{'frac_history':0.5}}; P['windows'].append(w)
  for s in sets:
   for seed in (42,7,1,2):
    key=f"{wid}__{s['set_id']}__s{seed}"
    G['runs'][key]={'ctx_key':f"{wid}__{s['set_id']}",'seed':seed,'psnr_db':{'s1':8.0,'s2':8.5,'s3':9.0,'s4':10.0,'nat3':7.0}[s['set_id']],'ssim':0.8}
t=a['table'](G,(42,7,1,2),P)
assert len(t)==432
assert all(a['pkg'](w,native=True)==('nat3' if int(w['window_id'][-1])%2 else 's3') for w in P['windows'])
print('PASS table includes all 432 cells, explicit nat3 and merged native packages; pkg resolves all 24 windows')
for label, mutate in [('missing',lambda g:g['runs'].pop(next(iter(g['runs'])))),('duplicate',lambda g:g['runs'].update({'dup':next(iter(g['runs'].values()))})),('extra',lambda g:g['runs'].update({'extra':{'ctx_key':'bad__s1','seed':42,'psnr_db':1}}))]:
 gg=json.loads(json.dumps(G)); mutate(gg)
 try: a['table'](gg,(42,7,1,2),P)
 except AssertionError: print('PASS table rejects',label)
 else: raise AssertionError(label)
m=a['matrix'](P,t,lambda w:a['pkg'](w,4),lambda w:a['pkg'](w,3),(42,7,1,2))
assert m['D']==1.0 and all(v==1.0 for v in m['D_room'].values()) and all(v==1.0 for v in m['D_seed'].values()) and m['gate']
print('PASS equal room/seed matrix and practical gate: D=1.0, all room/seed means=1.0')
an=ast.parse((BASE/'analyze_s146.py').read_text())
branch=next(n for n in ast.walk(an) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='mode' and any(isinstance(x,ast.Constant) and x.value=='op-primary' for x in n.test.comparators))
class Sink:
 def write_text(self,s): self.text=s
sink=Sink(); a.update({'J':lambda path:{'pool':P,'scores':G}[path],'Path':lambda path:sink,'sys':SimpleNamespace(argv=['analysis','op-primary','pool','scores','out']),'EVAL':(42,7,1,2),'json':json})
with contextlib.redirect_stdout(io.StringIO()): exec(compile(ast.fix_missing_locations(ast.Module(body=branch.body,type_ignores=[])),str(BASE/'analyze_s146.py'),'exec'),a)
res=json.loads(sink.text)
true_native=np.mean([t[(w['window_id'],a['pkg'](w,native=True),seed)] for w in P['windows'] for seed in (42,7,1,2)])
print('WITNESSED per_rule_means[nat3]=',res['psnr_db']['per_rule_means']['nat3'],'but all-window native mean=',true_native)
print('No files written; numerical fixtures ran on CPU only.')
PY
```

Complete output (exit 0):

```text
PASS 40 CPU pose fixtures: rules 2 and 4 exactly match frozen S146 build_pool implementations
WITNESSED pool accepts mismatched targets/init/convention: True
WITNESSED pool accepts 33-frame offered bank: True
PASS table includes all 432 cells, explicit nat3 and merged native packages; pkg resolves all 24 windows
PASS table rejects missing
PASS table rejects duplicate
PASS table rejects extra
PASS equal room/seed matrix and practical gate: D=1.0, all room/seed means=1.0
WITNESSED per_rule_means[nat3]= 7.0 but all-window native mean= 8.0
No files written; numerical fixtures ran on CPU only.
```

### Appendix E — S139 precision counterexample

Exact command (read-only reviewer):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import ast
from pathlib import Path
import numpy as np, torch
from scipy.spatial.transform import Rotation as Rot
p=Path('work/S146_fresh12/pool_op_s146.py'); tr=ast.parse(p.read_text()); ns={'np':np,'torch':torch}
exec(compile(ast.Module(body=[n for n in tr.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(p),'exec'),ns)
rng=np.random.default_rng(268)
for case in range(100):
 target=np.eye(4); target[:3,:3]=Rot.from_rotvec(rng.normal(size=3)).as_matrix()
 bank=[]
 for i in range(32):
  b=target.copy(); b[:3,:3]=target[:3,:3]@Rot.from_rotvec(rng.normal(size=3)*0.0005).as_matrix(); bank.append(b)
 q64=target.copy(); q64[:3,:3]=Rot.from_quat(Rot.from_matrix(q64[:3,:3]).as_quat()).as_matrix()
 q32=target.astype(np.float32); q32[:3,:3]=Rot.from_quat(Rot.from_matrix(q32[:3,:3]).as_quat()).as_matrix()
 thr=sorted(ns['geo32'](bank[i],bank[j]) for i in range(5) for j in range(i+1,5))[5]
 s64=ns['select'](list(range(32)),bank,q64,thr); s32=ns['select'](list(range(32)),bank,q32,thr)
 if s64!=s32:
  print('WITNESSED valid synthetic poses; RNG seed=268; case=',case)
  print('S146 rule2 original pool_op:',s64)
  print('S139 load-float32 target semantics:',s32)
  print('max target rotation absolute delta=',float(abs(q64.astype(np.float32)-q32).max()))
  print('threshold=',thr)
  break
else: raise AssertionError('no witness')
print('CPU-only synthetic counterexample; not a claim about actual S146 selections; no files written.')
PY
```

Complete output (exit 0):

```text
WITNESSED valid synthetic poses; RNG seed=268; case= 2
S146 rule2 original pool_op: [1, 22, 0, 6]
S139 load-float32 target semantics: [15, 12, 16, 6]
max target rotation absolute delta= 5.960464477539063e-08
threshold= 0.0014648438664153218
CPU-only synthetic counterexample; not a claim about actual S146 selections; no files written.
```

### Appendix F — Scorer, generator and replay consistency

Exact command (read-only reviewer):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import ast, io, json, math
from pathlib import Path
import numpy as np
import torch
from PIL import Image
torch.set_num_threads(1)
paths = ['work/S140_warp_guided/score_s140.py', 'work/S146_fresh12/score_gen_s146.py']
spaces = []
for p in paths:
    tree = ast.parse(Path(p).read_text())
    chosen = [n for n in tree.body if isinstance(n, ast.FunctionDef) or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'_g', '_K'} for t in n.targets))]
    ns = {'io': io, 'np': np, 'torch': torch, 'Image': Image}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), p, 'exec'), ns)
    spaces.append((tree, ns))
for name in ['ref_grid', 'pred_u8', 'ssim']:
    nodes = [next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name) for t, _ in spaces]
    assert ast.dump(nodes[0]) == ast.dump(nodes[1])
print('PASS: ref_grid/pred_u8/ssim ASTs identical')
rng = np.random.default_rng(268)
raw = rng.integers(0, 256, (480, 640, 3), dtype=np.uint8)
b = io.BytesIO(); Image.fromarray(raw).save(b, format='PNG')
class MemoryPNG:
    def read_bytes(self): return b.getvalue()
refs = [ns['ref_grid'](MemoryPNG()) for _, ns in spaces]
assert np.array_equal(*refs) and refs[0].shape == (576, 576, 3)
print('PASS: in-memory 640x480 reference conversion byte-identical')
for lo, hi in [(0, 1), (-1, 1)]:
    frames = rng.uniform(lo, hi, (4, 3, 576, 576)).astype(np.float32)
    results = []
    for _, ns in spaces:
        preds = [ns['pred_u8'](f) for f in frames]
        sse = sum(float(((p.astype(np.int64) - refs[0].astype(np.int64)) ** 2).sum()) for p in preds)
        results.append((-10 * math.log10(sse / (4 * 576 * 576 * 3 * 255 * 255)), float(np.mean([ns['ssim'](p, refs[0]) for p in preds]))))
    assert results[0] == results[1]
    print('PASS: four-target PSNR/SSIM exact equality for range', (lo, hi))
g = Path('work/S146_fresh12/gen_s141.py').read_bytes()
assert g == Path('work/S141_finetune/gen_s141.py').read_bytes()
print('PASS: S146 generator byte-identical to S141 generator')
r = json.loads(Path('work/S146_fresh12/plan_s143_replay.json').read_text())['contexts'][0]
old = json.loads(Path('work/S139_crossseq_revisit/plan.json').read_text())['contexts']
matched = [c for c in old if c['ctx_key'] == r['ctx_key']]
assert len(matched) == 1
for field in ['ctx_key', 'window_id', 'convention', 'ctx_refs', 'target_refs', 'arms']:
    assert r[field] == matched[0][field]
p = json.loads(Path('work/S146_fresh12/PARITY_MANIFEST_chess_w0.json').read_text())['windows'][0]
assert len(p['bank']) == len(set(p['bank'])) == 32
assert len(p['targets']) == len(set(p['targets'])) == 4
assert not set(p['bank']) & set(p['targets'])
assert p['window_id'] == r['window_id'] and p['targets'] == r['target_refs']
assert set(r['ctx_refs']) <= set(p['bank'])
sha = Path('work/S143_context_ranking/results/tacc/REPLAY_SHA256.txt').read_text().splitlines()
assert len(sha) == 2 and all(x.split()[0] == '913394e0f8d25b5f179aaffbdd6ba3d9ac7ed21d8f86dd393bf9235ccaf111bb' for x in sha)
print('PASS: replay plan matches S139, parity manifest valid, frozen replay SHA agrees with archived receipt')
PY
```

Complete output (exit 0):

```text
PASS: ref_grid/pred_u8/ssim ASTs identical
PASS: in-memory 640x480 reference conversion byte-identical
PASS: four-target PSNR/SSIM exact equality for range (0, 1)
PASS: four-target PSNR/SSIM exact equality for range (-1, 1)
PASS: S146 generator byte-identical to S141 generator
PASS: replay plan matches S139, parity manifest valid, frozen replay SHA agrees with archived receipt
```

### Appendix G — Split parser reproduction

Exact command (read-only reviewer):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import re

def old(txt):
    seqs = [(int(a), int(b)) for a, b in re.findall(r'start=(\d+) ; end=(\d+)', txt)]
    return seqs[0], seqs[1]

def fixed(txt):
    rows = re.findall(r'(sequence[01])\s*\[frames=(\d+)\]\s*\[start=(\d+) ; end=(\d+)\]', txt)
    assert len(rows) == 2 and {x[0] for x in rows} == {'sequence0', 'sequence1'}, 'split labels'
    seqs = {name: (int(a), int(b), int(n)) for name, n, a, b in rows}
    (h0, h1, nh), (c0, c1, nc) = seqs['sequence0'], seqs['sequence1']
    assert h0 == 0 and h1 >= h0 and c1 >= c0 and c0 == h1 + 1, 'split ranges'
    assert nh == h1 - h0 + 1 and nc == c1 - c0 + 1, 'split counts'
    return (h0, h1), (c0, c1)

txt = 'sequence1 [frames=200] [start=100 ; end=299]\nsequence0 [frames=100] [start=0 ; end=99]\n'
print('original parser, reversed label order:', old(txt))
print('patched parser, reversed label order:', fixed(txt))
assert fixed(txt) == ((0,99),(100,299))
for name, bad in [('overlap', 'sequence0 [frames=100] [start=0 ; end=99]\nsequence1 [frames=250] [start=50 ; end=299]'), ('wrong count', 'sequence0 [frames=99] [start=0 ; end=99]\nsequence1 [frames=200] [start=100 ; end=299]')]:
    try: fixed(bad)
    except AssertionError as e: print('PASS: rejected', name, 'with', str(e))
    else: raise AssertionError(name)
PY
```

Complete output (exit 0):

```text
original parser, reversed label order: ((100, 299), (0, 99))
patched parser, reversed label order: ((0, 99), (100, 299))
PASS: rejected overlap with split ranges
PASS: rejected wrong count with split counts
```

### Appendix H — Consolidated patch context and syntax verification

Exact command (parent; patches applied only to in-memory strings):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
import ast,re,subprocess,collections
report=Path('work/agents/CODEX_R268_S146OP_CODE_REVIEW.md').read_text()
ops=collections.defaultdict(list)
fence=chr(96)*3
for block in re.findall(fence+r'diff\n(.*?)'+fence,report,re.S):
 lines=block.splitlines(True); i=0; path=None
 while i<len(lines):
  if lines[i].startswith('--- a/'):
   path=lines[i][6:].strip(); i+=2; continue
  if not lines[i].startswith('@@ '): i+=1; continue
  m=re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@',lines[i]); assert m,lines[i]
  cur=int(m[1])-1; start=cur; original=Path(path).read_text().splitlines(True); i+=1; pend=None; added=[]; oldcount=newcount=0
  def flush():
   global pend,added
   if pend is not None:
    ops[path].append((pend,cur,''.join(added)))
    pend=None; added=[]
  while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
   line=lines[i]; sign=line[:1]; text=line[1:]
   if sign in (' ','-'):
    assert original[cur]==text,(path,cur+1,repr(original[cur]),repr(text))
    oldcount+=1
   if sign in (' ','+'): newcount+=1
   if sign==' ':
    flush(); cur+=1
   elif sign=='-':
    if pend is None: pend=cur
    cur+=1
   elif sign=='+':
    if pend is None: pend=cur
    added.append(text)
   else: raise AssertionError((path,line))
   i+=1
  flush(); assert (oldcount,newcount)==(int(m[2]),int(m[4])),(path,oldcount,newcount,m.groups())
patched={}
for path,changes in ops.items():
 old=Path(path).read_text().splitlines(True); result=[]; cursor=0
 for start,end,text in sorted(set(changes),key=lambda x:(x[0],x[1])):
  assert start>=cursor,('overlapping edits',path,start,cursor)
  result.extend(old[cursor:start]); result.append(text); cursor=end
 result.extend(old[cursor:]); new=''.join(result); patched[path]=new
 if path.endswith('.py'): ast.parse(new,filename=path)
 else:
  r=subprocess.run(['bash','-n'],input=new,capture_output=True,text=True)
  assert r.returncode==0,(path,r.stderr)
  for marker,body in re.findall(r"<<'([A-Z_]+)'\n(.*?)\n\1",new,re.S):
   ast.parse(body,filename=marker)
 print('PASS combined patch contexts and syntax:',path)
print('No production files written.')
PY
```

Complete output (exit 0):

```text
PASS combined patch contexts and syntax: work/S146_fresh12/s146op_chain.sh
PASS combined patch contexts and syntax: work/S146_fresh12/pool_op_s146.py
PASS combined patch contexts and syntax: work/S146_fresh12/run_retrieval_s146op.py
PASS combined patch contexts and syntax: work/S146_fresh12/analyze_s146.py
PASS combined patch contexts and syntax: work/S146_fresh12/stage_12scenes_s146.py
No production files written.
```

### Appendix I — Final source-drift and concurrency check

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
import hashlib,re,subprocess
p=Path('work/agents/CODEX_R268_S146OP_CODE_REVIEW.md')
text=p.read_text()
rows=re.findall(r'^SHA256 (\S+) ([0-9a-f]{64}|MISSING)$',text,re.M)
for name,want in rows:
 q=Path(name); got=hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else 'MISSING'
 assert got==want,(name,want,got)
print('PASS all recorded reviewed-source hashes unchanged')
print('GIT_STATUS_BEGIN')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('GIT_STATUS_END')
PY
```

Complete output (exit 0):

```text
PASS all recorded reviewed-source hashes unchanged
GIT_STATUS_BEGIN
 M work/agents/PREAMBLE_CODEX_CURRENT.md
?? docs/report/figures/
?? work/agents/CODEX_R266_KPSR_REJECTION.md
?? work/agents/CODEX_R267_S146_PATH_DECISION.md
?? work/agents/CODEX_R268_S146OP_CODE_REVIEW.md
?? work/agents/prompts/R266_FULL.md
?? work/agents/prompts/R266_PROMPT.md
?? work/agents/prompts/R267_FULL.md
?? work/agents/prompts/R267_PROMPT.md
?? work/agents/prompts/R268_FULL.md
?? work/agents/prompts/R268_PROMPT.md
?? work/agents/prompts/R269_FULL.md
?? work/agents/prompts/R269_PROMPT.md
GIT_STATUS_END
```

The untracked `docs/report/figures/` directory appeared during concurrent work; this review did not create, inspect or modify it. All recorded reviewed-source hashes remained unchanged.

## Delivery and follow-up

Changed file: `work/agents/CODEX_R268_S146OP_CODE_REVIEW.md` only. Existing source, protocols, outputs and other agents' files were left untouched. The initial checkout already contained an edited external-review preamble and untracked R266/R267/R268/R269 review material; these were not cleaned up. No SSH, Slurm, GPU, training, weight/dataset download, external message or research-ledger mutation was performed.

Next action for the executing agent: apply the verified focused corrections, complete the explicitly missing Amendment 3 evidence and pre-execution binding, stage the exact helper/source set, then perform the exposed parity and replay gates within the remaining recorded budget. If mandatory provenance cannot be supplied, retain HOLD; if any fresh policy is unavailable, report the full-panel unavailable result rather than replacing it with mem_pose. A follow-up session should inspect the actual sealed remote receipts/results; this review cannot certify them.
