# R274 — S147 implementation review

**Verdict: BLOCK LAUNCH as currently implemented.** The numerical development decision formulas are correct, and I found no schedule reconstruction off-by-one error. The blockers are incomplete checkpoint/data admission, an incomplete invalid-package fallback, unchecked baseline inputs, and missing fail-closed orchestration/budget gates. These findings do not constitute a scientific negative for Anchor-A.

Workspace: local Mac checkout. Reviewed source snapshot: HEAD 24e73643b402a31aad685ff5c9332e7e5071a32e; exact file hashes and CPU commands/complete outputs appear in Appendix A. All cited line numbers refer to that snapshot. No GPU, training, inference, SSH, Slurm, weight/data download, or contact with others was performed. Only this report is written. The existing untracked work/agents/prompts/R274_FULL.md was left alone.

The binding A–G text in PROTOCOL.md matches R273 §7; the implementation-note substitutions are treated as binding. The reported remote smoke results, current remote tensors/arrays, and CPU monitor construction receipts were not independently verified. In particular, the protocol's smoke values are not results of this review. new_method_validated=false and novelty_authorization=NONE remain unchanged.

Quantities in the appendix are **MEASURED CPU inspection/probe results**, not generation quality. Schedule counts derived from the frozen manifest are **DERIVED**. No literature claim is needed for this implementation review.

## 1. Blocking — checkpoint admission does not enforce the frozen experiment

Evidence: work/S147_anchor_a/train_s147.py:81–82,121–143,153–154,192–195; work/S147_anchor_a/gen_s147.py:130–145. Required contract: work/S147_anchor_a/PROTOCOL.md:29,35.

Resume checks only arm before strict=False loading. A checkpoint with missing adapter tensors can leave initialized values in place; extra keys that are genuine base-model keys can replace frozen weights. Neither operation is necessarily an unexpected-key error. Rank metadata, schema, recipe, input hashes, prototype identity, valid-update count, schedule cursor and optimizer/scheduler clocks are not checked. The next save uses newly constructed META, so changed current inputs can overwrite the provenance description of a resumed state.

The generator checks variant/rank and missing adapter keys, but not exact key-set equality or an independently supplied expected arm/checkpoint clock. Extra matching base keys can therefore overwrite the base there too. A wrong same-variant arm can also be accepted. Prototype validation checks only shape when BRANCH=null, not finiteness or equality to the frozen training prototype.

The full checkpoint does save optimizer/scheduler and global plus isolated Python/CUDA RNG states, but omits explicit permutation/cursor, recipe/schema and complete provenance. Final adapter files omit valid_updates. These are omissions in the required admission contract, not evidence that an existing remote checkpoint is corrupt.

Minimal immediately applicable containment for unsafe resume:

~~~diff
--- a/work/S147_anchor_a/train_s147.py
+++ b/work/S147_anchor_a/train_s147.py
@@ -128,2 +128,5 @@
 if last.exists():
+    raise RuntimeError(
+        'INVALID_IMPLEMENTATION: resume schema, keys, provenance, prototype and clocks '
+        'have not been validated')
     s = torch.load(last, weights_only=False)
~~~

This intentionally stops the interrupted engineering replay and therefore prevents full training. It is a containment patch, not a completed resume implementation. Replace it with a shared validator before reopening the gate: save schema, recipe, exact trainable names, frozen input-manifest identity, attempted/valid clocks, permutation/cursor/state and prototype; compare all against independently frozen expectations before loading; check exact adapter keys, tensor shape/dtype/finiteness, frozen F-arm LoRA identity, and the valid-update/scheduler/optimizer clocks against the schedule prefix. A warm start must not enter this path.

Minimal independent repair for the generator's extra-base-key defect:

~~~diff
--- a/work/S147_anchor_a/gen_s147.py
+++ b/work/S147_anchor_a/gen_s147.py
@@ -132,2 +132,4 @@
     assert st['variant'] == VARIANT and st['rank'] == RANK, (st['variant'], st['rank'])
+    assert set(st['adapter']) == set(C.adapter_state(pipe.model)), 'adapter key set mismatch'
+    assert all(torch.isfinite(v).all() for v in st['adapter'].values()), 'nonfinite adapter'
     res = pipe.model.load_state_dict(st['adapter'], strict=False)
~~~

The generator must additionally use that shared metadata validator with an expected arm and step supplied by the chain, not copied from the loaded checkpoint. Preserve explicit exceptions for pinned historical A and the documented F_null step-zero F_geo proxy. These two small patches alone do not discharge the complete loader contract.

## 2. Blocking — missing geometry provenance becomes a fallback; the validity predicate is incomplete

Evidence: work/S147_anchor_a/prep_dev_s147.py:41–51; work/S147_anchor_a/make_inputs_s147.py:10–16; work/S147_anchor_a/train_s147.py:46–50. Required contract: work/S147_anchor_a/PROTOCOL.md:41–47.

Missing CPU receipts are currently recorded as ordinary invalid geometry and the experiment continues. The protocol explicitly says missing validity provenance blocks engineering completion. Empty KPS lists pass vacuously; missing/empty focal lists and finite zero/negative focals also pass. The CPU probes reproduce those acceptance cases.

The saved CPU construction format contains only rendered uint8 RGB, boolean masks and KPS records: work/S144_A_wgs/warps_monitor_s144.py:75–83. Those outputs do not establish the required source-depth finiteness/pathology checks. The training invalid-list generator checks only median_reproj_px; the trainer adds shape/finiteness but no coverage range. The current local training receipts reproduce the frozen invalid list and show no additional bad positive scale/focal fields among retained records (Appendix A); that does not recover discarded depths or verify CPU monitor receipts.

Minimal predicate repair:

~~~diff
--- a/work/S147_anchor_a/prep_dev_s147.py
+++ b/work/S147_anchor_a/prep_dev_s147.py
@@ -42,5 +42,8 @@
-    if r is None: why.append('no receipt')
-    else:
-        for q in r['kps']:
-            if not (fin(q.get('median_reproj_px')) and fin(q.get('sigma')) and q['sigma'] > 0 and all(fin(f) for f in q.get('focals', []))):
-                why.append('non-finite KPS record')
+    if r is None or not isinstance(r.get('kps'), list) or not r['kps']:
+        raise RuntimeError(f'INVALID_IMPLEMENTATION: missing KPS provenance for {k}')
+    for q in r['kps']:
+        if not {'median_reproj_px', 'sigma', 'focals'} <= q.keys() or not q['focals']:
+            raise RuntimeError(f'INVALID_IMPLEMENTATION: incomplete KPS provenance for {k}')
+        if not (fin(q['median_reproj_px']) and fin(q['sigma']) and q['sigma'] > 0
+                and all(fin(f) and f > 0 for f in q['focals'])):
+            why.append('invalid KPS record')
--- a/work/S147_anchor_a/train_s147.py
+++ b/work/S147_anchor_a/train_s147.py
@@ -50,1 +50,3 @@
-        assert w.shape == (4, 5, 72, 72) and torch.isfinite(w).all(), c['id']; W5[c['id']] = w
+        assert w.shape == (4, 5, 72, 72) and torch.isfinite(w).all(), c['id']
+        assert ((w[:, 4] >= 0) & (w[:, 4] <= 1)).all(), c['id']
+        W5[c['id']] = w
~~~

