**R266 — REJECT S146 Amendment 2 as implemented; do not accept step A under its current gates.**

Local Mac checkout; review of the brief dated 2026-10-11. `new_method_validated=false`; `novelty_authorization=NONE`. This is a source-code and synthetic CPU rejection, not a measurement of fresh-room performance. Only this report is written.

The proposed finite-only mean has a real selection bias: it can improve its objective by making a difficult view invalid. A fixed support set repairs that particular defect. It does **not** make excluded views safe to use as geometry. The existing downstream depth conversion and delayed gates make that distinction consequential.

In the actual-residual synthetic check, the original and fixed-support objectives select scale **1**, while current KPS-R selects **3** after dropping a view; crossing the positive-point threshold changes another objective from **314.198798** to **8.789636**. These are **MEASURED, synthetic CPU** values from [Appendix A](#appendix-a), not dataset results.

**Findings**

For compact citations below, `K` = `work/S146_fresh12/kps.py`; `O` = `data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`; `P` = `data/S134_tacc/vmem_src/modeling/pipeline.py`. Each alias denotes that exact file, not another source copy. Source hashes and checkout identity are in [Appendix E](#appendix-e).

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| A scale can win by deleting a difficult view from the mean. | **BLOCKER** | `K:39-44` changes both support and denominator with scale. `K:22-24` returns infinity below the positive-point threshold **before** `K:31-33` applies its penalty. [Appendix A](#appendix-a) reproduces both whole-view disappearance and threshold crossing with the actual free-focal residual. | Freeze the union of views valid at **any** declared grid point; require every member of that fixed set to remain valid at a candidate. Definition below. |
| Refinement can discard a valid grid solution and return infinity. This predates Amendment 2. | **BLOCKER** | `K:45-57` overwrites the grid incumbent without comparing validity or loss; original `work/S139_crossseq_revisit/kps.py:42-54` does the same. An actual geometric fixture in [Appendix A](#appendix-a) has a finite grid minimum but invalid returned refinement. | Keep the finite grid incumbent. Optional refinement may replace it only with a better finite evaluated candidate. Explicitly fail if the grid has no valid candidate. |
| “Excluded from scale fitting” does not mean “excluded from the output geometry.” | **BLOCKER** | `K:105-120` transforms **every** dense pointmap, initializes its depth, and merely skips a non-finite focal. `O:235-248` converts negative/zero/NaN/negative-infinite raw depth to a positive value after log sanitization and exponentiation; [Appendix B](#appendix-b) verifies this. | Preserve raw depth validity before the setter; validate and propagate it to consumers. Never count a sanitized positive value as measured valid geometry. Fail the required-view gate when usable geometry is absent. |
| Missing focal does not get repaired by rigid registration. | **MAJOR** | `K:76,109-120`: every star edge registers the root's `pred_i` against root `world[i]`; the non-root focal may remain unset. `O:35-38,166-176` leaves an initializer corresponding to `max(H,W)`; `O:251-261` constructs pointmaps using the current focal. Registration itself estimates a similarity scale, `data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py:264-271`. | Require explicit focal provenance for every VMem-consumed view. Default/unset is not a successful estimate. A calibrated fallback needs its own prospective specification; do not silently introduce it here. |
| Gates are incomplete, inconsistent, and too late. | **BLOCKER** | `K:102-124` mutates initialization and logs `OK` even without a finite optimum. `work/S146_fresh12/run_retrieval_s139.py:106-113,128-133` constructs memory and marks the record `OK` without validating each KPS call. `build_pool_s146.py:127-128` accepts an empty log via `all(...)`; `warps_s146.py:64` omits positive-scale and focal/support checks. Rule 5's stronger check at `build_pool_s146.py:96-100` still consumes all depth maps without raw-validity checks. All three short filenames in this row are under `work/S146_fresh12/`. | One shared validation contract, enforced before geometry is committed/used and checked again in receipts. Require exact call count/order, non-root support, root validity separately, positive scale, finite objective, and consumer-specific usable geometry. |
| Growing memory preserves earlier geometry; a later accepted scale cannot repair it. | **MAJOR interaction** | `P:980-997` passes cached depth and appends focal estimates. `data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py:186-193` presets old depths before KPS. `O:218-224,239-242` freezes them; `P:1025-1049,1083` retains existing surfels. Retrieval averages the accumulated focal list at `P:637-645`. | Gate each construction before retention. Record creation stage, raw validity and effective focal provenance. Compare implied **metric depths on shared frames**, not raw sigmas alone, across calls. Preserve upstream accumulation for comparability; rebuilding old memory is a separate amendment. |
| Existing warp files and unversioned convention receipts can bypass the new definition. | **MAJOR** | `work/S146_fresh12/warps_s146.py:53-55` skips by output existence alone. `convention_check_s146.py:15-17` and `convention_check2_s146.py:13-15` import the modified KPS; `s146_cpu_prep.sh:8-9` caches the first check but reruns the second. All short filenames here are under `work/S146_fresh12/`. | Use a new immutable geometry-version directory, matching source/protocol/input hashes and accepted receipts. Pin the detector used for frozen conventions, or explicitly amend and recompute both checks consistently. This is a code risk, not a claim that remote caches are contaminated. |
| Failed warp workers can be followed by apparent completion. | **MAJOR** | Bare `wait` after background pipelines at `work/S146_fresh12/s146_cpu_prep.sh:25-26` and `work/S146_fresh12/s146_chain.sh:19-20` loses child failure status. [Appendix C](#appendix-c) demonstrates the shell behavior. | Capture every worker PID, wait for each explicitly and propagate failure. Require all expected successful package receipts before completion/sealing. |
| Finite successful calls do not prove historical retrieval equivalence or a well-identified scale. | **MAJOR claim correction** | `work/S146_fresh12/PROTOCOL.md:54-59` infers exact chess retrieval equivalence from successful calls. Equality of the objectives/search requires validity at every evaluated candidate, not just the old winner (`K:39-57` versus original `work/S139_crossseq_revisit/kps.py:39-54`). A flat objective still passes in [Appendix A](#appendix-a). | Restrict equivalence to checked inputs; archive curve/scale/output comparisons for any exact claim. Majority is an availability gate, not a robustness or accuracy guarantee. Replace “no scale makes that convention consistent” (`PROTOCOL.md:43-44`) with “no accepted finite solution was obtained by the declared search.” |

**Exact recommended KPS-R definition (ANALYTICAL proposal)**

Use a new explicit version, for example `KPS-R-fixed-support-v1`. This is a numerical repair, not a new-method or novelty judgment.

1. Keep the same deterministic per-view correspondence selection and subsampling for the whole call (`K:88-101`). Let \(N\) be the original number of non-root views. Require \(N\ge1\); require finite input coordinates/transforms/intrinsics and a nonempty, strictly increasing, finite positive scale grid \(G\). Malformed numeric input is a failure, not a reason to silently shrink the denominator. A finite sample with fewer than the existing minimum number of points is a recorded support failure.
2. For every original view \(j\) and every grid scale \(g\), evaluate the existing per-view residual/focal. Explicitly classify a pair as valid only when
   \[
   b_j(g)=\mathrm{isfinite}(r_j(g))\ \land\ \mathrm{isfinite}(f_j(g))\ \land\ f_j(g)>0.
   \]
   The existing residual uses positive-camera-depth samples, fitted focal, median pixel residual and the additive bad-depth fraction penalty (`K:18-33`). Add explicit finite checks to the implementation; checking `f<=0` alone does not reject NaN.
3. Freeze the set **after the complete first grid pass and before selecting a scale**:
   \[
   E=\{j:\exists g\in G,\ b_j(g)\},\qquad X=\{1,\ldots,N\}\setminus E.
   \]
   Require \(|E|\ge\lceil N/2\rceil\). The root is not in this count. \(X\) means “unsupported on the declared finite grid,” not “invalid at every possible continuous scale.”
4. For **every** grid and refinement candidate, use exactly
   \[
   J(\sigma)=
   \begin{cases}
   \frac{1}{|E|}\sum_{j\in E}r_j(\sigma),&
       \text{if }b_j(\sigma)\text{ holds for every }j\in E,\\
   +\infty,&\text{otherwise}.
   \end{cases}
   \]
   Neither membership nor denominator may change during optimization. Require at least one finite grid \(J(g)\). If none exists, return a typed failure before pose/depth setters; do not relax to another subset, silently return the first scale, or invoke the original MST fallback.
5. Set the incumbent to the first grid minimizer in ascending-grid order. With refinement disabled, return it. With refinement enabled, retain the existing neighboring-grid bracket and existing deterministic log-space probe schedule (`K:49-56`) **only as a candidate generator**: compare every finite probe, and the final midpoint, against the saved incumbent under the same \(E\); update only for a strictly smaller objective, retaining the incumbent on ties. The returned objective must therefore be finite and no worse than the finite grid minimum. The majority count is never recalculated to drop a view.
6. Log original view IDs, sampled point counts, \(N,E,X\), grid-validity counts and failure reasons per view, grid/hash, grid minimum, chosen scale/objective, final per-view residual/focal/positive-point counts, root focal provenance, and whether refinement improved the incumbent. Keep scale-fit validity separate from dense-geometry validity. Rename or explain `median_reproj_px`: it is a **mean of per-view penalized medians**, not one overall median (`K:30-44,123`).
7. Do not certify scale identification from a finite value. At minimum flag a numerically flat finite grid curve, an endpoint minimum, and insufficient translational sensitivity. Treat a completely flat/unsupported scale as unusable for an “identified metric scale” claim; use a predeclared calibration only if the experiment is explicitly amended. Record the objective profile rather than inventing an absolute quality threshold from fresh outputs.

Freezing the set “at the first pass” means the **union over the entire declared grid**, not the set finite at its first/smallest scale or at an adaptively selected winner. An intersection over all grid scales discards informative views merely because distant scales are impossible. The union rule deliberately rejects mutually incompatible views if no jointly valid grid candidate exists; [Appendix A](#appendix-a) exercises that case.

This removes the demonstrated **whole-view deletion reward**. It does not make the objective smooth or globally unimodal. The positive-depth indicator still changes with scale, and the additive penalty can trade off against the median over surviving points (`K:22-33`). The source comment that discarded points cannot make a scale win is stronger than the actual formula. Safeguarded refinement is a bounded numerical heuristic, not a global optimizer.

**Downstream disposition and required acceptance gates**

An excluded view can have useful dense depth: fitting uses a confidence-selected subset, whereas the depth setter receives the full pointmap (`K:88-101,105-116`). Conversely, an excluded view with bad cheirality, invalid coordinates, or an unset focal is not rescued by a finite scale fitted to other views.

The raw depth for view \(i\) is
\[
d_i(u)=\left[T_i^{-1}T_0\,(P_i(u)/\sigma,1)^\top\right]_z.
\]
This follows directly from `K:104-116`; focal is not in this expression once sigma is fixed. Preserve \(\mathrm{isfinite}(d_i)\land d_i>10^{-6}\) and point-coordinate validity **before** `_set_depthmap`. Keep invalid pixels masked through resize and depth lookup; interpolation and normal estimation must not allow invalid placeholders to contaminate accepted samples.

- **VMem:** final pointmaps are reconstructed from depth and the current fitted/default focal (`O:251-261`), and surfel filtering only uses returned depth quantile and confidence (`P:869-896`). Require an explicitly sourced finite positive focal for every consumed view, valid point/normal/radius values, and actual valid support for each required bank frame. An unset/default focal fails this contract unless a separately frozen fallback is introduced.
- **Rule 5 and package warps:** they backproject returned z using the staged dataset \(K\), **not** CUT3R's fitted focal (`work/S146_fresh12/build_pool_s146.py:69,73-80,100`; `work/S146_fresh12/warps_s146.py:32-40,52,65-68`). Thus skipping a focal does not by itself invalidate these consumers if scale, raw depth and dataset calibration are usable. Their shared immediate defect is loss of raw depth validity: both use `depth>0`. Apply the preserved mask; report usable source support and target coverage. Do not substitute nearest-fill pixels for geometric support.
- **Cleaning is not a substitute:** `data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py:349-359,581-620` adjusts confidence, not raw depth validity. It may suppress some bad surfels; it neither guarantees this nor protects coverage/warps, which ignore that confidence. [Appendix B](#appendix-b) tests the consumer predicates, not a claim that every artificial point survives real reconstruction.

For the proposed full-bank assay, inability to validate a required view means **INVALID_ASSAY/INELIGIBLE**, with no substitution. Consequently, the fixed-support numerical repair may still leave the triggering window unusable for VMem retrieval. That is the correct negative outcome unless an explicit geometry fallback is separately specified and validated. Do not silently remove an excluded view from the bank or describe a default focal as measured.

The schedule itself is appropriate for coverage: the runner initializes the first group and changes `target_num_frames` to each incoming chunk (`work/S146_fresh12/run_retrieval_s139.py:105-113`); the pipeline adds the corresponding final chunk (`P:1027-1031`). For the protocol schedule (`work/S146_fresh12/PROTOCOL.md:25`), the expected non-root log sizes are **[4,19,31]**, and accumulated focal entries total **57** (**DERIVED** from those code paths and `P:996`). Full ID coverage only proves association with at least one surfel, not accurate surfaces (`run_retrieval_s139.py:129`; `build_pool_s146.py:126`, both under `work/S146_fresh12/`).

Require exactly those ordered construction records, one rule-5 record and one record per package, using the same versioned validator. Check both initialization diagnostics and actual post-alignment consumer inputs before persistent memory or geometry output is committed. Preset depths remain frozen (`O:218-224,239-242`), and the depth getter detaches the original parameters (`O:245-246,303-317`; [Appendix B](#appendix-b)); a later alignment run is not evidence that early invalid depth has been repaired. Independent CUT3R calls may change their arbitrary point scale, so changes in sigma alone do not prove metric inconsistency. Compare candidate metric depths on common valid pixels with cached metric depths and a tolerance frozen on exposed controls.

The original binding review already required usable depth and disclosure of repeated focal estimates (`work/agents/CODEX_R265_S146_DRAFT_REJECTION.md:94`). Amendment 2's scalar/focal-count gate does not discharge that requirement. Stronger masks or calibrated fallbacks change the actual geometry pipeline; record them prospectively rather than calling them bitwise-equivalent to historical KPS.

**Evidence limits and handoff**

The brief's triggering real-bank failure and the historical success/non-finite counts in `work/S146_fresh12/PROTOCOL.md:51-56` are **UNVERIFIED in this review**; no remote artifacts were accessed. Synthetic evidence proves the failure mechanisms can occur, not their incidence or effect on fresh-room retrieval/generation. No literature novelty claim is made, so no unverified arXiv citations are introduced.

Only `work/agents/CODEX_R266_KPSR_REJECTION.md` is created. The pre-existing untracked `work/agents/prompts/R266_FULL.md` and `R266_PROMPT.md` are left alone. Follow-up: amend the definition and acceptance implementation, then verify the corrected CPU fixtures and any claimed archived-input equivalence before accepting step A. No production correction or experimental run is represented as completed here.

The appendices give exact commands and complete captured outputs for the reported executable checks. Commands use the repository root as working directory. No GPU, model initialization, training, weight/data download, SSH, or cluster submission was used. Tests B and C were executed by read-only review workers; their code findings were independently checked against the cited source. The local project environment was reused; no packages were installed.

<a id="appendix-a"></a>

**Appendix A — deterministic estimator checks**

MEASURED, synthetic CPU. The fixed-support helper is a grid-only reference used to test the definition; it is not a patched production initializer. The final narrow-support fixture calls the actual residual, with no monkeypatch. All reported final cases pass. An initial mistaken test expectation and the diagnostic rerun are preserved in Appendix D.

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
import importlib.util
import sys
import numpy as np
import torch

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
new = load('new', 'work/S146_fresh12/kps.py')
old = load('old', 'work/S139_crossseq_revisit/kps.py')
print('environment:', sys.version.split()[0], 'numpy', np.__version__, 'torch', torch.__version__, 'device=cpu')
xy = np.stack(np.meshgrid(np.linspace(-1, 1, 10), np.linspace(-1, 1, 10)), -1).reshape(-1, 2)
pix = 10 * xy
good = dict(P=np.c_[pix[:, 0] / 100 - 1, pix[:, 1] / 100, np.ones(100)],
            pix=pix, R=np.eye(3), t=np.array([1., 0, 0]), pp=np.zeros(2))
grid = np.array([0.5, 1., 1.5, 1.999, 2., 2.5, 3.])
def residual(v, s):
    return new._proj_residual(v['P'], v['pix'], v['R'], v['t'], s, v['pp'], v.get('f'))
def fixed_grid(vs, g):
    rr = np.array([[residual(v, s)[0] for v in vs] for s in g])
    eligible = np.isfinite(rr).any(axis=0)
    if eligible.sum() < max(1, int(np.ceil(len(vs) / 2))):
        return None, eligible, np.full(len(g), np.inf)
    valid = np.isfinite(rr[:, eligible]).all(axis=1)
    objective = np.full(len(g), np.inf)
    objective[valid] = rr[valid][:, eligible].mean(axis=1)
    if not np.isfinite(objective).any():
        return None, eligible, objective
    return float(g[np.argmin(objective)]), eligible, objective

a = new.estimate_sigma([good, good], grid, refine=True)
b = old.estimate_sigma([good, good], grid, refine=True)
assert a[0:3] == b[0:3] and np.array_equal(a[3], b[3])
print('all_finite_parity:', True, 'sigma=%.9f' % a[0], 'objective=%.9f' % a[2])

short = dict(good, P=good['P'][:49], pix=good['pix'][:49])
a = new.estimate_sigma([good, short], grid, refine=False)
b = old.estimate_sigma([good, short], grid, refine=False)
c, e, _ = fixed_grid([good, short], grid)
assert a[0] == c == 1.0 and not np.isfinite(b[2]) and e.tolist() == [True, False]
print('permanent_49_points: original_objective=inf dynamic_sigma=%.3f fixed_sigma=%.3f eligible=%s' % (a[0], c, e.tolist()))

bad = dict(P=np.c_[xy, np.full(100, 2.)], pix=100 * np.c_[xy[:, 0] - xy[:, 1], xy[:, 0] + xy[:, 1]],
           R=np.eye(3), t=np.array([0., 0., -1.]), pp=np.zeros(2))
a = new.estimate_sigma([good, bad], grid, refine=False)
b = old.estimate_sigma([good, bad], grid, refine=False)
c, e, objective = fixed_grid([good, bad], grid)
assert a[0] == 3. and b[0] == c == 1.
for s in [1., 1.999, 2.]:
    rs = np.array([residual(v, s)[0] for v in [good, bad]])
    dynamic = rs[np.isfinite(rs)].mean()
    print('dropout_at_sigma=%.3f residuals=%s dynamic_objective=%.6f' % (s, np.array2string(rs, precision=6), dynamic))
print('dropout_selection: original=%.3f dynamic=%.3f fixed=%.3f eligible=%s' % (b[0], a[0], c, e.tolist()))

z = np.r_[np.full(49, 3.), 2., np.full(50, 0.1)]
threshold = dict(bad, P=np.c_[xy, z])
rs1 = np.array([residual(v, 1.999)[0] for v in [good, threshold]])
rs2 = np.array([residual(v, 2.)[0] for v in [good, threshold]])
assert np.isfinite(rs1).all() and not np.isfinite(rs2[1])
print('50_to_49_positive: before_objective=%.6f after_objective=%.6f excluded_view_before=%.6f' %
      (rs1.mean(), rs2[0], rs1[1]))

flat = dict(good, t=np.zeros(3))
a = new.estimate_sigma([flat, flat], grid, refine=False)
assert np.isfinite(a[2]) and np.ptp(a[3]) == 0
print('unidentifiable_flat_curve: objective=%.6f span=%.6f accepted_sigma=%.3f' % (a[2], np.ptp(a[3]), a[0]))

a = new.estimate_sigma([short, short], grid, refine=True)
assert np.isfinite(a[0]) and not np.isfinite(a[2])
print('all_invalid: still_returns_finite_sigma=%s objective=inf' % np.isfinite(a[0]))

narrow = dict(P=np.tile([-0.99, 0., 1.01], (100, 1)), pix=np.tile([1., 0.], (100, 1)),
              R=np.eye(3), t=np.array([1., 0., -1.]), pp=np.zeros(2))
a = new.estimate_sigma([narrow], np.array([0.5, 1., 2.]), refine=True)
assert np.min(a[3]) == 0 and not np.isfinite(a[2])
print('actual_narrow_support: grid_best_objective=0 refined_objective=inf refined_sigma=%.9f' % a[0])

left = dict(good, t=np.zeros(3), P=np.c_[xy, np.full(100, 0.9)])
left['t'] = np.array([0., 0., -1.])
left['pix'] = 100 * xy
right = dict(left, P=np.c_[xy, np.full(100, -1.1)], t=np.array([0., 0., 1.]))
c, e, o = fixed_grid([left, right], np.array([0.5, 1., 1.5]))
a = new.estimate_sigma([left, right], np.array([0.5, 1., 1.5]), refine=False)
assert c is None and e.all() and np.isfinite(a[2])
print('disjoint_support: union_eligible=%s fixed_result=FAIL dynamic_result=FINITE' % e.tolist())
print('PASS: 8 deterministic CPU cases using actual KPS residual and estimator code.')
PY
```

Complete captured output (exit status 0):

```text
environment: 3.12.14 numpy 1.26.4 torch 2.7.0 device=cpu
all_finite_parity: True sigma=1.000000001 objective=0.000000138
permanent_49_points: original_objective=inf dynamic_sigma=1.000 fixed_sigma=1.000 eligible=[True, False]
dropout_at_sigma=1.000 residuals=[5.333694e-15 8.461970e+01] dynamic_objective=42.309851
dropout_at_sigma=1.999 residuals=[ 8.789368 84.619701] dynamic_objective=46.704535
dropout_at_sigma=2.000 residuals=[8.789636      inf] dynamic_objective=8.789636
dropout_selection: original=1.000 dynamic=3.000 fixed=1.000 eligible=[True, True]
50_to_49_positive: before_objective=314.198798 after_objective=8.789636 excluded_view_before=619.608229
unidentifiable_flat_curve: objective=8.789636 span=0.000000 accepted_sigma=0.500
all_invalid: still_returns_finite_sigma=True objective=inf
actual_narrow_support: grid_best_objective=0 refined_objective=inf refined_sigma=0.500000002
disjoint_support: union_eligible=[True, True] fixed_result=FAIL dynamic_result=FINITE
PASS: 8 deterministic CPU cases using actual KPS residual and estimator code.
```

<a id="appendix-b"></a>

**Appendix B — actual depth setter/getter and frozen-prefix behavior**

MEASURED, synthetic CPU, executed by the downstream review worker. AST extraction runs the actual source functions without importing a model. The surfel predicate fixture uses an illustrative confidence threshold; its high confidence also exceeds the pinned setting. No full reconstruction or cleaner is simulated.

Exact command:

```bash
.venv-cut3r/bin/python -B - <<'PY'
import ast
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
path = Path('data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py')
tree = ast.parse(path.read_text())
selected = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in {'ParameterStack', '_ravel_hw'}:
        selected.append(node)
    if isinstance(node, ast.ClassDef):
        selected.extend(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in {'_set_depthmap', 'get_depthmaps'})
ns = {'torch': torch, 'nn': torch.nn, 'np': np}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), ns)
raw = torch.tensor([[-2.0, 0.0, float('nan'), -float('inf'), 0.25, 2.0]])
p = torch.nn.Parameter(torch.zeros_like(raw))
s = SimpleNamespace(max_area=6, imshapes=[(1, 6)], im_depthmaps=[p])
ns['_set_depthmap'](s, 0, raw)
out = ns['get_depthmaps'](s)[0]
print('raw_depth:', raw.tolist())
print('stored_log_depth:', p.detach().tolist())
print('returned_depth:', out.detach().tolist())
mask = (out <= torch.quantile(out, 0.999)) & (torch.full_like(out, 10) >= 1.5)
print('surfel_depth_conf_mask:', mask.tolist())
print('warp_positive_depth_mask:', (out > 0).tolist())
out.sum().backward()
print('original_depth_parameter_grad:', p.grad)
p.requires_grad_(False)
ns['_set_depthmap'](s, 0, torch.full_like(raw, 9.0))
print('preset_old_depth_after_new_init:', ns['get_depthmaps'](s)[0].detach().tolist())
PY
```

Complete captured output (exit status 0):

```text
raw_depth: [[-2.0, 0.0, nan, -inf, 0.25, 2.0]]
stored_log_depth: [[0.0, 0.0, 0.0, 0.0, -1.3862943649291992, 0.6931471824645996]]
returned_depth: [[1.0, 1.0, 1.0, 1.0, 0.25, 2.0]]
surfel_depth_conf_mask: [[True, True, True, True, True, False]]
warp_positive_depth_mask: [[True, True, True, True, True, True]]
original_depth_parameter_grad: None
preset_old_depth_after_new_init: [[1.0, 1.0, 1.0, 1.0, 0.25, 2.0]]
```

<a id="appendix-c"></a>

**Appendix C — background failure propagation**

MEASURED, synthetic shell check, executed by the gate review worker. This isolates bare-wait semantics; it does not execute either project pipeline.

Exact command:

```bash
bash -c 'set -euo pipefail; (exit 7) & (exit 9) & wait; printf "continued_after_failed_shards\n"'
```

Complete captured output (exit status 0):

```text
continued_after_failed_shards
```

<a id="appendix-d"></a>

**Appendix D — retained test-development failure and diagnostic rerun**

The first fixture incorrectly asserted that dynamic KPS-R must choose exactly scale 2. The actual grid winner is 3: the important failure is still view deletion, but the test expectation was too specific. The production source was not changed. The diagnostic command replaces only that assertion with a print; the final Appendix A command correctly asserts the observed deterministic winner and replaces the refinement stub with an actual geometric fixture.

<details>
<summary>Initial exact command and full failure output</summary>

<a id="appendix-d-initial"></a>

**Initial numerical command**

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
import importlib.util
import sys
import numpy as np
import torch

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
new = load('new', 'work/S146_fresh12/kps.py')
old = load('old', 'work/S139_crossseq_revisit/kps.py')
print('environment:', sys.version.split()[0], 'numpy', np.__version__, 'torch', torch.__version__, 'device=cpu')
xy = np.stack(np.meshgrid(np.linspace(-1, 1, 10), np.linspace(-1, 1, 10)), -1).reshape(-1, 2)
pix = 10 * xy
good = dict(P=np.c_[pix[:, 0] / 100 - 1, pix[:, 1] / 100, np.ones(100)],
            pix=pix, R=np.eye(3), t=np.array([1., 0, 0]), pp=np.zeros(2))
grid = np.array([0.5, 1., 1.5, 1.999, 2., 2.5, 3.])
def residual(v, s):
    return new._proj_residual(v['P'], v['pix'], v['R'], v['t'], s, v['pp'], v.get('f'))
def fixed_grid(vs, g):
    rr = np.array([[residual(v, s)[0] for v in vs] for s in g])
    eligible = np.isfinite(rr).any(axis=0)
    if eligible.sum() < max(1, int(np.ceil(len(vs) / 2))):
        return None, eligible, np.full(len(g), np.inf)
    valid = np.isfinite(rr[:, eligible]).all(axis=1)
    objective = np.full(len(g), np.inf)
    objective[valid] = rr[valid][:, eligible].mean(axis=1)
    if not np.isfinite(objective).any():
        return None, eligible, objective
    return float(g[np.argmin(objective)]), eligible, objective

a = new.estimate_sigma([good, good], grid, refine=True)
b = old.estimate_sigma([good, good], grid, refine=True)
assert a[0:3] == b[0:3] and np.array_equal(a[3], b[3])
print('all_finite_parity:', True, 'sigma=%.9f' % a[0], 'objective=%.9f' % a[2])

short = dict(good, P=good['P'][:49], pix=good['pix'][:49])
a = new.estimate_sigma([good, short], grid, refine=False)
b = old.estimate_sigma([good, short], grid, refine=False)
c, e, _ = fixed_grid([good, short], grid)
assert a[0] == c == 1.0 and not np.isfinite(b[2]) and e.tolist() == [True, False]
print('permanent_49_points: original_objective=inf dynamic_sigma=%.3f fixed_sigma=%.3f eligible=%s' % (a[0], c, e.tolist()))

bad = dict(P=np.c_[xy, np.full(100, 2.)], pix=100 * np.c_[xy[:, 0] - xy[:, 1], xy[:, 0] + xy[:, 1]],
           R=np.eye(3), t=np.array([0., 0., -1.]), pp=np.zeros(2))
a = new.estimate_sigma([good, bad], grid, refine=False)
b = old.estimate_sigma([good, bad], grid, refine=False)
c, e, objective = fixed_grid([good, bad], grid)
assert a[0] == 2. and b[0] == c == 1.
for s in [1., 1.999, 2.]:
    rs = np.array([residual(v, s)[0] for v in [good, bad]])
    dynamic = rs[np.isfinite(rs)].mean()
    print('dropout_at_sigma=%.3f residuals=%s dynamic_objective=%.6f' % (s, np.array2string(rs, precision=6), dynamic))
print('dropout_selection: original=%.3f dynamic=%.3f fixed=%.3f eligible=%s' % (b[0], a[0], c, e.tolist()))

z = np.r_[np.full(49, 3.), 2., np.full(50, 0.1)]
threshold = dict(bad, P=np.c_[xy, z])
rs1 = np.array([residual(v, 1.999)[0] for v in [good, threshold]])
rs2 = np.array([residual(v, 2.)[0] for v in [good, threshold]])
assert np.isfinite(rs1).all() and not np.isfinite(rs2[1])
print('50_to_49_positive: before_objective=%.6f after_objective=%.6f excluded_view_before=%.6f' %
      (rs1.mean(), rs2[0], rs1[1]))

flat = dict(good, t=np.zeros(3))
a = new.estimate_sigma([flat, flat], grid, refine=False)
assert np.isfinite(a[2]) and np.ptp(a[3]) == 0
print('unidentifiable_flat_curve: objective=%.6f span=%.6f accepted_sigma=%.3f' % (a[2], np.ptp(a[3]), a[0]))

a = new.estimate_sigma([short, short], grid, refine=True)
assert np.isfinite(a[0]) and not np.isfinite(a[2])
print('all_invalid: still_returns_finite_sigma=%s objective=inf' % np.isfinite(a[0]))

real = new._proj_residual
def narrow(P, pix, R, t, sigma, pp, f_fixed=None):
    return (0., 100.) if sigma == 1. else (np.inf, np.nan)
new._proj_residual = narrow
a = new.estimate_sigma([good], np.array([0.5, 1., 2.]), refine=True)
new._proj_residual = real
assert np.min(a[3]) == 0 and not np.isfinite(a[2])
print('controlled_narrow_support: grid_best_objective=0 refined_objective=inf refined_sigma=%.9f' % a[0])

left = dict(good, t=np.zeros(3), P=np.c_[xy, np.full(100, 0.9)])
left['t'] = np.array([0., 0., -1.])
left['pix'] = 100 * xy
right = dict(left, P=np.c_[xy, np.full(100, -1.1)], t=np.array([0., 0., 1.]))
c, e, o = fixed_grid([left, right], np.array([0.5, 1., 1.5]))
a = new.estimate_sigma([left, right], np.array([0.5, 1., 1.5]), refine=False)
assert c is None and e.all() and np.isfinite(a[2])
print('disjoint_support: union_eligible=%s fixed_result=FAIL dynamic_result=FINITE' % e.tolist())
print('PASS: 8 deterministic CPU cases; controlled_narrow_support stubs only the residual to isolate refinement.')
PY
```

Complete captured output (exit status 1):

```text
environment: 3.12.14 numpy 1.26.4 torch 2.7.0 device=cpu
all_finite_parity: True sigma=1.000000001 objective=0.000000138
permanent_49_points: original_objective=inf dynamic_sigma=1.000 fixed_sigma=1.000 eligible=[True, False]
Traceback (most recent call last):
  File "<stdin>", line 50, in <module>
AssertionError
```

</details>

<details>
<summary>Diagnostic exact command and full output</summary>

<a id="appendix-d-diagnostic"></a>

**Diagnostic numerical command**

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
import importlib.util
import sys
import numpy as np
import torch

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
new = load('new', 'work/S146_fresh12/kps.py')
old = load('old', 'work/S139_crossseq_revisit/kps.py')
print('environment:', sys.version.split()[0], 'numpy', np.__version__, 'torch', torch.__version__, 'device=cpu')
xy = np.stack(np.meshgrid(np.linspace(-1, 1, 10), np.linspace(-1, 1, 10)), -1).reshape(-1, 2)
pix = 10 * xy
good = dict(P=np.c_[pix[:, 0] / 100 - 1, pix[:, 1] / 100, np.ones(100)],
            pix=pix, R=np.eye(3), t=np.array([1., 0, 0]), pp=np.zeros(2))
grid = np.array([0.5, 1., 1.5, 1.999, 2., 2.5, 3.])
def residual(v, s):
    return new._proj_residual(v['P'], v['pix'], v['R'], v['t'], s, v['pp'], v.get('f'))
def fixed_grid(vs, g):
    rr = np.array([[residual(v, s)[0] for v in vs] for s in g])
    eligible = np.isfinite(rr).any(axis=0)
    if eligible.sum() < max(1, int(np.ceil(len(vs) / 2))):
        return None, eligible, np.full(len(g), np.inf)
    valid = np.isfinite(rr[:, eligible]).all(axis=1)
    objective = np.full(len(g), np.inf)
    objective[valid] = rr[valid][:, eligible].mean(axis=1)
    if not np.isfinite(objective).any():
        return None, eligible, objective
    return float(g[np.argmin(objective)]), eligible, objective

a = new.estimate_sigma([good, good], grid, refine=True)
b = old.estimate_sigma([good, good], grid, refine=True)
assert a[0:3] == b[0:3] and np.array_equal(a[3], b[3])
print('all_finite_parity:', True, 'sigma=%.9f' % a[0], 'objective=%.9f' % a[2])

short = dict(good, P=good['P'][:49], pix=good['pix'][:49])
a = new.estimate_sigma([good, short], grid, refine=False)
b = old.estimate_sigma([good, short], grid, refine=False)
c, e, _ = fixed_grid([good, short], grid)
assert a[0] == c == 1.0 and not np.isfinite(b[2]) and e.tolist() == [True, False]
print('permanent_49_points: original_objective=inf dynamic_sigma=%.3f fixed_sigma=%.3f eligible=%s' % (a[0], c, e.tolist()))

bad = dict(P=np.c_[xy, np.full(100, 2.)], pix=100 * np.c_[xy[:, 0] - xy[:, 1], xy[:, 0] + xy[:, 1]],
           R=np.eye(3), t=np.array([0., 0., -1.]), pp=np.zeros(2))
a = new.estimate_sigma([good, bad], grid, refine=False)
b = old.estimate_sigma([good, bad], grid, refine=False)
c, e, objective = fixed_grid([good, bad], grid)
print('DEBUG dropout:', a[0], b[0], c, objective.tolist())
for s in [1., 1.999, 2.]:
    rs = np.array([residual(v, s)[0] for v in [good, bad]])
    dynamic = rs[np.isfinite(rs)].mean()
    print('dropout_at_sigma=%.3f residuals=%s dynamic_objective=%.6f' % (s, np.array2string(rs, precision=6), dynamic))
print('dropout_selection: original=%.3f dynamic=%.3f fixed=%.3f eligible=%s' % (b[0], a[0], c, e.tolist()))

z = np.r_[np.full(49, 3.), 2., np.full(50, 0.1)]
threshold = dict(bad, P=np.c_[xy, z])
rs1 = np.array([residual(v, 1.999)[0] for v in [good, threshold]])
rs2 = np.array([residual(v, 2.)[0] for v in [good, threshold]])
assert np.isfinite(rs1).all() and not np.isfinite(rs2[1])
print('50_to_49_positive: before_objective=%.6f after_objective=%.6f excluded_view_before=%.6f' %
      (rs1.mean(), rs2[0], rs1[1]))

flat = dict(good, t=np.zeros(3))
a = new.estimate_sigma([flat, flat], grid, refine=False)
assert np.isfinite(a[2]) and np.ptp(a[3]) == 0
print('unidentifiable_flat_curve: objective=%.6f span=%.6f accepted_sigma=%.3f' % (a[2], np.ptp(a[3]), a[0]))

a = new.estimate_sigma([short, short], grid, refine=True)
assert np.isfinite(a[0]) and not np.isfinite(a[2])
print('all_invalid: still_returns_finite_sigma=%s objective=inf' % np.isfinite(a[0]))

real = new._proj_residual
def narrow(P, pix, R, t, sigma, pp, f_fixed=None):
    return (0., 100.) if sigma == 1. else (np.inf, np.nan)
new._proj_residual = narrow
a = new.estimate_sigma([good], np.array([0.5, 1., 2.]), refine=True)
new._proj_residual = real
assert np.min(a[3]) == 0 and not np.isfinite(a[2])
print('controlled_narrow_support: grid_best_objective=0 refined_objective=inf refined_sigma=%.9f' % a[0])

left = dict(good, t=np.zeros(3), P=np.c_[xy, np.full(100, 0.9)])
left['t'] = np.array([0., 0., -1.])
left['pix'] = 100 * xy
right = dict(left, P=np.c_[xy, np.full(100, -1.1)], t=np.array([0., 0., 1.]))
c, e, o = fixed_grid([left, right], np.array([0.5, 1., 1.5]))
a = new.estimate_sigma([left, right], np.array([0.5, 1., 1.5]), refine=False)
assert c is None and e.all() and np.isfinite(a[2])
print('disjoint_support: union_eligible=%s fixed_result=FAIL dynamic_result=FINITE' % e.tolist())
print('PASS: 8 deterministic CPU cases; controlled_narrow_support stubs only the residual to isolate refinement.')
PY
```

Complete captured output (exit status 0):

```text
environment: 3.12.14 numpy 1.26.4 torch 2.7.0 device=cpu
all_finite_parity: True sigma=1.000000001 objective=0.000000138
permanent_49_points: original_objective=inf dynamic_sigma=1.000 fixed_sigma=1.000 eligible=[True, False]
DEBUG dropout: 3.0 1.0 1.0 [46.60053591968644, 42.309850588132825, 46.60053591968645, 46.704534645792705, inf, inf, inf]
dropout_at_sigma=1.000 residuals=[5.333694e-15 8.461970e+01] dynamic_objective=42.309851
dropout_at_sigma=1.999 residuals=[ 8.789368 84.619701] dynamic_objective=46.704535
dropout_at_sigma=2.000 residuals=[8.789636      inf] dynamic_objective=8.789636
dropout_selection: original=1.000 dynamic=3.000 fixed=1.000 eligible=[True, True]
50_to_49_positive: before_objective=314.198798 after_objective=8.789636 excluded_view_before=619.608229
unidentifiable_flat_curve: objective=8.789636 span=0.000000 accepted_sigma=0.500
all_invalid: still_returns_finite_sigma=True objective=inf
controlled_narrow_support: grid_best_objective=0 refined_objective=inf refined_sigma=0.500000002
disjoint_support: union_eligible=[True, True] fixed_result=FAIL dynamic_result=FINITE
PASS: 8 deterministic CPU cases; controlled_narrow_support stubs only the residual to isolate refinement.
```

</details>

<a id="appendix-e"></a>

**Appendix E — checked source snapshot**

MEASURED source hashes and checkout identity. Line citations refer to this local snapshot; remote deployed identity was not checked.

Exact command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
from pathlib import Path
from hashlib import sha256
import subprocess
paths = [
'work/S146_fresh12/PROTOCOL.md',
'work/S146_fresh12/kps.py',
'work/S139_crossseq_revisit/kps.py',
'work/S146_fresh12/run_retrieval_s139.py',
'work/S146_fresh12/build_pool_s146.py',
'work/S146_fresh12/warps_s146.py',
'work/S146_fresh12/s146_cpu_prep.sh',
'work/S146_fresh12/s146_chain.sh',
'data/S134_tacc/vmem_src/modeling/pipeline.py',
'data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py',
'data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py',
'data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py',
'data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py'
]
print('HEAD', subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
for p in paths:
    print(sha256(Path(p).read_bytes()).hexdigest(), p)
PY
```

Complete captured output (exit status 0):

```text
HEAD 7fdd39fe41cae5c95a2a52c7d2d7f3beb07e3e41
65c93df1fcee2841ada3d7c3164d7f5a8fe1ba711c14a7d143416a80cce52e64 work/S146_fresh12/PROTOCOL.md
fc463275ab03a7e33459b2bd96514060622e9be5e632f5b83df1ed194d8fc1d5 work/S146_fresh12/kps.py
71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f work/S139_crossseq_revisit/kps.py
6670478ca26001eb2a011e2f801360893c0d6e2ca67a068b4ba32ab587b039fc work/S146_fresh12/run_retrieval_s139.py
e3c9f9421a9939c6c2898ec0b0129c0003a219d2bef1596f5a692f9d03dfe946 work/S146_fresh12/build_pool_s146.py
2d604ca9ae4627dc7eeeb3f6861b8ae2d3e031699dd626aed7e368a3a18b07dc work/S146_fresh12/warps_s146.py
cc025c5e2d0c7f54eb021f0f41e8405d10a6110c087911f1671e7997713ca9b7 work/S146_fresh12/s146_cpu_prep.sh
5945323bdbecfdc6051782280c6ce4c72d96b9bc496ec9fc43fbefb2e0e68d9d work/S146_fresh12/s146_chain.sh
680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
8a348645cd387147c35635f0a6b432d85bcf844e3839bd5a000d8147a85b17d5 data/S134_tacc/vmem_src/extern/CUT3R/surfel_inference.py
b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21 data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py
f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11 data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py
edd07a0d04e72c5687149f9dd90c36bfebcdac365c424e3ba9161fc73c495134 data/S134_tacc/vmem_src/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py
```

