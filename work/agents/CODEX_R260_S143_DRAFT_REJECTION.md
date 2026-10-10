# R260 — S143 draft rejection

Workspace: local Mac checkout. Review date: 2026-10-10. **Verdict: reject freezing the draft unchanged; retain a corrected exploratory context-ranking audit.** The cross-fitted statistic is defensible, but the claimed oracle interpretation, significance gate, scorer/cache plumbing, geometry contract, and novelty wording require changes.

This review writes only this file. No GPU, model inference, training, weight/dataset download, cluster connection, scheduler submission, external contact, or target-image read was performed. S141 runtime outcomes and remote fidelity artifacts were not inspected. The existing S141 protocol records a fidelity check; that is archived documentation, not a replay performed here (S141/PROTOCOL.md:75–77). No project tests were run because this is a document-only review; the CPU computations and their complete outputs appear below.

Evidence labels: **MEASURED (archived)** = earlier stored scores; **DERIVED** = calculations reproduced below; **ANALYTICAL** = mathematical conclusions or proposed protocol choices; **UNVERIFIED** = missing execution or generalization evidence. The two authorization fields remain **new_method_validated=false; novelty_authorization=NONE**.

Path abbreviations: D = work/S143_context_ranking/PROTOCOL_DRAFT.md; R259 = work/agents/CODEX_R259_IDEATION_EVALUATION.md; S139/ = work/S139_crossseq_revisit/; S137/ = work/S137_geometry_baselines/; S140/ = work/S140_warp_guided/; S141/ = work/S141_finetune/; V/ = data/S134_tacc/vmem_src/. Source snapshot hashes and the draft hash are in §5. The memory registry was only a continuity locator; current files and reproduced scores support the findings.

## 1. Findings

CRITICAL means a directly copied implementation would invalidate the comparison. MAJOR means interpretation or reproducibility must change before freezing. Neither severity means that a new GPU result has been observed.

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| Broad novelty is already occupied. “Useful evidence is consumer-dependent” is not the contribution. | MAJOR; reject the broad novelty claim | D:9–12,30; FAR, arXiv:2609.34677, exact title and inspected sections in §4. It already defines consumer predictive utility and uses it to supervise recall. | Ask whether this specified external warp proxy leaves a held-seed selection shortfall for a fixed sampled generator over identical complete context sets. Describe an exploratory case study, not a new principle or retriever. |
| Selection among six arms does **not** create positive expected cross-fitted R under independent held-seed noise. “Oracle” nevertheless misnames its estimand. | MAJOR conceptual correction | D:26–29; proof and simulations in §2. Selection and evaluation folds are disjoint. | Retain the split. Rename it a two-selection-seed **cross-fitted hindsight selector**. It estimates that procedure's value relative to c_W, not the true best expected set. Keep negative R. |
| The proposed gate is not a calibrated significance procedure. Shared-window seed effects matter. | MAJOR | D:30–34; S139/gen_s139.py:109–126 and S141/gen_s141.py:134–155 reset the same seed in every cell. The exact shared-panel permutation reference passes the full draft gate in 109/1296 cases, DERIVED in §2.4. | Keep +0.20 dB as a practical bar. Predeclare null models, preserve whole seed panels in dependence sensitivities, rerun selection inside every null draw, and label resulting tail probabilities assumption-dependent. Do not equate window-bootstrap exclusion of zero with scene-level significance. |
| Three archived arms cannot identify six-arm variance/covariance, and duplicate labels are not independent arms. | MAJOR | S139/PROTOCOL.md:32–38 versus D:15–23. The score tensor and simulation receipts are in §2. | Calibrate on actual unique ordered sets; copy scores exactly across duplicate rule aliases. Treat the six-arm planning null here as an extrapolation. Compute ranks over unique sets, not repeated labels. |
| This is reused chess data and reused discovery seeds. Windows share history and are not independent scenes. | MAJOR for confirmation | S139/PROTOCOL.md:17–22,38; R259:133–154; D:15. The manifest reuses a history traversal within each pair. | Mark S143 exploratory. Report all pair means and leave-one-pair-out estimates. Fresh seeds would improve seed-level replication but would not make chess unexposed. No population generalization from the window CI. |
| A 32-frame rooted star is implementable at the KPS interface, but its runtime/reliability is not verified here. | MAJOR specification gap | S139/kps.py:64–99 checks all known poses and root-0 edges without a four-view limit; V/extern/CUT3R/surfel_inference.py:188–196 presets poses, :356–363 creates the star. | If retained, freeze bank order, root, all poses, depths=None, niter=0, KPS parameters, crop and validity rules. Assert the actual star and prohibit silent KPS fallback. |
| Bank-conditioned depth is not interchangeable with four-context B2 depth. Reusing it for Q_W breaks “same evidence.” | MAJOR | CUT3R recurrent state depends on preceding frames: V/extern/CUT3R/src/dust3r/model.py:813–847,862–876. KPS estimates one scale from all non-root views: S139/kps.py:85–105. B2 reconstructs its selected context list anew: S139/baselines_s139.py:51–60. | Use bank geometry only to construct rule 5. Recompute Q_W from exactly the same four ordered RGB/pose inputs consumed by VMem, for every candidate. A coverage proxy need not equal B2 coverage, but must be named accurately. |
| A cheaper archived surfel proxy exists, but only for the last target. Frame-count sums are not union coverage. | MAJOR if substituted silently | S139/run_retrieval_s139.py:89–91,120–127 saves membership and a last-target render with learned focal ×0.65; V/modeling/pipeline.py:392–409 returns the visible index map, :473–498 produces weighted/quantized frame counts. Inventory in §5. | Prefer explicitly named **last-target surfel-support greedy** for the minimum-cost pilot. Build per-frame support masks from visible surfel membership and greedily maximize their OR-union. All-four-target coverage requires additional rendering; do not claim the cached map provides it. |
| Sorting changes actual conditioning, not just metadata. The draft's regeneration decision is correct. | MAJOR, already partly addressed | V/modeling/pipeline.py:1099–1119 scales from centered slot 0; :1136–1140 anchors Plücker coordinates to slot 0. S141/gen_s141.py:173–190 preserves ordered images and poses. §5 counts changed order in 22/24 contexts for each memory arm and changed slot 0 in 20/24. | Regenerate all canonical candidates and their B2 warps. Never pair sorted Q_W with old-order archived Q_G. State utility under this fixed slot policy, not order-invariant set utility. Keep the original-order fidelity replay separate. |
| The inherited warp scorer loses all but the first candidate's Q_W per window. | CRITICAL if reused unchanged | S140/score_s140.py:26 traverses generation files in sorted order; :39–43 guards and stores solely by window_id. | Precompute warp scores independently of generation traversal, keyed by window plus canonical ordered-set identity. One Q_W per unique candidate, shared only across seeds/consumers for that same candidate. Assert complete key coverage. |
| The generator's image cache can silently combine one set's images with another set's cameras. | CRITICAL if ctx_group is only the window | S141/gen_s141.py:170–184 caches latents/CLIP by ctx_group; :185–190 reloads cameras from the current ctx_refs. B2 filenames use window/ARM/target at S139/baselines_s139.py:67. | Use one ordered evidence identity consistently for ctx_group, warp filenames, scores, output keys and deduplication. Add a CPU schema/identity check before generation. |
| Plan schemas are incompatible without an explicit adapter. | MAJOR | S139/build_plan_s139.py:15–25 places scene_dir at plan level; S141/gen_s141.py:166,170 expects per-context scene_dir/ctx_group; S140/score_s140.py:30,35,44 additionally expects warp_files/mode/strength. | Freeze an S143 schema and validate all required fields. Explicitly select VARIANT=A, ADAPTER=NONE for base generation. Do not pass the S139 plan verbatim. |
| “KPS OK” and “failures logged” do not define a valid analysis panel. | MAJOR | S139/kps.py:18–33 can return infinite errors; :39–55 takes argmin without a finite-objective gate; :118–120 still emits OK. D:41–42 does not specify what missing candidates do to R. | Check numerical geometry independently of the label. Invalid required geometry/cells make the primary run incomplete; stop and report, without deleting difficult windows or replacing candidates after scores. |
| Q_W is a particular filled-image predictor, not absolute geometric information. Metric and rasterization details can change its rankings. | MAJOR | S137/geometry_baselines.py:23,49–75 exposes SPLAT and nearest fill; S139/baselines_s139.py:27–30 pools target SSE, :45–48 maps depth to the image grid. D:35's “SSIM versions” is undefined. | Freeze SPLAT=1, crop, depth mapping, fill, integer scoring, and aggregation. Add fixed common-support diagnostics and distinguish SSIM rescoring from SSIM-based reselection. Report per-window warp best-minus-second-best margins, not just best-minus-worst spread. |
| A negative R or a failed +0.20 threshold does not establish matching ranks or no consumer dependence. | MAJOR interpretation | ANALYTICAL: a noisy two-seed selector can choose badly; §2.1. D:46 correctly says a miss is not equivalence. | Preserve that caution. Report “no demonstrated shortfall with this pool and selection budget,” with uncertainty. Do not recycle a miss into a broad conclusion about all retrieval or all contexts. |