These corrections do not manufacture the missing depth/latent provenance. Until source-only validity evidence and checks are available, the minimal honest launch interlock is:

~~~diff
--- a/work/S147_anchor_a/s147_chain.sh
+++ b/work/S147_anchor_a/s147_chain.sh
@@ -31,1 +31,2 @@
+echo '[s147] INVALID_IMPLEMENTATION: complete source-only depth/latent validity gate is required'; exit 3
 OMP_NUM_THREADS=8 $PY $S/prep_dev_s147.py $S/plan_dev_s147.json $DV $WDV $G4/dev_A $PD | tail -n 2
~~~

Remove that interlock only after implementing and verifying the missing gate. Do not expand the frozen invalid list after training starts. A newly discovered incompatibility must stop the run, not silently change exposure.

## 3. Blocking — true branch bypass still depends on failed warp arrays

Evidence: work/S147_anchor_a/gen_s147.py:151–162,263,274–280,301–305; work/S147_anchor_a/prep_dev_s147.py:47–50,54–64. Required behavior: work/S147_anchor_a/PROTOCOL.md:43–47.

The convolution bypass itself is genuine: it returns base before calling warp, including its bias. However, generation always opens and VAE-encodes the original warp files first. A package marked invalid because of malformed array shape still crashes in stacking, pooling or encoding before reaching bypass. Ordinary A/A_cont also needlessly depend on those files. Thus the general declared invalid-package policy is not implemented, even though the currently reported objective-invalid c02028 may have well-formed arrays.

Minimal repair: ordinary sampling with A or a bypassed branch must not read/encode the failed warp; use dummy zero extras only to satisfy the B input interface.

~~~diff
--- a/work/S147_anchor_a/gen_s147.py
+++ b/work/S147_anchor_a/gen_s147.py
@@ -275,6 +275,11 @@
-        ws = [np.load(WARP_DIR / wf) for wf in c['warp_files']]
-        wimg = torch.stack([torch.from_numpy(z['filled'].astype(np.float32) / 255. * 2 - 1).permute(2, 0, 1) for z in ws]).to(device, dtype)
-        cov = torch.stack([torch.nn.functional.avg_pool2d(torch.from_numpy(z['valid'].astype(np.float32))[None, None], 8)[0] for z in ws]).to(device)
+        need_warp = mode != 'none' or (VARIANT == 'B' and _BR['cur'] != 'off')
+        if need_warp:
+            ws = [np.load(WARP_DIR / wf) for wf in c['warp_files']]
+            wimg = torch.stack([torch.from_numpy(z['filled'].astype(np.float32) / 255. * 2 - 1).permute(2, 0, 1) for z in ws]).to(device, dtype)
+            cov = torch.stack([torch.nn.functional.avg_pool2d(torch.from_numpy(z['valid'].astype(np.float32))[None, None], 8)[0] for z in ws]).to(device)
+        else:
+            cov = torch.zeros((4, 1, 72, 72), device=device, dtype=dtype)
         with torch.inference_mode():
             lat = encode_vae_image(imgs, ae, device, dtype); emb = encode_image(imgs, clip, device, dtype)
-            zw = encode_vae_image(wimg, ae, device, dtype)
+            zw = encode_vae_image(wimg, ae, device, dtype) if need_warp else torch.zeros(
+                (4, 4, 72, 72), device=device, dtype=dtype)
~~~

The existing manual-off replay tests only c02000 (s147_chain.sh:77–84,106–109). Also check the automatic bypass on every actual invalid development package before quantization:

~~~diff
--- a/work/S147_anchor_a/score_s147.py
+++ b/work/S147_anchor_a/score_s147.py
@@ -37,1 +37,4 @@
         for name, d in ARMS.items():
+            if not ok and name in {'F_geo', 'F_null', 'F_geo_proto', 'F_geo_perm'}:
+                assert (Path(d) / f"{k}__s{s}.npy").read_bytes() == (AD / f"{k}__s{s}.npy").read_bytes(), \
+                    ('invalid-package bypass differs from A', name, k, s)
~~~

J_geo must not be compared bytewise to A: its bypass intentionally retains its jointly updated LoRA.

## 4. Blocking — baseline coefficient freezing and consumed-input identity are not enforced

Evidence: work/S147_anchor_a/prep_dev_s147.py:67–85; work/S147_anchor_a/score_s147.py:17–19; work/S147_anchor_a/s147_chain.sh:30–32. Requirement: work/S147_anchor_a/PROTOCOL.md:53–55,109–110.

The chain refits BL_A0 but never requires the documented frozen alpha=0.30. The saved record hashes the plan and validity JSON, but stores only an A directory name, not hashes of its prediction arrays. BL_AC's coefficient is read freely from ALPHA.json rather than checked against 0.60. The current archived AC coefficient is correct; the defect is failure to reject changed inputs/coefficients.

Minimal coefficient/input fix:

~~~diff
--- a/work/S147_anchor_a/prep_dev_s147.py
+++ b/work/S147_anchor_a/prep_dev_s147.py
@@ -83,3 +83,7 @@
 sc = {a: score(a) for a in GRID}; best = max(sc.values()); alpha = min(a for a in GRID if sc[a] == best)
+assert alpha == 0.30, f'INVALID_IMPLEMENTATION: frozen BL_A0 alpha changed to {alpha}'
+a_hashes = {f"{c['ctx_key']}__s{s}.npy": sha(AD / f"{c['ctx_key']}__s{s}.npy")
+            for c in plan for s in (3, 4)}
 (OUT / 'BL_A0_ALPHA.json').write_text(json.dumps({'alpha': alpha, 'psnr_by_alpha': sc, 'rule': 'max seed-then-clip, sequence-equal mean PSNR; ties smaller',
-    'inputs': {'plan_sha256': sha(PL), 'A_none_dir': str(AD), 'validity_sha256': sha(OUT / 'DEV_GEOMETRY_VALIDITY.json')}}, indent=1) + '\n')
+    'inputs': {'plan_sha256': sha(PL), 'A_none_dir': str(AD), 'A_none_sha256': a_hashes,
+               'validity_sha256': sha(OUT / 'DEV_GEOMETRY_VALIDITY.json')}}, indent=1) + '\n')
--- a/work/S147_anchor_a/score_s147.py
+++ b/work/S147_anchor_a/score_s147.py
@@ -11,1 +11,1 @@
-import json, sys, types
+import hashlib, json, sys, types
@@ -17,1 +17,2 @@
 A_AC = json.loads(Path(sys.argv[8]).read_text())['alpha']['AC']; OUT = Path(sys.argv[9])
+assert A_AC == 0.60, 'frozen BL_AC coefficient changed'
@@ -19,1 +20,5 @@
 VAL = json.loads((PD / 'DEV_GEOMETRY_VALIDITY.json').read_text()); A0 = json.loads((PD / 'BL_A0_ALPHA.json').read_text())['alpha']
+assert A0 == 0.30, 'frozen BL_A0 coefficient changed'
+for filename, expected_hash in json.loads((PD / 'BL_A0_ALPHA.json').read_text())['inputs']['A_none_sha256'].items():
+    assert hashlib.sha256((AD / filename).read_bytes()).hexdigest() == expected_hash, filename
+
~~~

This records the actual refit inputs and protects them through scoring. It must be combined with the pretraining frozen source/input manifest below; merely rehashing changed files immediately before training does not establish identity with the original frozen panel.

## 5. Blocking — malformed archived predictions can become finite comparator scores

Evidence: work/S147_anchor_a/score_s147.py:28,32,34–40; work/S147_anchor_a/score_s144_functions.py:11–14; work/S147_anchor_a/analyze_s147.py:25–32.

Only new candidate arrays are checked for raw shape/finiteness. Archived A_none, A_C, V and fallback V go directly through pred_u8. In the CPU probe, an all-NaN float image becomes an all-zero finite uint8 image. Full-frame metric finiteness then cannot detect the corrupt input. Archived comparator matching is skipped for invalid geometry packages, precisely where fallback V and ordinary A must still be trustworthy.

Keep the helper block verbatim. Validate arrays in the scorer before conversion:

~~~diff
--- a/work/S147_anchor_a/score_s147.py
+++ b/work/S147_anchor_a/score_s147.py
@@ -21,1 +21,6 @@
 runs = {}
+def prediction(path):
+    arr = np.load(path, allow_pickle=False)
+    assert arr.shape == (4, 3, 576, 576) and np.isfinite(arr).all(), str(path)
+    return [M.pred_u8(f) for f in arr]
+
@@ -28,1 +33,1 @@
-        V = [M.pred_u8(f) for f in np.load(FD / f"{k}__V__s0.npy")]
+        V = prediction(FD / f"{k}__V__s0.npy")
@@ -32,4 +37,4 @@
-        V = [M.pred_u8(f) for f in np.load(FV / f"{k}__fallback__V__s0.npy")]
+        V = prediction(FV / f"{k}__fallback__V__s0.npy")
     for s in SEEDS:
-        A_none = [M.pred_u8(f) for f in np.load(AD / f"{k}__s{s}.npy")]
-        src = [M.pred_u8(f) for f in np.load(AD / f"{k}__C__s{s}.npy")] if ok else A_none
+        A_none = prediction(AD / f"{k}__s{s}.npy")
+        src = prediction(AD / f"{k}__C__s{s}.npy") if ok else A_none
~~~

Apply the same raw check in BL_A0 preparation, which also converts archived A first:

~~~diff
--- a/work/S147_anchor_a/prep_dev_s147.py
+++ b/work/S147_anchor_a/prep_dev_s147.py
@@ -77,1 +77,3 @@
-        A = [M.pred_u8(f) for f in np.load(AD / f"{k}__s{s}.npy")]
+        arr = np.load(AD / f"{k}__s{s}.npy", allow_pickle=False)
+        assert arr.shape == (4, 3, 576, 576) and np.isfinite(arr).all(), (k, s)
+        A = [M.pred_u8(f) for f in arr]
~~~

## 6. Blocking — the frozen provenance gate is a write-only receipt

Evidence: work/S147_anchor_a/s147_chain.sh:8–15,24; work/S147_anchor_a/train_s147.py:81–82. Requirement: work/S147_anchor_a/PROTOCOL.md:17.

Only source A is checked against a predeclared expected hash. CODE_SHA256.txt records whatever happens to be present remotely. Its inventory includes the stage files, clip manifest, pipeline.py and base model, but not all loaded VMem dependencies/configuration, VAE/CLIP/CUT3R weights, latent shards, warp construction/artifacts and archived comparator sources. The prototype is not frozen and verified against an independently established expected identity. A pipeline or model-weight hash written after deployment is not a comparison with a frozen expected artifact.

No patch can invent these missing expected hashes. A minimal launch interlock can require and verify a pre-frozen complete manifest, before namespace creation or compute:

~~~diff
--- a/work/S147_anchor_a/s147_chain.sh
+++ b/work/S147_anchor_a/s147_chain.sh
@@ -10,1 +10,5 @@
 [ "$(sha256sum $ADA | cut -d' ' -f1)" = "$ADA_SHA" ] || { echo "[s147] adapter A hash mismatch"; exit 3; }
+: "$S147_FROZEN_INPUTS"
+test -s "$S147_FROZEN_INPUTS"
+sha256sum --check --strict "$S147_FROZEN_INPUTS"
+export S147_FROZEN_INPUTS
~~~

This patch intentionally refuses launch when the manifest is absent. Before supplying it, independently freeze and inspect its complete inventory, including the source-only validity receipts, baseline inputs, and prototype. Bind its hash into checkpoints and generation/scoring receipts and recheck mutable consumed files before each stage. Do not generate the expected manifest from the unverified remote files in the same preflight. This is ordinary protocol provenance, not a request for retired authorization packets.

## 7. Blocking — the chain is not fully fail closed under background execution

Evidence: work/S147_anchor_a/s147_chain.sh:18–27,39–42,60–61,78–89,107–119,124–126.

Three distinct shell cases matter:

- If the first wait fails under set -e, the parent exits before waiting for its sibling. The sibling remains running. The CPU shell probe confirms that its output appears after the first worker fails. This does not advance the parent to the next stage, but it leaves compute/artifact writing unmanaged after the gate failure.
- gen is used in && lists in development. Bash suppresses errexit inside such a function invocation. The unguarded mkdir/sha256sum steps can fail and still reach Python; only the Python invocation has an explicit error handler.
- same compares command-substitution strings. If both hash pipelines fail and yield empty stdout, empty equals empty and fidelity passes. The probe demonstrates this mechanism with failing input reads.

Minimal fixes:

~~~diff
--- a/work/S147_anchor_a/s147_chain.sh
+++ b/work/S147_anchor_a/s147_chain.sh
@@ -5,1 +5,9 @@
 set -euo pipefail
+wait_pair() {
+  local rc=0 status
+  wait "$1" || { status=$?; rc=$status; }
+  wait "$2" || { status=$?; if [ "$rc" -eq 0 ]; then rc=$status; fi; }
+  return "$rc"
+}
+# Always drain every direct child on an early exit; do not orphan the sibling.
+trap 'rc=$?; trap - EXIT; wait || :; exit "$rc"' EXIT
@@ -24,1 +32,2 @@
-  mkdir -p $6; sha256sum $S/gen_s147.py $S/s141_common.py $5 $3 > $6/CODE_SHA256.txt
+  mkdir -p "$6" || return
+  sha256sum "$S/gen_s147.py" "$S/s141_common.py" "$5" "$3" > "$6/CODE_SHA256.txt" || return
@@ -27,1 +36,7 @@
-same() { [ "$(sha256sum $1 | cut -d' ' -f1)" = "$(sha256sum $2 | cut -d' ' -f1)" ]; }
+same() {
+  local a b
+  test -f "$1" && test -f "$2" || return 1
+  a=$(sha256sum "$1") || return
+  b=$(sha256sum "$2") || return
+  [ "${a%% *}" = "${b%% *}" ]
+}
@@ -40,1 +55,1 @@
-wait $P1; wait $P2
+wait_pair "$P1" "$P2"
~~~