## 2. Null-distribution computation

### 2.1 What is being estimated

**ANALYTICAL.** Fix the panel, targets, ordered candidate packages, warp predictor and metric. Write Y(w,c,s) = μ(w,c) + ε(w,c,s), with μ the expected generated PSNR over sampling seeds. Let A and B be independent seed folds and ĉ_A(w) = argmax_c mean_A Y(w,c,s).

Conditional on the entire selection fold,

E[mean_B Y(w,ĉ_A(w),s) − mean_B Y(w,c_W(w),s) | A]
= μ(w,ĉ_A(w)) − μ(w,c_W(w)).

Thus E[R]=0 under equal μ across candidates within every window, regardless of candidate count. Correlation across arms within a seed, unequal arm variances, and correlation across windows do not invalidate this expectation; they affect variance. Dependence between the selection and evaluation seed vectors can invalidate it.

The ideal finite-pool oracle gap is mean_w[max_c μ(w,c) − μ(w,c_W)]. R estimates the value of a noisy two-seed selection procedure and is generally downward relative to that ideal gap under the stated independence. It can be negative. Averaging the exchanged folds does not create two independent experiments.

Three nulls must not be conflated:

- **Equal expected PSNR:** all candidates have equal μ; their sample outputs and variances may differ. This is the useful seed-noise null.
- **Joint arm exchangeability:** relabeling candidate scores preserves their joint distribution. This stronger assumption supports the permutation reference below.
- **Literal set invariance under common noise:** every candidate produces the same output at a paired seed. Then R is identically zero; independent-arm Gaussian noise is not a model of that sharp null.

Both selectors use target RGB scores in the analysis. Seed splitting prevents ordinary same-sample maximum optimism; it does not make either hindsight selector deployable or create target/scene holdout.

### 2.2 Construction and interpretation of the nulls

Only archived RTX 3090 seeds 3,4,5,6 are used, avoiding the hardware-confounded H800 seed block (S139/PROTOCOL.md:37–38). No target RGB is read. The commands join the archived score records with the existing three-candidate plan and B2 score files.