Use wait_pair for the same two-wait idiom at original lines 40,61,79,81,88,89,108 as well. The EXIT trap is a containment backstop for those paths even before that mechanical replacement. Draining both jobs deliberately preserves child errors and prevents the launcher exiting while a sibling is still writing. If immediate termination is required, use supervised process groups that terminate Python descendants as well; killing only a background shell PID is insufficient.

The final if also treats any JSON-load/interpreter failure as a scientific development stop. Use the same interpreter and separate gate parsing from the Boolean branch:

~~~diff
--- a/work/S147_anchor_a/s147_chain.sh
+++ b/work/S147_anchor_a/s147_chain.sh
@@ -124,1 +124,4 @@
-if python3 -c "import json,sys; sys.exit(0 if json.load(open('$G/DEV_GATE.json'))['GATE']['GO'] else 1)"; then
+GO=$("$PY" -c "import json,sys; g=json.load(open(sys.argv[1]))['GATE']['GO']; assert type(g) is bool; print(int(g))" "$G/DEV_GATE.json") || {
+  echo '[s147] INVALID_IMPLEMENTATION: unreadable development gate'; exit 3;
+}
+if [ "$GO" = 1 ]; then
~~~

No claim is made that any remote worker was actually orphaned; only local short-lived shell reproductions were executed.

## 8. Blocking — budget projections do not implement §G

Evidence: work/S147_anchor_a/s147_chain.sh:17,34–85,59–73,87–89,112–119; work/S147_anchor_a/train_s147.py:150–155,177–188. Requirements: work/S147_anchor_a/PROTOCOL.md:37,83–85,125–126.

The pilot uses median inner-loop timing plus hard-coded startup/save allowances. It does not measure a representative checkpoint/finalization cycle. The chain does not enforce the engineering/preparation cap, has no complete development projection before generation, and has no stage-allocation accounting across retries. T0 is only printed at completion. These are missing gates, not a measured claim that the current workload exceeds a cap.

Until measured end-to-end accounting is implemented, the smallest honest patch stops before the unaccounted GPU work:

~~~diff
--- a/work/S147_anchor_a/s147_chain.sh
+++ b/work/S147_anchor_a/s147_chain.sh
@@ -35,1 +35,2 @@
+echo '[s147] INVALID_IMPLEMENTATION: engineering allocation and complete stage timing receipts are not verified'; exit 3
 CUDA_VISIBLE_DEVICES=3 OMP_NUM_THREADS=8 $PY $S/eng_s147.py $G1/clips_s141.json $G1/lat $G1/warps $ADA $S/INVALID_GEOMETRY.json $G/eng/ENG.json \
@@ -114,1 +115,2 @@
+echo '[s147] INVALID_IMPLEMENTATION: complete development projection is not verified'; exit 3
 ( gen 3 B $G/runs/F_geo/adapter_final.pt orig $PG $G/dev/F_geo 3,4 $DV $WDV && gen 3 B $G/runs/J_geo/adapter_final.pt orig $PG $G/dev/J_geo 3,4 $DV $WDV && \
~~~

These are explicit containment fences, not a replacement budget implementation and not a finding of actual budget exhaustion. Remove them only when stage projections include loading, full fixed job lists, validation, saves, finalization, pilots/replays/retries and occupied GPU wall time under the frozen caps. No additional pilot was run by this review.

## 9. Should-fix — engineering verifies an update only for the unconditional case

Evidence: work/S147_anchor_a/eng_s147.py:60–69; requirement work/S147_anchor_a/PROTOCOL.md:33.

Both backwards execute, but the second zero_grad discards the conditional gradients and the only optimizer step is after the loop. The gate therefore cannot claim that both conditioning cases produced a parameter update.

~~~diff
--- a/work/S147_anchor_a/eng_s147.py
+++ b/work/S147_anchor_a/eng_s147.py
@@ -60,1 +60,2 @@
 for tag in ('c', 'uc'):
+    before = [p.detach().clone() for p in params]
@@ -66,1 +67,3 @@
-opt.step()
+    opt.step()
+    res[f'{tag}_parameter_update'] = any(not torch.equal(p, b) for p, b in zip(params, before))
+    ok &= res[f'{tag}_parameter_update']
~~~

The existing whole-state before/after comparison still verifies frozen tensors across both updates. The frozen checkpointed-forward/finite-difference tolerance substitutions were reviewed as specified; no unsupported ordinary-backward parity claim is made here.

## 10. Should-fix — completeness is self-referential and the development report is incomplete

Evidence: work/S147_anchor_a/analyze_s147.py:17–22,35–68,76–78; work/S147_anchor_a/score_s147.py:20,40–46. Requirements: work/S147_anchor_a/PROTOCOL.md:45,47,53,57,63,65.

The current supplied plan is correct. Nevertheless, analysis derives expected IDs and sequence labels from the scores themselves. Some other set of the same cardinality can pass; per-seed metadata disagreement is not rejected. Bind the score cells to the frozen plan and check each full-frame cell before aggregation:

~~~diff
--- a/work/S147_anchor_a/analyze_s147.py
+++ b/work/S147_anchor_a/analyze_s147.py
@@ -17,1 +17,12 @@
 runs = S['runs']; assert len(runs) == 64
+expected = {c['ctx_key']: c for c in json.loads(
+    Path(__file__).with_name('plan_dev_s147.json').read_text())['contexts']}
+assert set(runs) == {f'{w}__s{s}' for w in expected for s in (3, 4)}
+for w, c in expected.items():
+    rr = [runs[f'{w}__s{s}'] for s in (3, 4)]
+    assert rr[0]['geometry_valid'] == rr[1]['geometry_valid']
+    for s, r in zip((3, 4), rr):
+        assert (r['window_id'], r['seed'], r['seq'], r['kind']) == (c['window_id'], s, c['seq'], c['kind'])
+        for a in ARMS:
+            for m in ('psnr_db', 'ssim'):
+                assert isinstance(r[a][m], (int, float)) and math.isfinite(r[a][m]), (w, s, a, m)
~~~

GO currently combines only useful/practical Boolean values (analyze_s147.py:76–78). It relies on the chain for engineering/data gates; those gates are incomplete as findings 1–8 establish. Standalone DEV_GATE.json must not be treated as an independent engineering certificate.

Mandatory descriptive omissions are fallback fraction, valid-only contrasts, archived BL_FC, individual-seed means beyond the primary, memory/static categories, and region pixel denominators. Add them without changing any advancement threshold or allowing them to rescue GO:

~~~diff
--- a/work/S147_anchor_a/score_s147.py
+++ b/work/S147_anchor_a/score_s147.py
@@ -41,1 +41,4 @@
         rec = {'window_id': c['window_id'], 'seed': s, 'seq': c.get('seq'), 'kind': c.get('kind'), 'geometry_valid': ok}
+        rec['region_pixels'] = {'full': sum(m.size for m in Mk),
+                                'covered': sum(int(m.sum()) for m in Mk),
+                                'holes': sum(int((~m).sum()) for m in Mk)}
--- a/work/S147_anchor_a/analyze_s147.py
+++ b/work/S147_anchor_a/analyze_s147.py
@@ -69,1 +69,28 @@
 P, Q = res['psnr_db'], res['ssim']
+def descriptive(ws, seeds=(3, 4), archived=False):
+    source = S4['runs'] if archived else runs
+    arms = ['BL_FC'] if archived else ARMS
+    out = {'n_clips': len(ws), 'n_cells': len(ws) * len(seeds), 'sequences': {}}
+    for q in SEQS:
+        ww = [w for w in ws if seq[w] == q]
+        out['sequences'][q] = {'n_clips': len(ww), 'n_cells': len(ww) * len(seeds),
+            'means': {m: {a: float(np.mean([source[f'{w}__s{s}'][a][m]
+                for w in ww for s in seeds])) if ww else None for a in arms}
+                for m in ('psnr_db', 'ssim')}}
+    out['means'] = {m: {a: float(np.mean([out['sequences'][q]['means'][m][a]
+        for q in SEQS])) if all(out['sequences'][q]['n_clips'] for q in SEQS) else None
+        for a in arms} for m in ('psnr_db', 'ssim')}
+    if not archived:
+        out['contrasts'] = {m: {f'{a} - {b}':
+            out['means'][m][a] - out['means'][m][b]
+            if out['means'][m][a] is not None else None for a, b in pairs}
+            for m in ('psnr_db', 'ssim')}
+    return out
+res['fallback_fraction'] = sum(not v for v in valid.values()) / len(clips)
+res['valid_only'] = descriptive([w for w in clips if valid[w]])
+res['individual_seed_panels'] = {str(s): descriptive(clips, (s,)) for s in (3, 4)}
+res['categories'] = {k: descriptive([w for w in clips
+    if runs[f'{w}__s3']['kind'] == k]) for k in ('memory', 'static')}
+res['archived_BL_FC_original_geometry_descriptive_only'] = descriptive(clips, archived=True)
+res['region_pixel_denominators'] = {k: r['region_pixels'] for k, r in runs.items()}
+
~~~

Archived BL_FC must retain the explicit original-geometry/historical label; it is not an operational fallback comparator or a gate input. The existing regional panel/bootstrap also yields NaN if an entire sequence has no defined region (analyze_s147.py:44–54,65–67). This edge case is not established on the current reported panel. It should produce null with the denominators above, retaining the equal-sequence estimand rather than silently reweighting to the other sequence. A minimal fail-closed guard pending null propagation is:

~~~diff
--- a/work/S147_anchor_a/analyze_s147.py
+++ b/work/S147_anchor_a/analyze_s147.py
@@ -45,1 +45,3 @@
+    if any(not any(seq[w] == q and d[w] is not None for w in clips) for q in SEQS):
+        raise RuntimeError('undefined sequence-region mean: report null with denominators before issuing GO')
     sm = {q: float(np.mean([d[w] for w in clips if seq[w] == q and d[w] is not None])) for q in SEQS}
~~~

## Checks that did not reveal a defect

These are bounded source/CPU findings, not remote engineering passes.

| Requested check | Finding and source |
|---|---|
| RNG and epoch reconstruction | Isolated CFG and sigma/noise streams are initialized/restored at train_s147.py:127–134; scheduled draws precede skipping at :159–175. Validation has its own generator at :110–116. Actual NumPy reconstruction passed boundary cases in Appendix A. This is not a CUDA interrupted-training replay. |
| Invalid exposure and warm-up | Invalid attempts do not call optimizer/scheduler at train_s147.py:164–175. The frozen manifest produces the specified attempted/valid counts in Appendix A. LambdaLR at :80 reaches the full rate on the specified valid-update warm-up boundary in a CPU scheduler probe. |
| Fresh-run trainable ownership | train_s147.py:69–79 selects branch-only F, branch+LoRA J, and LoRA-only A_cont. s141_common.py:109–126 freezes base tensors and serializes all adapter tensors. Final F LoRA equality is asserted at train_s147.py:193–194. This does not cure malicious/stale checkpoint loading or replace complete remote frozen-tensor evidence. Exact optimizer names should be persisted in the checkpoint repair. |
| Prototype | train_s147.py:51–57 reduces valid training clips only, in float64 with final float32 cast. Original warp latent serialization is float32 at work/S141_finetune/warps_s141.py:93–97. Generation substitutes only latent channels and retains coverage at gen_s147.py:301–305. |
| Conditioning and context bias | Both c/uc get extras at gen_s147.py:187–189. s141_common.py:157–164 uses zero context extras; its WarpInConv at :97–106 retains bias on those slots. |
| Sampler and permutation reuse | AST comparisons confirm unchanged sample_none, sample_w2cr, _cond, transforms and perm_latent versus S144. gen_s147.py:235–246 retains the S145 seeded private PCG64 permutation and moved fractions; sampler noise is reseeded at :181–197. Receipts record moved fractions at :307–309. |
| COPY and operational definitions | prep_dev_s147.py:33–36,52–60 matches the nearest-camera rule in work/S141_finetune/build_clips_s141.py:26–29, including first-context tie break. score_s147.py:25–36 uses COPY for invalid B2, zero coverage, COPY's VAE round trip, and A_none as the invalid BL_AC source. These definitions are correct subject to admission/fallback fixes above. |
| Baseline fitting arithmetic | prep_dev_s147.py:76–83 averages seeds within clips and equally averages sequence means; exact ties select the smaller alpha. Its freezing and raw-input checks are incomplete, as above. |
| S144 helper block | score_s144_functions.py:6–31 is verbatim S144 score_s144.py:18–43. Pooled target SSE/PSNR, SSIM and blend conversion therefore retain the archived definitions. Keep that file unchanged. |
| Main aggregation/bootstrap | analyze_s147.py:35–54 averages seeds then clips then sequences; paired clip differences are resampled within each sequence with RNG 0. Full-frame finiteness is checked, but cell/metadata and empty-region handling need the fixes above. |
| Every numerical development gate | analyze_s147.py:69–78 implements PSNR >= threshold, SSIM >= guardrail, strict sequence positivity for primary/useful and permutation, nonnegative sequences for practical, and the exact mandatory comparator list. Boundary-injection outputs are in Appendix A. There is correctly no added permutation SSIM gate. J_geo comparisons remain descriptive at :58–63. |
| Plans and stopping scope | plan_dev_s147.json matches archived ordinary-A contexts; plan_replay_s147.json matches its first context; plan_chess_s147.json matches S145 (Appendix A). plan_score_chess_s147.json:1–34 is an inherited B_mem scoring plan, not a supported gen_s147 mode (gen_s147.py:264–265). It is unused by s147_chain.sh:112–127, so it does not add an unauthorized chess sweep. Confirmation is correctly left pending at chain:124–126. |

## Scope, limitations, and handoff

The output is a pre-run code review, not an execution certificate. Full training/GPU tests, byte-identity replay, checkpoint interruption replay and remote data validity were not run because this brief forbids them. Repository tests/linter were not run: no executable file was changed, and the targeted CPU checks below exercise only inspection, extracted control flow, small tensors and shell semantics.

Patches are proposals, not applied changes. Where required evidence does not exist locally, the patch is explicitly a launch interlock rather than fabricated validation. Do not interpret those interlocks as completed functionality.

Changed file: work/agents/CODEX_R274_S147_CODE_REVIEW.md only. Follow-up: implement the repairs, freeze any necessary pre-output amendment, complete source/input and geometry provenance, then rerun the specified engineering gates within the measured budget before full training. If a gate cannot be completed, use the protocol's invalid/incomplete-test wording; do not infer a scientific negative.

## Appendix A — Exact CPU commands and complete outputs

All commands below were executed from the repository root. No omitted stdout/stderr is represented as a successful check. They create no files; PYTHONDONTWRITEBYTECODE is set. The test patches above were not applied or claimed tested. The small torch loading example demonstrates strict=False semantics on a toy module, not a load of the remote VMem checkpoint. Shell probes use local short-lived children, not cluster jobs.


### A1. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess
scripts = {
 'background_wait': 'set -euo pipefail; (sleep 0.05; exit 7) & P1=$!; (sleep 0.15; echo SECOND_WORKER_CONTINUED) & P2=$!; wait "$P1"; wait "$P2"; echo REACHED_NEXT_STAGE',
 'and_list_function': 'set -euo pipefail; gen() { false; echo CONTINUED_AFTER_FAILED_PREFLIGHT; }; (gen && echo NEXT_GENERATION_STARTED)',
 'missing_fidelity_files': 'set -euo pipefail; same() { [ "$(cat /dev/null/nonexistent 2>/dev/null | cut -d" " -f1)" = "$(cat /dev/null/nonexistent 2>/dev/null | cut -d" " -f1)" ]; }; same && echo EMPTY_HASH_COMPARISON_PASSED',
}
for name, code in scripts.items():
 p = subprocess.run(['bash', '-c', code], capture_output=True, text=True)
 print(name, 'returncode=', p.returncode, 'stdout=', repr(p.stdout), 'stderr=', repr(p.stderr))
PY
~~~

Complete output (exit code 0):

~~~text
background_wait returncode= 7 stdout= 'SECOND_WORKER_CONTINUED\n' stderr= ''
and_list_function returncode= 0 stdout= 'CONTINUED_AFTER_FAILED_PREFLIGHT\nNEXT_GENERATION_STARTED\n' stderr= ''
missing_fidelity_files returncode= 0 stdout= 'EMPTY_HASH_COMPARISON_PASSED\n' stderr= ''
~~~

### A2. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
p=Path('work/S147_anchor_a')
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
for f in sorted(p.iterdir()):
 if f.is_file(): print('SHA256',f,hashlib.sha256(f.read_bytes()).hexdigest())
print('STATUS',repr(subprocess.check_output(['git','status','--short'],text=True)))
PY
~~~

Complete output (exit code 0):

~~~text
HEAD 24e73643b402a31aad685ff5c9332e7e5071a32e
SHA256 work/S147_anchor_a/INVALID_GEOMETRY.json bcaf322bed389679b674b503388eb5a756b890b07e28f5f61723fdb7199aa456
SHA256 work/S147_anchor_a/PROTOCOL.md f3489a9ce9be90958b96dfbaf1e2573db3b02598c4e4e53f54d697ca3277939b
SHA256 work/S147_anchor_a/PROTOCOL_DRAFT.md 503cfb82d4777a80e07b1c0d3f136eee455f180550f8c669773b6943382d39f3
SHA256 work/S147_anchor_a/analyze_s147.py b83ff31e217dd8d416d8a1061b86886bf42f8ea06f0f124f0b11224d6305fd65
SHA256 work/S147_anchor_a/eng_s147.py 1015ce8351821a7286bfeb276d2ba150a6f4fcfdd37035c5100854d36d3ca306
SHA256 work/S147_anchor_a/gen_s147.py 13fbc594108ca1a28811f639eb7a502eb2c67bbc9d0b1b02c6630c598cb94312
SHA256 work/S147_anchor_a/make_inputs_s147.py 02379ec114a1aaae69ba1be9b76d0ea4cc1decfee1f4ee14c687b8bfc9627c75
SHA256 work/S147_anchor_a/plan_chess_s147.json fbae82c640e29512b2aabe76a51957f464ee7a99bd7b8fa27f7471129f98e89b
SHA256 work/S147_anchor_a/plan_dev_s147.json 76156c2523bea8ad9a9098a1edbfede4d2218f2a0008ad96c23d4db5a32074e3
SHA256 work/S147_anchor_a/plan_replay_s147.json b4dd75db321a57de6f70de5e0b0c4e64893ebdc0ec2281be6bcfa9079bed8fa6
SHA256 work/S147_anchor_a/plan_score_chess_s147.json 0753f9aa743fc307e5af5f07223790642d6594d353f45a3e2966d22e22517a57
SHA256 work/S147_anchor_a/prep_dev_s147.py 097eab5c9657732d7b667b9833cef2f6b984dc782f93d31e3356b322119c48ac
SHA256 work/S147_anchor_a/s141_common.py 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc
SHA256 work/S147_anchor_a/s147_chain.sh 57dd31faac9abbd9e43b444044acfb8bb3e57252a409ca5235af84807f3d6e21
SHA256 work/S147_anchor_a/score_s144_functions.py 037fdd21569cbfcdfb690ed14361c6c5a5cc3d72946df494697663d2fc373cf1
SHA256 work/S147_anchor_a/score_s147.py 63ae5173d9425a1556086d40c97f3202b122005cdac8a0b310c33de26ac8511d
SHA256 work/S147_anchor_a/train_s147.py 87898a79fa82553ff1dea89f968914deed8a3622a8a2171a97ed5d66ecce6947
STATUS '?? work/agents/prompts/R274_FULL.md\n'
~~~

### A3. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import ast, json, hashlib
from pathlib import Path
p=Path('work/S147_anchor_a'); old=Path('work/S144_A_wgs/gen_s144.py')
def fn(path,name):
 return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
for n in ('perm_latent','sample_none','sample_w2cr','_cond','load_rgb','load_pose','model_grid_K'):
 print(n,'AST identical to S144:',ast.dump(fn(p/'gen_s147.py',n))==ast.dump(fn(old,n)))
plan=json.loads((p/'plan_dev_s147.json').read_text())['contexts']
arch=[c for c in json.loads(Path('work/S144_A_wgs/plan_dev_A.json').read_text())['contexts'] if c['mode']=='none']
print('dev_plan_equal',plan==arch,'unique_context_groups',len({c['ctx_group'] for c in plan}))
print('common_helper_identical',(p/'s141_common.py').read_bytes()==Path('work/S141_finetune/s141_common.py').read_bytes())
src=Path('work/S144_A_wgs/score_s144.py').read_text(); helper=(p/'score_s144_functions.py').read_text()
block=helper[helper.index('def ref_grid'):]
print('metric_function_block_verbatim',block in src)
print('current_archived_alpha_AC',json.loads(Path('work/S144_A_wgs/results/ALPHA.json').read_text())['alpha']['AC'])
print('binding_R273_block_verbatim',(p/'PROTOCOL.md').read_text().split('### A. Scope')[1].split('## Implementation notes')[0].strip() in Path('work/agents/CODEX_R273_S147_REJECTION.md').read_text())
PY
~~~

Complete output (exit code 0):

~~~text
perm_latent AST identical to S144: True
sample_none AST identical to S144: True
sample_w2cr AST identical to S144: True
_cond AST identical to S144: True
load_rgb AST identical to S144: True
load_pose AST identical to S144: True
model_grid_K AST identical to S144: True
dev_plan_equal True unique_context_groups 32
common_helper_identical True
metric_function_block_verbatim True
current_archived_alpha_AC 0.6
binding_R273_block_verbatim True
~~~

### A4. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from pathlib import Path
import ast,math,warnings,numpy as np
src=Path('work/S147_anchor_a/prep_dev_s147.py').read_text().splitlines()
block='\n'.join(line[4:] for line in src[40:46])
for name,r in [('missing',None),('empty_kps',{'kps':[]}),('missing_focals',{'kps':[{'median_reproj_px':1.,'sigma':1.}]}),('negative_focal',{'kps':[{'median_reproj_px':1.,'sigma':1.,'focals':[-1.]}]}),('zero_focal',{'kps':[{'median_reproj_px':1.,'sigma':1.,'focals':[0.]}]})]:
 ns={'c':{'ctx_key':'x','scene_dir':'s'},'DS':Path('.'),'logs':{} if r is None else {'x':r},'fin':lambda x:isinstance(x,(int,float)) and math.isfinite(x)}
 exec(block,ns); print(name,'geometry_valid=',not ns['why'],'reasons=',ns['why'])
src=ast.parse(Path('work/S147_anchor_a/score_s144_functions.py').read_text())
fn=next(n for n in src.body if isinstance(n,ast.FunctionDef) and n.name=='pred_u8')
ns={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-pred-u8>','exec'),ns)
with warnings.catch_warnings(record=True) as w:
 warnings.simplefilter('always'); out=ns['pred_u8'](np.full((3,2,2),np.nan))
print('nan_prediction_after_conversion','finite=',bool(np.isfinite(out).all()),'unique=',np.unique(out).tolist(),'warnings=',[str(x.message) for x in w])
PY
~~~

Complete output (exit code 0):

~~~text
missing geometry_valid= False reasons= ['no receipt']
empty_kps geometry_valid= True reasons= []
missing_focals geometry_valid= True reasons= []
negative_focal geometry_valid= True reasons= []
zero_focal geometry_valid= True reasons= []
nan_prediction_after_conversion finite= True unique= [0] warnings= ['invalid value encountered in cast']
~~~

### A5. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from pathlib import Path
import numpy as np,json
lines=Path('work/S147_anchor_a/train_s147.py').read_text().splitlines()
init='\n'.join(lines[152:154]); advance='\n'.join(x[4:] for x in lines[156:158])
def tail(ids,step,total):
 ns={'np':np,'train':ids,'step':step};exec(init,ns);out=[]
 for i in range(step,total):
  ns['step']=i;exec(advance,ns);out.append(ns['c'])
 return out
cases=0
for n in (5,2000):
 ids=list(range(n));full=tail(ids,0,5*n)
 for s in (0,1,n-1,n,n+1,2*n-1,2*n,5*n-1):
  assert tail(ids,s,5*n)==full[s:];cases+=1
print('actual_NumPy_permutation_reconstruction_cases_PASS',cases)
p=Path('work/S147_anchor_a');cs=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())['clips'];ids=[c['id'] for c in cs if c['split']=='train'];bad=set(json.loads((p/'INVALID_GEOMETRY.json').read_text())['invalid_clip_ids']);order=tail(ids,0,10000)
print('schedule_attempts',len(order),'invalid_attempts',sum(x in bad for x in order),'valid_updates',sum(x not in bad for x in order))
import torch
x=torch.nn.Parameter(torch.ones(()));opt=torch.optim.AdamW([x],lr=1e-4,weight_decay=0.0);sched=torch.optim.lr_scheduler.LambdaLR(opt,lambda s:min(1.,(s+1)/100));used=[]
for i in range(101):
 used.append(opt.param_groups[0]['lr']);opt.zero_grad();x.grad=torch.ones_like(x);opt.step();sched.step()
print('LR_used_updates_1_99_100_101',[used[k-1] for k in (1,99,100,101)])
PY
~~~

Complete output (exit code 0):

~~~text
actual_NumPy_permutation_reconstruction_cases_PASS 16
schedule_attempts 10000 invalid_attempts 230 valid_updates 9770
LR_used_updates_1_99_100_101 [1.0000000000000002e-06, 9.900000000000001e-05, 0.0001, 0.0001]
~~~

### A6. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
from pathlib import Path
import ast,torch
src=ast.parse(Path('work/S147_anchor_a/analyze_s147.py').read_text()); block=[n for n in src.body if 69<=n.lineno<=78]
def run(mean=.2,ssim=-.01,seq=(.2,.2),override=None):
 practical=['A_none','A_cont','COPY','B2','V','BL_A0','BL_AC']; rivals=set(practical+['F_null','F_geo_proto','F_geo_perm'])
 P={f'F_geo - {x}':{'mean':mean,'seq_means':dict(zip(('a','b'),seq))} for x in rivals}
 Q={f'F_geo - {x}':{'mean':ssim} for x in rivals}
 if override:
  rival,field,value=override
  if field=='ssim':Q[f'F_geo - {rival}']['mean']=value
  else:P[f'F_geo - {rival}'][field]=value
 ns={'res':{'psnr_db':P,'ssim':Q},'PRACTICAL':practical,'THR':.2,'TOL':-.01}
 exec(compile(ast.Module(body=block,type_ignores=[]),'<actual-gates>','exec'),ns);g=ns['res']['GATE']
 return tuple(g[x] for x in ('PRIMARY_SCREEN_PASS','USEFUL_CONTENT_SCREEN_PASS','PRACTICAL_PASS','GO'))
cases=[('at_boundaries',{},(True,True,True,True)),('below_psnr',{'mean':.199},(False,False,False,False)),('below_ssim',{'ssim':-.0101},(False,False,False,False)),('primary_zero_sequence',{'override':('F_null','seq_means',{'a':0.,'b':.4})},(False,False,True,False)),('prototype_zero_sequence',{'override':('F_geo_proto','seq_means',{'a':0.,'b':.4})},(True,False,True,False)),('permutation_zero_sequence',{'override':('F_geo_perm','seq_means',{'a':0.,'b':.4})},(True,False,True,False)),('practical_zero_sequence',{'override':('COPY','seq_means',{'a':0.,'b':.4})},(True,True,True,True)),('practical_negative_sequence',{'override':('COPY','seq_means',{'a':-.001,'b':.401})},(True,True,False,False)),('permutation_no_ssim_gate',{'override':('F_geo_perm','ssim',-.1)},(True,True,True,True))]
for label,kw,want in cases:
 got=run(**kw);assert got==want,(label,got,want);print(label,got)
class M(torch.nn.Module):
 def __init__(self):
  super().__init__();self.base=torch.nn.Linear(1,1);self.warp=torch.nn.Linear(1,1)
m=M();before=m.base.weight.detach().clone();r=m.load_state_dict({'base.weight':torch.full_like(m.base.weight,9.)},strict=False)
print('strict_false_matching_base_key','unexpected_keys=',r.unexpected_keys,'base_changed=',not torch.equal(before,m.base.weight),'missing_branch_keys=',[k for k in r.missing_keys if k.startswith('warp.')])
PY
~~~

Complete output (exit code 0):

~~~text
at_boundaries (True, True, True, True)
below_psnr (False, False, False, False)
below_ssim (False, False, False, False)
primary_zero_sequence (False, False, True, False)
prototype_zero_sequence (True, False, True, False)
permutation_zero_sequence (True, False, True, False)
practical_zero_sequence (True, True, True, True)
practical_negative_sequence (True, True, False, False)
permutation_no_ssim_gate (True, True, True, True)
strict_false_matching_base_key unexpected_keys= [] base_changed= True missing_branch_keys= ['warp.weight', 'warp.bias']
~~~

### A7. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import json,math,collections
r={}
for p in sorted(Path('work/S141_finetune/results/tacc/logs').glob('WARP_LOG_*.jsonl')):
 for line in p.read_text().splitlines():
  if line.strip(): x=json.loads(line);r[x['id']]=x
bad=sorted(k for k,x in r.items() if not all(isinstance(q.get('median_reproj_px'),(int,float)) and math.isfinite(q['median_reproj_px']) for q in x['kps']))
p=Path('work/S147_anchor_a');inv=json.loads((p/'INVALID_GEOMETRY.json').read_text())
print('training_receipts_unique',len(r),'invalid_list_matches',bad==inv['invalid_clip_ids'])
print('retained_receipt_empty_kps_or_bad_positive_fields',[k for k,x in r.items() if k not in bad and (not x['kps'] or any(not (math.isfinite(q['sigma']) and q['sigma']>0 and q.get('focals') and all(math.isfinite(v) and v>0 for v in q['focals'])) for q in x['kps']))])
dev=json.loads((p/'plan_dev_s147.json').read_text())['contexts']
print('dev_ids',dev[0]['ctx_key'],dev[-1]['ctx_key'],'sequences',dict(collections.Counter(x['seq'] for x in dev)),'categories',dict(collections.Counter(x['kind'] for x in dev)))
print('replay_equals_first_dev',json.loads((p/'plan_replay_s147.json').read_text())['contexts']==dev[:1])
print('chess_plan_equals_S145',json.loads((p/'plan_chess_s147.json').read_text())['contexts']==json.loads(Path('work/S145_B_diagnosis/plan_s145.json').read_text())['contexts'])
PY
~~~

Complete output (exit code 0):

~~~text
training_receipts_unique 2032 invalid_list_matches True
retained_receipt_empty_kps_or_bad_positive_fields []
dev_ids c02000 c02031 sequences {'seq-10': 16, 'seq-14': 16} categories {'memory': 23, 'static': 9}
replay_equals_first_dev True
chess_plan_equals_S145 True
~~~

### A8. CPU command

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import hashlib,subprocess
for f in sorted(Path('work/S147_anchor_a').iterdir()):
 if f.is_file(): print('SHA256',f,hashlib.sha256(f.read_bytes()).hexdigest())
p=Path('work/agents/CODEX_R274_S147_CODE_REVIEW.md')
print('OUTPUT_ALREADY_EXISTS',p.exists())
print('STATUS',repr(subprocess.check_output(['git','status','--short'],text=True)))
PY
~~~

Complete output (exit code 0):

~~~text
SHA256 work/S147_anchor_a/INVALID_GEOMETRY.json bcaf322bed389679b674b503388eb5a756b890b07e28f5f61723fdb7199aa456
SHA256 work/S147_anchor_a/PROTOCOL.md f3489a9ce9be90958b96dfbaf1e2573db3b02598c4e4e53f54d697ca3277939b
SHA256 work/S147_anchor_a/PROTOCOL_DRAFT.md 503cfb82d4777a80e07b1c0d3f136eee455f180550f8c669773b6943382d39f3
SHA256 work/S147_anchor_a/analyze_s147.py b83ff31e217dd8d416d8a1061b86886bf42f8ea06f0f124f0b11224d6305fd65
SHA256 work/S147_anchor_a/eng_s147.py 1015ce8351821a7286bfeb276d2ba150a6f4fcfdd37035c5100854d36d3ca306
SHA256 work/S147_anchor_a/gen_s147.py 13fbc594108ca1a28811f639eb7a502eb2c67bbc9d0b1b02c6630c598cb94312
SHA256 work/S147_anchor_a/make_inputs_s147.py 02379ec114a1aaae69ba1be9b76d0ea4cc1decfee1f4ee14c687b8bfc9627c75
SHA256 work/S147_anchor_a/plan_chess_s147.json fbae82c640e29512b2aabe76a51957f464ee7a99bd7b8fa27f7471129f98e89b
SHA256 work/S147_anchor_a/plan_dev_s147.json 76156c2523bea8ad9a9098a1edbfede4d2218f2a0008ad96c23d4db5a32074e3
SHA256 work/S147_anchor_a/plan_replay_s147.json b4dd75db321a57de6f70de5e0b0c4e64893ebdc0ec2281be6bcfa9079bed8fa6
SHA256 work/S147_anchor_a/plan_score_chess_s147.json 0753f9aa743fc307e5af5f07223790642d6594d353f45a3e2966d22e22517a57
SHA256 work/S147_anchor_a/prep_dev_s147.py 097eab5c9657732d7b667b9833cef2f6b984dc782f93d31e3356b322119c48ac
SHA256 work/S147_anchor_a/s141_common.py 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc
SHA256 work/S147_anchor_a/s147_chain.sh 57dd31faac9abbd9e43b444044acfb8bb3e57252a409ca5235af84807f3d6e21
SHA256 work/S147_anchor_a/score_s144_functions.py 037fdd21569cbfcdfb690ed14361c6c5a5cc3d72946df494697663d2fc373cf1
SHA256 work/S147_anchor_a/score_s147.py 63ae5173d9425a1556086d40c97f3202b122005cdac8a0b310c33de26ac8511d
SHA256 work/S147_anchor_a/train_s147.py 87898a79fa82553ff1dea89f968914deed8a3622a8a2171a97ed5d66ecce6947
OUTPUT_ALREADY_EXISTS False
STATUS '?? work/agents/prompts/R274_FULL.md\n'
~~~

The final pre-write snapshot above matches the initial S147 source hashes. No source-file drift was observed during this review.