**DERIVED:** the archived cross-fitted R is **0.310847 dB**, and the local-selector-minus-global-rule gap is **0.355587 dB**. Pair means are **0.205295, 0.114483, 0.612763 dB**; leaving out the third pair reduces R to **0.159889 dB**. These are exploratory arithmetic on old-order S139 outputs, not S143 results. [Complete computation/output](#null-results).

For the pure-noise Gaussian planning null, remove each window-arm mean and the common seed effect:

D(w,c,s) = Y(w,c,s) − mean_s Y(w,c,s) − mean_c Y(w,c,s) + mean_cs Y(w,c,s).

Estimate per-window contrast-noise variance by sum_cs D² / [(3−1)(4−1)]. The degrees of freedom matter: dividing by 3(4−1) after double-centering would underestimate iid arm-specific variance. The resulting RMS σ is **0.302666 dB**; raw within-arm seed SD RMS is **0.449990 dB**. [Complete computation/output](#null-results).

The independent-window model generates independent candidate errors with that σ and fresh independent two-seed fold means. The panel-covariance model instead uses factor L(w,:) = vec(D(w,:,:))/sqrt(6), so LLᵀ retains the measured average cross-window contrast covariance. It draws independent candidate vectors with that covariance. This is **not** the complete empirical cross-arm covariance; it is an explicit exchangeable-candidate extrapolation. For six candidates the fixed reference is candidate 0 in every window. That is a planning scenario, not a verified future pattern of c_W. The factor is estimated from very little data and has rank six.

The raw-score permutation sensitivity independently relabels arms in each seed. One version permutes independently within each window; another uses one permutation per seed shared across the entire window panel. A single permutation shared across all seeds would preserve repeatable candidate effects and would not remove them. Raw permutations retain observed score spread, including genuine candidate effects, so they are **exchangeability reference distributions, not pure seed-variance estimates**.

**DERIVED summary; all units are dB except the tail fraction.** Sources: [Monte Carlo receipt](#null-results), [exact permutation receipt](#exact-results).

| Reference distribution | Mean R | SD R | 95th percentile R | Fraction R ≥ 0.20 |
|---|---:|---:|---:|---:|
| Three candidates, Gaussian, independent windows | −0.000203 | 0.040045 | 0.067413 | 0 / 100000 |
| Three candidates, Gaussian, panel covariance | −0.000226 | 0.061490 | 0.103428 | 0.000900 |
| Six candidates, Gaussian, independent windows | 0.000061 | 0.043535 | 0.073242 | 0.000020 |
| Six candidates, Gaussian, panel covariance | 0.000159 | 0.062500 | 0.105877 | 0.001140 |
| Three candidates, raw per-seed permutation, independent windows | 0.000210 | 0.080491 | 0.136463 | 0.008890 |
| Three candidates, raw per-seed permutation, shared panel, **exact enumeration** | 0.000000 | 0.142796 | 0.248774 | 0.085648148 |

The six-arm Gaussian models show no upward expected cross-fitted bias. In contrast, selecting and evaluating on the same fold gives about **0.256 dB** purely from noise. A deliberately imposed fold correlation of 0.25 produces a cross-fitted mean of **0.063816 dB**; that is an assumption sensitivity, not measured fold leakage. [Complete computation/output](#null-results).

**Decision on +0.20:** it comfortably exceeds the tails of the specific fitted pure-noise Gaussian models, so the claim that “six-arm winner's curse necessarily explains +0.20 after splitting” is rejected. It is nevertheless **not safe as a universal significance cutoff**. In the exact shared-panel permutation reference, the draft's entire gate—including the window-bootstrap lower bound, pair-sign condition, and geometric-spread condition—passes in **109/1296 = 0.084104938** relabelings. The window bootstrap does not cure shared-panel variation. This fraction is conditional on the exchangeability reference and exposed three-arm data; it is not a demonstrated S143 false-positive rate. [Exact computation/output](#exact-results).

A planning cutoff of **+0.30 dB** would have tail mass **25/1296 = 0.019290123** in that exact three-arm reference, but importing +0.30 into six-arm S143 as a certified threshold would repeat the same mistake. Use the actual frozen pool and explicit null assumptions as specified in §3. The observed old R has reference tail mass **20/1296 = 0.015432099**; this is not confirmatory significance because the panel, seeds and promising statistic were already inspected. [Exact computation/output](#exact-results).

Zero exceedances in a finite Monte Carlo sample mean zero observed exceedances, not zero probability. Three sequence pairs also cannot yield a one-sided sign-test probability below 1/8 even if all signs are positive (ANALYTICAL); do not present pair signs as a conventional population significance test.

<a id="null-results"></a>
### 2.3 Exact CPU command and complete Monte Carlo output

Executed from the repository root using the existing environment. Exit code: 0. The program writes no files.

~~~bash
.venv-cut3r/bin/python -B - <<'PY'
import sys, json, hashlib
from pathlib import Path
import numpy as np
root = Path('work/S139_crossseq_revisit')
paths = [root/'plan_v2.json', root/'WINDOW_MANIFEST.json',
         root/'results/stepB_tacc/S139_SCORES_tacc.json',
         *[root/f'BASE_b2_{a}.json' for a in ['static','mem_pose','mem_vmem']]]
plan, manifest, scores = [json.loads(p.read_text()) for p in paths[:3]]
arms = ['static_recent','mem_pose','mem_vmem']; seeds = [3,4,5,6]
wins = [w['window_id'] for w in manifest['windows']]
pairs = [w['pair'] for w in manifest['windows']]
lookup = {(c['window_id'],a):c for c in plan['contexts'] for a in c['arms']}
Y = np.array([[[scores['runs'][lookup[w,a]['ctx_key']+'__s'+str(s)]['aggregate']['psnr_db']
               for s in seeds] for a in arms] for w in wins])
warp = [{r['window_id']:r['psnr'] for r in json.loads(p.read_text())['rows']} for p in paths[3:]]
W = np.array([[d[w] for d in warp] for w in wins])
cw = W.argmax(1); wi = np.arange(len(wins))
A, B = Y[:,:,:2].mean(2), Y[:,:,2:].mean(2)
rw = .5*(B[wi,A.argmax(1)]-B[wi,cw]+A[wi,B.argmax(1)]-A[wi,cw])
gg = .5*(B[wi,A.argmax(1)]-B[:,A.mean(0).argmax()]+A[wi,B.argmax(1)]-A[:,B.mean(0).argmax()])
rng = np.random.default_rng(260)
print('DERIVED ARCHIVED scores only; no image pixels, model calls, or file writes')
print('python',sys.version.split()[0],'numpy',np.__version__)
print('shape_windows_arms_seeds',Y.shape,'seeds',seeds,'finite',bool(np.isfinite(Y).all()))
print('observed_R_db %.6f global_gap_db %.6f warp_spread_db %.6f' % (rw.mean(),gg.mean(),np.ptp(W,axis=1).mean()))
ci = np.quantile(rw[rng.integers(0,len(wins),(10000,len(wins)))].mean(1),[.025,.975])
print('DESCRIPTIVE_window_bootstrap95_db',np.round(ci,6).tolist())
for pair in sorted(set(pairs)):
    mask = np.array([p==pair for p in pairs])
    print('pair',pair,'R_db %.6f leave_pair_out_R_db %.6f'%(rw[mask].mean(),rw[~mask].mean()))
# Double-center: remove stable window-arm means, then common seed effects.
E = Y-Y.mean(2,keepdims=True)
D = E-E.mean(1,keepdims=True)
nw, na, ns = Y.shape
# Unbiased contrast-based iid-arm variance, per window: (A-1)*(S-1) degrees of freedom.
sigma = np.sqrt((D*D).sum((1,2))/((na-1)*(ns-1)))
factor = D.reshape(nw,na*ns)/np.sqrt((na-1)*(ns-1))
assert np.allclose((factor*factor).sum(1),sigma*sigma)
print('raw_within_arm_seed_sd_RMS_db %.6f'%np.sqrt(np.mean(np.var(Y,axis=2,ddof=1))))
print('contrast_noise_sigma_db min_median_RMS_max',np.round([sigma.min(),np.median(sigma),np.sqrt(np.mean(sigma*sigma)),sigma.max()],6).tolist())
print('spatial_factor_rank',int(np.linalg.matrix_rank(factor)),'estimated_from_only_4_seed_panels')
N = 100000; batch = 2000
print('null_replicates',N,'rng_default_rng_260','quantiles',[.025,.50,.95,.975,.99])
def stats(label, r, extra=None):
    q=np.quantile(r,[.025,.50,.95,.975,.99])
    print(label,'mean_sd_db',np.round([r.mean(),r.std(ddof=1)],6).tolist(),
          'q_db',np.round(q,6).tolist(),'Pr_R_ge_0.20 %.6f'%np.mean(r>=.2),
          'Pr_R_ge_observed %.6f'%np.mean(r>=rw.mean()))
    if extra is not None:
        print(label,'SAME_FOLD_max_minus_fixed_mean_db %.6f'%extra.mean())
def fold_stat(x,z,ref):
    selx=x.argmax(2); selz=z.argmax(2)
    pick=lambda a,k:np.take_along_axis(a,k[:,:,None],axis=2)[:,:,0]
    r=.5*(pick(z,selx)-pick(z,ref)+pick(x,selz)-pick(x,ref))
    naive=.5*(x.max(2)-pick(x,ref)+z.max(2)-pick(z,ref))
    return r.mean(1),naive.mean(1)
def gaussian(k,spatial=False,rho=0.0):
    rs=[]; nsame=[]
    for start in range(0,N,batch):
        n=min(batch,N-start)
        def draw():
            if spatial:
                return np.einsum('bka,wa->bwk',rng.normal(size=(n,k,na*ns)),factor)/np.sqrt(2)
            return rng.normal(size=(n,nw,k))*sigma[None,:,None]/np.sqrt(2)
        x=draw(); z=rho*x+np.sqrt(1-rho*rho)*draw()
        ref=np.broadcast_to(cw if k==3 else np.zeros(nw,dtype=int),(n,nw))
        r,nn=fold_stat(x,z,ref); rs.append(r); nsame.append(nn)
    stats('GAUSSIAN_k%d_%s_rho%.2f'%(k,'panel_cov' if spatial else 'indep_windows',rho),np.concatenate(rs),np.concatenate(nsame))
for k in [3,6]:
    gaussian(k)
    gaussian(k,spatial=True)
gaussian(6,rho=.25)
# Sensitivity only: raw score permutations impose stronger arm exchangeability, not just equal means.
for shared in [False,True]:
    rs=[]
    for start in range(0,N,batch):
        n=min(batch,N-start)
        shape=(n,1 if shared else nw,na,ns)
        idx=rng.random(shape).argsort(axis=2)
        yp=np.take_along_axis(np.broadcast_to(Y,(n,nw,na,ns)),
                             np.broadcast_to(idx,(n,nw,na,ns)),axis=2)
        x,z=yp[:,:,:,:2].mean(3),yp[:,:,:,2:].mean(3)
        ref=np.broadcast_to(cw,(n,nw))
        r,_=fold_stat(x,z,ref); rs.append(r)
    stats('RAW_PER_SEED_ARM_PERM_'+('panel_shared' if shared else 'window_local'),np.concatenate(rs))
print('six-arm results are model-based extrapolations; three new arms have no archived scores')
for p in paths:
    print('sha256',hashlib.sha256(p.read_bytes()).hexdigest(),str(p))
PY
~~~

~~~text
DERIVED ARCHIVED scores only; no image pixels, model calls, or file writes
python 3.12.14 numpy 1.26.4
shape_windows_arms_seeds (24, 3, 4) seeds [3, 4, 5, 6] finite True
observed_R_db 0.310847 global_gap_db 0.355587 warp_spread_db 1.928376
DESCRIPTIVE_window_bootstrap95_db [0.112921, 0.57351]
pair seq-01->seq-02 R_db 0.205295 leave_pair_out_R_db 0.363623
pair seq-04->seq-03 R_db 0.114483 leave_pair_out_R_db 0.409029
pair seq-06->seq-05 R_db 0.612763 leave_pair_out_R_db 0.159889
raw_within_arm_seed_sd_RMS_db 0.449990
contrast_noise_sigma_db min_median_RMS_max [0.155648, 0.278631, 0.302666, 0.562949]
spatial_factor_rank 6 estimated_from_only_4_seed_panels
null_replicates 100000 rng_default_rng_260 quantiles [0.025, 0.5, 0.95, 0.975, 0.99]
GAUSSIAN_k3_indep_windows_rho0.00 mean_sd_db [-0.000203, 0.040045] q_db [-0.07533, -0.001373, 0.067413, 0.081392, 0.097503] Pr_R_ge_0.20 0.000000 Pr_R_ge_observed 0.000000
GAUSSIAN_k3_indep_windows_rho0.00 SAME_FOLD_max_minus_fixed_mean_db 0.170634
GAUSSIAN_k3_panel_cov_rho0.00 mean_sd_db [-0.000226, 0.06149] q_db [-0.115633, -0.001776, 0.103428, 0.124652, 0.148512] Pr_R_ge_0.20 0.000900 Pr_R_ge_observed 0.000000
GAUSSIAN_k3_panel_cov_rho0.00 SAME_FOLD_max_minus_fixed_mean_db 0.170853
GAUSSIAN_k6_indep_windows_rho0.00 mean_sd_db [6.1e-05, 0.043535] q_db [-0.08271, -0.000903, 0.073242, 0.087954, 0.105243] Pr_R_ge_0.20 0.000020 Pr_R_ge_observed 0.000000
GAUSSIAN_k6_indep_windows_rho0.00 SAME_FOLD_max_minus_fixed_mean_db 0.255671
GAUSSIAN_k6_panel_cov_rho0.00 mean_sd_db [0.000159, 0.0625] q_db [-0.117242, -0.001736, 0.105877, 0.127823, 0.152624] Pr_R_ge_0.20 0.001140 Pr_R_ge_observed 0.000000
GAUSSIAN_k6_panel_cov_rho0.00 SAME_FOLD_max_minus_fixed_mean_db 0.255473
GAUSSIAN_k6_indep_windows_rho0.25 mean_sd_db [0.063816, 0.045956] q_db [-0.023439, 0.062746, 0.141435, 0.156877, 0.174244] Pr_R_ge_0.20 0.002060 Pr_R_ge_observed 0.000000
GAUSSIAN_k6_indep_windows_rho0.25 SAME_FOLD_max_minus_fixed_mean_db 0.255714
RAW_PER_SEED_ARM_PERM_window_local mean_sd_db [0.00021, 0.080491] q_db [-0.151061, -0.002227, 0.136463, 0.163821, 0.196673] Pr_R_ge_0.20 0.008890 Pr_R_ge_observed 0.000140
RAW_PER_SEED_ARM_PERM_panel_shared mean_sd_db [0.000367, 0.142952] q_db [-0.244944, -0.004468, 0.250263, 0.280104, 0.328601] Pr_R_ge_0.20 0.085780 Pr_R_ge_observed 0.015400
six-arm results are model-based extrapolations; three new arms have no archived scores
sha256 62c49eeb87b5e5934e38469fa53465b3fbe8fdb469b688130cd8efab3a83fb6b work/S139_crossseq_revisit/plan_v2.json
sha256 30de073668f72ad28fa209d2696fb48f106056035f99a8658aab5f5bc420fc61 work/S139_crossseq_revisit/WINDOW_MANIFEST.json
sha256 3c42e2c3658f1115bda23b5bb1ecef673a824bbc51166137bffe19a32340bd5f work/S139_crossseq_revisit/results/stepB_tacc/S139_SCORES_tacc.json
sha256 9c95977f93a923bb31a133aac8a0c9f443b9f0ff32c9e8f78d693ac81fdfe8cb work/S139_crossseq_revisit/BASE_b2_static.json
sha256 bfc7d4f4ffde5205743985880767160164cd01fd3556e755290ecfdc71ff64a1 work/S139_crossseq_revisit/BASE_b2_mem_pose.json
sha256 478407dd57883cebb255b3237424a15ef6eb0b505351433e256a8e56aeb3db4f work/S139_crossseq_revisit/BASE_b2_mem_vmem.json
~~~

<a id="exact-results"></a>
### 2.4 Exact enumeration and the complete draft gate

The shared-panel three-arm transformation group has (3!)^4 = 1296 elements. This enumerates all of them rather than relying on Monte Carlo. Exactness refers to enumeration and, **only if its assumptions hold**, the conditional joint-exchangeability test. It does not prove arm exchangeability under the weaker equal-means null.

Executed from the repository root. Exit code: 0. Complete command and output:

~~~bash
.venv-cut3r/bin/python -B - <<'PY'
import itertools, json
from pathlib import Path
import numpy as np
r=Path('work/S139_crossseq_revisit')
p=json.loads((r/'plan_v2.json').read_text())
m=json.loads((r/'WINDOW_MANIFEST.json').read_text())['windows']
s=json.loads((r/'results/stepB_tacc/S139_SCORES_tacc.json').read_text())['runs']
arms=['static_recent','mem_pose','mem_vmem']; wi=np.arange(len(m))
lookup={(c['window_id'],a):c['ctx_key'] for c in p['contexts'] for a in c['arms']}
Y=np.array([[[s[lookup[w['window_id'],a]+'__s'+str(seed)]['aggregate']['psnr_db']
             for seed in [3,4,5,6]] for a in arms] for w in m])
wd=[{q['window_id']:q['psnr'] for q in json.loads((r/f'BASE_b2_{a}.json').read_text())['rows']}
    for a in ['static','mem_pose','mem_vmem']]
W=np.array([[d[w['window_id']] for d in wd] for w in m]); cw=W.argmax(1)
def stat(y):
    a,b=y[:,:,:2].mean(2),y[:,:,2:].mean(2)
    return .5*(b[wi,a.argmax(1)]-b[wi,cw]+a[wi,b.argmax(1)]-a[wi,cw])
obs=stat(Y).mean()
perms=list(itertools.permutations(range(3))); rr=[]
for ps in itertools.product(perms,repeat=4):
    yp=np.stack([Y[:,list(ps[t]),t] for t in range(4)],axis=2)
    rr.append(stat(yp))
rr=np.array(rr); means=rr.mean(1)
print('EXACT conditional panel-shared per-seed arm-exchangeability reference; NOT equal-means-only exactness')
print('permutations',len(means),'R_observed_db %.6f'%obs)
print('mean_sd_db',np.round([means.mean(),means.std(ddof=0)],6).tolist())
print('q_025_50_95_975_99_db',np.round(np.quantile(means,[.025,.5,.95,.975,.99]),6).tolist())
for threshold in [.2,.3,obs]:
    count=int(np.sum(means>=threshold))
    print('threshold_db %.6f count %d / %d probability %.9f'%(threshold,count,len(means),count/len(means)))
# Implement the draft's full gate for this archived three-arm reference, including its rng=0 bootstrap.
rng=np.random.default_rng(0)
idx=rng.integers(0,len(m),(10000,len(m)))
counts=np.stack([np.bincount(row,minlength=len(m)) for row in idx])/len(m)
lower=np.quantile(rr@counts.T,.025,axis=1)
pm=np.stack([rr[:,[i for i,w in enumerate(m) if w['pair']==pair]].mean(1)
             for pair in sorted({w['pair'] for w in m})],axis=1)
gate=(means>=.2)&(lower>0)&((pm<0).sum(1)<2)&(np.ptp(W,axis=1).mean()>=1)
print('full_draft_gate_count %d / %d probability %.9f'%(gate.sum(),len(gate),gate.mean()))
print('identity_descriptive_bootstrap_lower_db %.6f'%np.quantile(stat(Y)@counts.T,.025))
print('This is an exposed three-arm sensitivity calculation, not an S143 six-arm p-value.')
PY
~~~

~~~text
EXACT conditional panel-shared per-seed arm-exchangeability reference; NOT equal-means-only exactness
permutations 1296 R_observed_db 0.310847
mean_sd_db [0.0, 0.142796]
q_025_50_95_975_99_db [-0.244863, -0.00456, 0.248774, 0.279913, 0.327863]
threshold_db 0.200000 count 111 / 1296 probability 0.085648148
threshold_db 0.300000 count 25 / 1296 probability 0.019290123
threshold_db 0.310847 count 20 / 1296 probability 0.015432099
full_draft_gate_count 109 / 1296 probability 0.084104938
identity_descriptive_bootstrap_lower_db 0.110938
This is an exposed three-arm sensitivity calculation, not an S143 six-arm p-value.
~~~

## 3. Corrected minimal specification

The following is an **ANALYTICAL proposal for the main agent to freeze**, not an executed protocol or permission to change validation flags.

### 3.1 Question, status and evidence boundary

Question: on the exposed S139 chess panel, does choosing an ordered context package by this fixed B2 predictor's PSNR leave generated PSNR that a two-seed hindsight selector can recover on other seeds?

Keep the existing panel, target references, base weights and generation budget. Retain seeds {3,4}/{5,6} only as an explicitly **exploratory continuation**. Do not describe recomputation with those seeds as independent replication of R259. A later confirmation must reserve new scenes/windows and/or new sampling seeds according to the particular generalization claim.

Construction and generation may read all bank RGB/poses and target poses. Only the scoring/analysis process may read target RGB. Geometry used to score a selected set must use only its four source RGBs and poses. No target depth. Do not claim the hindsight c_W or c_G is a deployable retrieval policy.

### 3.2 Pool and rule 5

Keep construction rules 1–4 and 6, with these clarifications:

1. Import S139 memberships from the archived plan/receipts. Do not silently recompute mem_pose in fp64 and call it the same arm: its original implementation casts poses and geodesics to fp32 and queries the last target (S139/pose_arms_s139.py:20–28,45–51). The new nearest-four rule averages distance over all four target poses; it is intentionally a different rule (D:17–18).
2. For nearest-four, use float64 input poses, rotation angle in radians plus 0.1 times translation distance in dataset units, mean over the four targets, stable bank-index tie-breaking.
3. For random, freeze NumPy version, manifest traversal order, default_rng(259), and one choice(32, size=4, replace=False) call per window before scoring.
4. Sort every resulting context by frozen bank index. Deduplicate exact ordered sets once; preserve construction-rule aliases without replenishing the pool. Freeze m_w, the actual unique-set count per window. Ties between candidates use the minimum original rule index attached to the set.

**Recommended minimal rule 5: last-target surfel-support greedy.** Use the already archived Step-A map and surfel-to-frame membership. For bank frame b define M_b(p)=1 when pixel p has a valid visible surfel whose membership includes b; otherwise 0. Starting with an empty set, choose the distinct remaining bank frame maximizing the number of newly covered pixels in the OR-union. Break ties by bank index and select four distinct frames even when marginal gain is zero. Freeze whether negative-facing pixels are excluded; use the existing renderer convention and exclude cos_value<0 to match its support filtering (V/modeling/pipeline.py:466–479). Record masks, marginal gains, map/membership hashes and selected refs.

This is a legitimate additional construction heuristic at the same final context budget; it is **not equivalent** to four-target B2 coverage or ground-truth visibility. It avoids a new full-bank CUT3R pass. The last-target focus also matches the existing mem_pose query, but does not make the average-target nearest-four rule identical.

If all-four-target coverage is essential, retain the proposed 32-frame star instead and write its full geometry contract before freezing. Use the exact bank order/root 0; all known poses; depths=None; niter=0; fixed KPS sampling, confidence rule and crop. Define coverage as the sum, over all four targets, of per-frame projected support unions with fixed positive-depth, image-boundary and raster rules. Require finite KPS objective/sigma/focals and usable finite positive-depth support; report endpoint/near-zero-baseline degeneracy. Do not accept an OK label alone. No unverified runtime or depth-equivalence claim accompanies this alternative.

In either variant, **do not feed bank-conditioned depths into the primary Q_W**. Otherwise the warp sees extra images that the generator does not, even when both outputs are labeled by the same four-frame set. The source grounds this distinction in the findings table.

### 3.3 Ordered identity, generation and warp scoring

Define a canonical identity from window_id, ordered ctx_refs, ordered target_refs, scene_dir, convention, intrinsics identity and the frozen reconstruction configuration. Keep consumer/checkpoint and seed in output identities in addition to this shared evidence identity. Store a content hash and human-readable refs.

Every context record must include scene_dir, window_id, ctx_key, ctx_group, ctx_refs, target_refs, convention, arms/rule aliases, and warp_files. ctx_group must uniquely identify the ordered image evidence. If adapting S140's scorer, provide its mode/strength fields or remove those dependencies in a new S143 scorer. No modification to historical S139–S141 files is needed.

Use VARIANT=A, ADAPTER=NONE explicitly. Freeze the actual source/weight/config hashes and package environment in the final protocol. The CPU B2 import resolves through the older isolated source and S135 KPS (work/S135_scale_init/repro_kps.py:22–31; S139/baselines_s139.py:14,42–43); the specific CUT3R/KPS files checked are byte-identical to the cited mirror (§5). This does not certify every file or either weight artifact. Hash the files actually loaded, rather than assuming a repository HEAD identifies transported/untracked code.

Generate every unique sorted context on all four seeds in fresh output directories. Keep a window's paired candidates/seeds on the same frozen hardware/software configuration; if multiple cards are used, shard complete windows rather than systematically assigning folds to devices. The existing generic job-index sharding is at S141/gen_s141.py:158–160 and does not enforce that rule.

First perform the draft's unchanged original-order mem_vmem/window-0/seed-3 replay on the generation hardware. Require the full archived hash, not the abbreviated protocol claim. Abort on mismatch. Preserve paired RNG resets and the same sampling path for all candidates (S141/gen_s141.py:134–155). Regeneration under new order is a new measurement; byte equality with old reordered contexts is not expected.

For each unique set, reconstruct B2 from exactly its ordered four inputs with fixed KPS/niter=0, pixel-center mapping, SPLAT=1, known camera convention and nearest-hole fill (S139/baselines_s139.py:43–60; S137/geometry_baselines.py:23,49–75). Save filled warps and masks using the canonical identity.

**Scorer fix, concretely:**

- Iterate over the frozen unique-context manifest to score all warps once, independently of which generation file is encountered first.
- Store warps[(window_id,set_id)] with ordered refs, target refs, reconstruction/warp hashes, pooled SSE, count, PSNR, SSIM and support counts.
- Generation rows join exactly that key plus seed and consumer; no window-only lookup.
- Require one warp record per manifest candidate and exactly one generated score per required candidate/seed. Reject absent, duplicated or extra cells. Verify that rule aliases point to the same bytes.
- Do not use window/ARM/target alone for warp filenames when a label can refer to multiple contexts.

This repairs S140/score_s140.py:39–43 and also prevents the independent ctx_group cache hazard. A small CPU fixture with two different context IDs in one window should prove distinct warp scores and correct joins before expensive generation; it is a required check for the future implementation, not a test run in this review.

### 3.4 Metric, selectors and uncertainty

Primary score: convert to the existing integer model grid, sum squared error and channel counts across all four target frames, convert that pooled MSE to dB once per generated seed, then average per-seed dB in each fold and average windows. This matches S139/score_s139.py:52–62 and S139/baselines_s139.py:27–30. Do not replace it with the mean of four framewise PSNR values.

Compute c_W and the two c_G selectors over unique ordered candidates. Preserve the draft R formula exactly, but name it R_2seed_hindsight. Record selection indices, margins and rule aliases. Select the global rule on one fold over the same complete panel, evaluate on the other, and exchange; its per-window aliases map to the same unique-set scores. Both local and global selectors remain target-informed.

Freeze null calibration code before exposing S143 outcomes:

- For an assumption-labeled Gaussian equal-mean null, center each actual window×unique-set score series over seeds. Generate independent selection/evaluation seed panels with a covariance model fitted to those residuals; retain cross-arm and cross-window covariance in the full-panel sensitivity. A factor E_flat/sqrt(S−1) supplies one explicit fitted model. Duplicate labels must share the same draw. Also report an independent-window sensitivity. Do not transfer the three-arm variance estimates above as if they were six-arm measurements.
- Fit no alternative null model merely because the first gives an inconvenient tail. With four seed panels, the fitted full covariance is highly uncertain and low rank; publish that limitation. These are model-based diagnostics, not finite-sample distribution-free p-values.
- Rerun candidate maximization and the global-rule selection inside every simulated dataset. Use at least 100000 draws, a fixed analysis RNG and a one-sided tail estimate (1+#null R≥observed R)/(B+1).
- Report arm-label permutation only under its stronger exchangeability assumption. Preserve whole-panel transformations where admissible. If duplicate-set patterns prevent a common label-permutation group, do not silently break aliases to obtain a convenient six-arm permutation test.
- Report the null 95th percentile and a sensitivity cutoff max(+0.20 dB, largest predeclared null 95th percentile), alongside the old descriptive window-bootstrap interval. This cutoff is an **assumption-conditional discovery rule**, not a universal significance guarantee. The analogous global-rule gap needs its own calibration.

Retain the geometric-spread condition, show each window's best-minus-second-best margin, all three pair means and leave-one-pair-out R. Use the draft's sign condition only as a descriptive guard. Require a positive calibrated local-minus-global gap before claiming finite-panel window-specific preference structure; otherwise report a global-rule effect. Do not infer that rule heterogeneity generalizes to new windows.

If a formal seed-generalization claim is required, the cleaner follow-up is to freeze c_G/c_W/global selections using discovery seeds, then evaluate their paired differences on **fresh independent seed panels** without reselection. Each test seed contributes one panel-average contrast, so the uncertainty unit is the seed panel. Predeclare an appropriate confidence procedure and adequate seed budget; four reused seeds and a window bootstrap do not supply that confirmation. Scene generalization separately needs independent scenes. This is outside the minimum exploratory pilot, not an automatic expansion of its compute cap.

### 3.5 Controls and outcomes

Report all candidate Q_W/Q_G pairs, unique-set rank correlations, seed-fold ranking agreement, ties and geometric selection margins. Undefined correlations for tied/degenerate pools remain undefined. Include copy-nearest within each set and from the whole bank; the latter has a larger choice pool and must be labeled accordingly. Freeze the same pose-distance definition for those copy baselines.

For SSIM, report both (a) SSIM differences at PSNR-selected identities and (b) a separately labeled exploratory SSIM-reselected R. These answer different questions. The full-frame metric comparison is primary. For regional diagnostics use a fixed common support mask across compared candidates and show its size; candidate-specific coverage masks otherwise change which pixels are evaluated. Keep nearest-fill/hole quality distinct from observed source support. No metric earns a claim of absolute evidence quality.

Success wording is limited to: “On this exposed panel and fixed slot policy, this B2-PSNR selector leaves a specified held-seed VMem-PSNR shortfall relative to a target-informed two-seed selection procedure, under the stated null sensitivities.” It does not establish that VMem ignores memory, that retrieval is optimal, or that the effect is a new general principle.

A miss means no demonstrated shortfall with this finite pool and selector budget. It is not equivalence or proof of agreeing rankings. Invalid geometry, fidelity failure or missing cells means **incomplete/invalid assay**, not a negative scientific result. Freeze that failure handling before scores; no post-score pool replacement or complete-case deletion.

A same-pool S141-A comparison, if later available, is secondary and concerns training dependence within VMem. A smaller R can also reflect changed noise or reduced candidate spread; inspect the full score/rank matrix and recalibrate its noise before saying preferences moved toward geometry. It is not an independent architecture replication.

Retain the draft generation cap; count the replay and any optional adapter generation explicitly. The draft GPU-time estimate is a planning estimate, not verified runtime for the corrected assay. Geometry validity, identity/scoring checks and fidelity precede the expensive run. This review does not start that run.

## 4. Verified literature boundary

The arXiv abstract records and relevant full HTML sections were checked. MBench and MIND have v2; the other inspected versions are v1. Statements below describe the inspected protocols, not all conceivable unpublished variants. No exact duplicate located is bounded retrieval evidence, not proof of firstness.

| Verified arXiv ID, exact record title and sections | Existing measurement and boundary |
|---|---|
| **2606.00793v2 — “MBench: A Comprehensive Benchmark on Memory Capability for Video World Models,” §§3–4, especially §4.3.1.** [Primary paper](https://arxiv.org/html/2606.00793v2) | Evaluates memory consistency with trigger-conditioned scoring; geometric metrics assess epipolar/reprojection consistency of generated frame pairs. Those are output diagnostics, not rankings of a shared finite input-set pool by an external warp and a generator. |
| **2602.08025v2 — “MIND: Benchmarking Memory Consistency and Action Control in World Models,” §§3.1,3.4–3.5.** [Primary paper](https://arxiv.org/html/2602.08025v2) | Uses memory-prefix prediction, revisit-reference MSE and generated forward/reverse consistency under controlled trajectories. Contextual fidelity is already evaluated, but the inspected protocol does not enumerate alternative context sets and compare two consumers' rankings on them. |
| **2608.27328v1 — “R2M-Bench: Evaluating Revisit Memory via Relative Consistency in Interactive Video World Models,” §§3–4,5.2.** [Primary paper](https://arxiv.org/html/2608.27328v1) | Calibrates revisit pairs against gap-matched and short-range pairs from the same rollout. Its same-rollout control is different from competing input sets. It expressly limits MemoryGain to observable consistency rather than causal identification of internal memory. |
| **2609.36843v1 — “RolloutFaith: Auditing Persistent Internal Interventions in Visual World Model,” §§3.2–3.4,5; Appendices B.3,E.1,H.2.** [Record](https://arxiv.org/abs/2609.36843), [full paper](https://arxiv.org/html/2609.36843v1) | Studies reference activation capacity, immediate/sustained benefit and restoration under matched events/actions/noise. Controlled headroom and consequential utility are established diagnostic ideas. Its intervention object is internal activation, not a pool of source-image sets ranked by reconstruction and generation. The record title is singular “Model”; the HTML heading uses “Models.” |
| **2608.08982v1 — “Twin Rollouts: Noise-Coupled Counterfactual Branching in Interactive Video World Models,” §§1–3.** [Primary paper](https://arxiv.org/html/2608.08982v1) | Formalizes shared-prefix/noise branching, locality and simulator counterfactual fidelity. The inspected version is a framework note with a minimal illustration and broader experiments forthcoming. Shared seeds are not new; no warp-versus-generator input-set ranking is specified. |
| **2609.34677v1 — “Learning What to Recall: Adaptive Multi-Cue Episodic Memory for World Models,” §§3.1–3.3,4.1–4.3; Appendices B.3,C.1.** [Primary paper](https://arxiv.org/html/2609.34677v1) | **FAR is the closest overlap.** It defines set-level predictive likelihood utility, trains recall using singleton negative diffusion-loss credit and evaluates geometric/FOV versus learned recall downstream. Appendix B.3 distinguishes singleton credit from higher-order set effects. Consumer-specific utility and geometry-only recall limitations are already part of its problem. The possible S143 distinction is direct external-warp PSNR versus held-seed sampled-generator PSNR over identical complete sets. |

**ANALYTICAL novelty assessment:** “geometric utility versus consumer utility on the same evidence” is too vague to be new: FAR already joins candidate-memory predictive utility to downstream recall. The exact paired **complete-set, external-reconstruction-versus-sampled-generation ranking audit** was not located in the inspected protocols. S143's sets allow joint context effects to influence the outcome, but do not isolate or prove higher-order interactions; that would require additional controlled set manipulations.

A potentially substantive result is a stable, null-calibrated set-ranking disagreement that survives canonical ordering, global-rule controls and independent scene/consumer replication. The contribution would be the measured structure and boundary of that disagreement plus a reproducible assay. One exposed chess panel with one frozen VMem remains a case study; neither a positive R nor the absence of an exact duplicate authorizes a novelty claim.

## 5. Source and ordering receipt

The checkout was already dirty at entry: AGENTS.md was modified and unrelated S141/S142 files, S143 drafts, reviewer outputs and prompts were untracked. They were left alone. The snapshot HEAD below does not imply all cited files are tracked at that revision.

This command checks metadata, ordering and source bytes only. It does not read image pixels, run CUT3R, verify weights, or inspect remote state. Executed from the repository root; exit code 0; complete output follows.

~~~bash
python3 -B - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
r=Path('work/S139_crossseq_revisit')
m=json.loads((r/'WINDOW_MANIFEST.json').read_text())
p=json.loads((r/'plan.json').read_text())
wins={w['window_id']:w for w in m['windows']}
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
print('draft_sha256',hashlib.sha256(Path('work/S143_context_ranking/PROTOCOL_DRAFT.md').read_bytes()).hexdigest())
for arm in ('static_recent','mem_pose','mem_vmem'):
    rows=[c for c in p['contexts'] if arm in c['arms']]
    reorder=first=repeat=0
    for c in rows:
        bank=wins[c['window_id']]['bank']; refs=c['ctx_refs']; ordered=sorted(refs,key=bank.index)
        reorder+=refs!=ordered; first+=refs[0]!=ordered[0]; repeat+=len(set(refs))<4
    print(arm,dict(contexts=len(rows),order_changes=reorder,first_slot_changes=first,repeated_frame_contexts=repeat))
root=r/'results/stepA_superpod'
print('stepA_saved_maps',sum((root/w['window_id']/'retrieval_maps.npz').is_file() for w in m['windows']))
print('stepA_saved_membership',sum((root/w['window_id']/'surfel_to_timestep.npz').is_file() for w in m['windows']))
print('all_stepA_map_targets_are_last_target',all(json.loads((root/w['window_id']/'WINDOW_RECEIPT.json').read_text())['render_last_target']['target']==w['targets'][-1] for w in m['windows']))
for suffix in ('extern/CUT3R/surfel_inference.py','extern/CUT3R/src/dust3r/model.py','extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py'):
    a=Path('work/S17C_interface_preparation/isolated_vmem_source')/suffix
    b=Path('data/S134_tacc/vmem_src')/suffix
    print(suffix,'same_bytes',a.read_bytes()==b.read_bytes(),'sha256',hashlib.sha256(b.read_bytes()).hexdigest())
a=Path('work/S135_scale_init/kps.py'); b=r/'kps.py'
print('kps_S135_S139_same_bytes',a.read_bytes()==b.read_bytes(),'sha256',hashlib.sha256(b.read_bytes()).hexdigest())
for name in ['work/S139_crossseq_revisit/baselines_s139.py','work/S137_geometry_baselines/geometry_baselines.py',
             'work/S140_warp_guided/score_s140.py','work/S141_finetune/gen_s141.py',
             'data/S134_tacc/vmem_src/modeling/pipeline.py']:
    print('sha256',hashlib.sha256(Path(name).read_bytes()).hexdigest(),name)
PY
~~~

~~~text
HEAD ddb6b6c56685b5650621be2fc57e1996fcfb7624
draft_sha256 f97de93e141db253a186938be3b018d6bb9ad8eb182c2c17911df4c612aa9f66
static_recent {'contexts': 24, 'order_changes': 0, 'first_slot_changes': 0, 'repeated_frame_contexts': 0}
mem_pose {'contexts': 24, 'order_changes': 22, 'first_slot_changes': 20, 'repeated_frame_contexts': 0}
mem_vmem {'contexts': 24, 'order_changes': 22, 'first_slot_changes': 20, 'repeated_frame_contexts': 0}
stepA_saved_maps 24
stepA_saved_membership 24
all_stepA_map_targets_are_last_target True
extern/CUT3R/surfel_inference.py same_bytes True sha256 8a348645cd387147c35635f0a6b432d85bcf844e3839bd5a000d8147a85b17d5
extern/CUT3R/src/dust3r/model.py same_bytes True sha256 43b82c734f264a2e0e0a242dbd2d42855fe4e794cc25c0d433d6ef1b0dc54150
extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py same_bytes True sha256 b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21
kps_S135_S139_same_bytes True sha256 71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f
sha256 791068ee1410449143be7a3bd4a1c823efc5abe4e16ea1c7d523aa59c5cb7173 work/S139_crossseq_revisit/baselines_s139.py
sha256 10adca3b573faa1dbfc89eb364cc82f590f4c78820f7b9abff809bde8cf201e3 work/S137_geometry_baselines/geometry_baselines.py
sha256 61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79 work/S140_warp_guided/score_s140.py
sha256 c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
sha256 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
~~~

Only authored file: work/agents/CODEX_R260_S143_DRAFT_REJECTION.md. Follow-up for the main agent: revise and freeze the S143 protocol, implement candidate identity/scorer fixes, then execute its separately authorized preflight and experiment. No draft, source, ledger, authorization flag or original deliverable was modified by this review.

