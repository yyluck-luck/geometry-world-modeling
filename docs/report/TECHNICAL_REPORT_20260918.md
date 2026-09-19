# A Finite-Panel Audit of Context Selection in a Frozen VMem Configuration

Technical report, 2026-09-18. HKUST CSIT6910 independent research project.

**Question.** A released view-generation system selects four historical frames to condition each
generation. On a fixed panel it delivers only three *distinct* frames into those four slots in 10
of 14 windows, because two independently seeded selections return the same frame. Does that wasted
slot cost image quality?

**Intervention.** Replace the redundant slot with the pipeline's own next distinct ranked
candidate, in place, changing nothing else. Retention threshold **+0.20 dB**, fixed in writing
before any repair output was scored.

**Result.** **−0.016 dB**, across the 8 of 10 duplication-affected windows in which the
prespecified policy offers a replacement candidate. The no-op control passed byte-identically.

**Decision.** The performance explanation is discarded and this branch is closed. No further
generation is planned.

Project governance flags, the correction log and the closed-direction records are in §8 and the
appendices.

---

## 1. Outcome and stopping decision

A prospectively specified intervention was run and did not meet its criterion.

The released selector delivers only three distinct frames into four context slots in 10 of 14
evaluated windows. The proposed explanation was that this wasted slot materially costs image
quality. The test was an in-place replacement of the redundant slot with the pipeline's own next
distinct ranked candidate, with a retention threshold of **+0.20 dB** fixed in writing before any
repair output was scored.

**Measured: −0.016 dB in mean across the 8 of 10 duplication-affected windows in which the
prespecified policy offers a replacement candidate** (SD across windows 0.309, 3 of 8 positive).
In the remaining 2 affected windows **the intervention could not be instantiated under the
prespecified candidate-selection policy**, because that policy provided no fourth distinct
candidate: requesting up to seven entries still returned four, holding three distinct frames
(record in §A2). That is a property of the prespecified read policy, not a demonstration that
those windows are untestable under any possible design. The no-op control passed: all 8
window-seed executions in the 4 unaffected windows reproduced the sealed output byte-identically.

The duplication-as-performance-explanation is **discarded**. The threshold was not lowered, the
replacement policy was not changed, and no favourable subgroup was elevated.

**This branch is closed.** No further generation is planned.

Failure to meet a +0.20 dB criterion is **not** proof of no effect. The source-level cause of the
duplicate selection remains established; only its proposed material PSNR consequence does not.

Two results in this report were also **withdrawn during the work** and are recorded as such in
§8: an interpretation of a contaminated arm, and a claim stated with the wrong sign.

---

## 2. Scope and the quantity measured

**Data.** Two exposed development sequences, RGB-D Scenes v2 `scene_13` and `scene_14`, seq-01.
These sequences are exposed: they shaped the hypotheses during this project. Their target frames
are excluded from conditioning, but the sequences are **not** independent held-out evaluation data
and the term "held-out" is not used for them anywhere in this report.

**Panel.** 14 fixed windows (7 window starts × 2 sequences; window start 0 fails retrieval in both
sequences and is excluded with that reason). Bank = start + {0,5,…,55}, 12 frames. Targets =
start + {60,75,90,105}, i.e. forward extrapolation beyond the bank. 2 fixed seeds (42, 7).
**One dependency group.** One frozen consumer.

**Unequal horizons, recorded because it matters.** The fixed-offset arm may use frames only up to
offset +45; the retrieval bank extends to +55. Retrieval therefore has a candidate-availability
advantage. This is **not** a guarantee of any performance ordering: a frozen generator's output is
not monotone in candidate proximity, and this selector carries no dominance guarantee.

**Metric.** RGB PSNR only. Reference frames are loaded at native 480×640, converted to float,
area-resized to 576×768, cropped to columns 96:672, and quantised to uint8. Predictions are mapped
from [−1,1] to [0,1] when needed and quantised identically. MSE is accumulated over all four
targets of a window-seed before a single PSNR is taken. No geometry metric, no perceptual metric,
no human study.

**Aggregation order, fixed.** Seeds are controlled stochastic replications, not independent
scenes. The two seeds are averaged **within a window first**; all reported statistics are then
window-level.

**Inference.** Windows are a finite panel, not a sample from a population. The quantity measured is
the mean over exactly these windows and seeds. **No standard error, t statistic, confidence
interval, significance test, equivalence test or bootstrap appears in this report.** SD is reported
solely as a description of heterogeneity across the panel.

**What is being compared.** Every arm receives real historical frames. The principal baseline
comparison is between **retrieval-selected historical context and fixed-offset historical
context**. The remaining contrasts compare **state initialisation or context-selection variants**
against one another. **None of them is a comparison of memory versus no memory.**

---

## 3. Software and execution provenance

**Consumer.** VMem (arXiv:2506.18903), public repository `runjiali-rl/vmem`. Frozen: no training,
no fine-tuning, no new weights, no modification of the upstream source.

**Pinned source verified against the live public repository on 2026-09-18.** Public HEAD commit
`39291e4f272f6b4f270691d930926ab5930f942e` (2025-07-25). The project's pinned `navigation.py` has
sha256 `6d267365d5dcccf9f7cd6d535f19f80521f60a9634dffb35b9af398407389fcf`, **byte-identical** to the
file at public HEAD. Other pinned hashes: `modeling/pipeline.py`
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`; `app.py`
`02144b511a89c5619a380b0d08e2f62ce0946d7185046d4fd035d9caad28cc31`;
`configs/inference/inference.yaml`
`8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3`. No local patch was applied to
upstream code at any point.

**Complete generation call graph of the release.** `navigation.py` is the only caller of
`generate_trajectory_frames`, and it has **three** call sites:

| line | method | reached from | NMS argument | effective setting |
|---|---|---|---|---|
| 185 | `move_backward` | `app.py:219` | `use_non_maximum_suppression=False` | disabled |
| 234 | `move_forward` | `app.py:215` | `use_non_maximum_suppression=False` | disabled |
| 321 | `_turn` | `app.py:208,210` via `turn_left`/`turn_right` | **none passed** | resolves to `None` → `pipeline.py:103` → config `true` → **enabled** |

`get_context_info` has exactly one internal caller, `pipeline.py:1249`.

**The released demo therefore uses both retrieval settings on the same pipeline object, selected by
which action the user takes.**

**Retrieval state semantics, from the pinned source.** In `get_context_info`: the NMS-disabled
branch executes `self.initial_threshold = 1e8` unconditionally and then reads it; the NMS-enabled
branch assigns the attribute only when the pipeline holds exactly five frames
(`is_second_step = len(self.pil_frames) == 5`); at any other bank size the enabled branch reads
whatever value is present. `reset()` does not clear the attribute.

**Consequence, stated as static reachability only.** A native interaction of the form
`initialize → move_forward → move_forward → turn_left` leaves the bank at a size other than five
when the turn executes, so the enabled branch consumes the `1e8` written by the preceding movement.
The threshold a turn uses depends on whether the user moved first. **The demo was not run; this is
a source-level reachability statement plus the selector's own semantics, not a measured demo
behaviour.**

**Evaluation entry point.** At public HEAD the repository's non-`extern/` Python files are exactly
`app.py`, `navigation.py`, `modeling/*` and `utils/*`. **No evaluation or benchmark script is
present.** The configuration that produced the paper's tables therefore cannot be determined from
the release, and this report makes no claim about it.

**Execution environment.** HKUST SuperPOD, H800, Slurm + Apptainer, digest-pinned container,
`--containall --no-home --cleanenv`, offline HF/transformers. fp32 parameters with CUDA autocast,
matching the upstream default. Sampler, step count, guidance, resolution, context count and target
offsets are copied unchanged from the sealed run across all arms.

**Job ledger.** 595599 order-invariance gate (zero diffusion); 595614 leak-regime census (zero
diffusion); 595625 disabled-branch threshold-independence (zero diffusion); 594957 sealed three-arm
run; 595887 clean NMS-on arm; 595891 refill repair arm; 595902 in-place repair arm.

---

## 4. Arms and prospective specifications

| arm | context | corresponding released behaviour |
|---|---|---|
| `static` | fixed offsets +0, +15, +30, +45; no retrieval call | none — a project-defined baseline |
| `memory_nms_off` | pipeline retrieval, NMS disabled | the movement path |
| `memory_nms_on` | NMS enabled under an inherited `initial_threshold = 1e8` | turning **after** a movement |
| `memory_nms_on_clean` | NMS enabled from an isolated state | turning, with an **isolated threshold assigned at the five-frame priming step**. "Clean" is this operational definition only; it does not assert the configuration the authors intended or used. |
| `refill` | `(a,a,b,c) → (a,b,c,d)` | none — repair variant, source-faithful fill order |
| `inplace` | `(a,a,b,c) → (a,d,b,c)` | none — repair variant, primary |

The correspondence is **structural, not exact**: in the demo the bank grows as generated frames are
written back, whereas this diagnostic holds a fixed 12-frame bank.

**Repair specification and when it was fixed.** `REPAIR_SPEC_PREDECLARED_20260918.md` was written
before any repair output was scored, after an external review identified that the `refill` mapping
mixes a content change with a position change. It names `inplace` primary, retains `refill` as the
source-faithful variant, fixes the +0.20 dB threshold, fixes the eligibility rule, and records the
8/4/2 window accounting. The already-sealed `refill` arm was **not** deleted or rewritten.

**Candidate-list provenance, verified rather than argued.** The ranked candidate list is read out
of the pipeline, not re-implemented. Because `pipeline.py:492` computes
`num_retrieved_frames = min(context_num_frames + 10, len(timestep_weights))`, requesting a longer
selection could in principle enlarge the candidate pool, so a matching four-element prefix would
not certify the remainder. The list was therefore obtained at `context_num_frames` 5, 6 and 7 —
three different pool requests — with the query centre held fixed by passing `target_c2ws[-1:]`
(for which the `[-2:]` slice used at those sizes selects the same single pose as the native
`[-1:]`). **In every evaluated window the lists were exactly nested**, e.g.
`[11,11,10,9,8] ⊂ [11,11,10,9,8,3] ⊂ [11,11,10,9,8,3,4]`, with the shipped `[11,11,10,9]` as
prefix, and the distinct-frame count never exceeded the bank size. This is a statement about
exactly those requests and windows, not a theorem about all candidate pools.

**Leak-regime census, fixed before any scoring.** Every window was classified by whether the leaked
threshold changed the padded context ids: NULL 2, PERMUTATION 4, CONTENT 8. Slot 0 was identical in
14 of 14 windows, as the source requires — `sorted_frames[0]` is appended before the threshold loop
and never reads the threshold, so the leak cannot move the ray-reference camera.

**Repair window manifest.** Full 14-window accounting in `REPAIR_WINDOW_MANIFEST_20260918.md`:
4 no-op controls + 10 duplication-affected, of which 8 repaired and scored and 2 excluded for
having no replacement candidate. The 8 repaired windows are **not** the same set as the 8 CONTENT
windows of the leak census; they differ in four entries.

---

## 5. Results and validity checks

All contrasts signed, window-level, seeds folded first.

### 5.1 Context configuration contrasts (n = 14 windows)

| contrast | mean | SD | positive |
|---|---|---|---|
| `memory_nms_off` − `static` | **+0.242 dB** | 1.270 | 8/14 |
| `memory_nms_on_clean` − `static` | **−0.485 dB** | 1.489 | 6/14 |
| `memory_nms_on_clean` − `memory_nms_off` | **−0.726 dB** | 1.210 | 5/14 |
| `memory_nms_on_clean` − `memory_nms_on` (leaked) | +0.245 dB | 0.711 | 6/14 |

Median of the first row is +0.385 dB; range −2.073 to +2.055.

Absolute arm means, **restricted to the same 14-window paired set** (14 windows x 2 seeds = 28
executions per arm), so that differences of the absolute means reproduce the paired contrasts
exactly:

| arm | executions | mean PSNR | SD across windows |
|---|---|---|---|
| `memory_nms_off` | 28 | **14.637 dB** | 1.718 |
| `static` | 28 | **14.395 dB** | 1.558 |
| `memory_nms_on_clean` | 28 | **13.911 dB** | 1.838 |
| `memory_nms_on` (leaked) | 28 | **13.666 dB** | 1.789 |

Check: 14.637 − 14.395 = +0.242; 13.911 − 14.395 = −0.485; 13.911 − 14.637 = −0.726;
13.911 − 13.666 = +0.245. Each matches the corresponding paired contrast above.

The `static` arm was also generated for two further windows (window start 0 in each sequence) where
retrieval terminates with a failure, so no memory arm exists to pair with. Its mean over all 32
executions is 14.560 dB. **That figure appears here only to document the wider generation set; it
must not be differenced against any arm measured on the 14-window panel**, because the window sets
differ. All contrasts in this report use the 14-window paired set.

### 5.2 Leak effect, stratified by the pre-fixed census

| stratum | n windows | `clean − leaked` | SD |
|---|---|---|---|
| NULL (identical selection) | 2 | **+0.000 dB** | 0.000 |
| PERMUTATION (same multiset, different order) | 4 | **−0.015 dB** | 0.015 |
| CONTENT (different multiset) | 8 | **+0.436 dB** | 0.917 |

### 5.3 Repair arms (n = 8 of 10 duplication-affected windows)

| contrast | mean | SD | positive |
|---|---|---|---|
| `inplace` − `memory_nms_off` | **−0.016 dB** | 0.309 | 3/8 |
| `refill` − `memory_nms_off` | −0.032 dB | 0.304 | 3/8 |
| `inplace` − `refill` (pure order) | +0.016 dB | 0.037 | 5/8 |

These three are algebraically linked: (−0.016) − (−0.032) = +0.016 up to rounding. The order
comparison is **not** independent confirmation of the other two.

### 5.4 Validity checks, with their exact coverage

- **Order-invariance gate** (job 595599, zero diffusion). The name refers to invariance of the
  **retrieval selection** to the order in which arms are executed. It says nothing about whether
  generated output is invariant to context slot order, which is a different question addressed in
  §5.2. The generation worker's own isolation routine makes the effective threshold, the ordered
  frame ids and the padding multiplicities equal between "clean arm alone" and "other arm first,
  then isolate, then clean arm". 11/11 checks,
  **including a non-vacuity assertion** that the test can detect the contaminated ordering it
  guards against. Covers 3 windows of scene_13.
- **Disabled-branch threshold independence** (job 595625, zero diffusion): forcing
  `initial_threshold` to the primed percentile, 1e8, 1e-9, 0.0, and deleting it, leaves the
  NMS-disabled selection unchanged. 6/6 windows. Deleting does not raise, because the disabled
  branch assigns before reading — which is also why it is the leak source.
- **NULL byte-identity gate**: **4 window-seed executions** (2 NULL windows × 2 seeds). All
  sha256-identical between the clean and leaked arms. This is what made reuse of sealed outputs
  admissible instead of regenerating them.
- **No-op byte-identity gate**: **8 window-seed executions** (4 unaffected windows × 2 seeds). All
  sha256-identical to the sealed shipped output.
- **Seal verification**: all 28 new outputs and all 88 sealed outputs re-hashed and matched before
  any target RGB was opened.
- **Historical linkage**: the contaminated ordering was reproduced 28/28 byte-identically against
  the sealed run, and the census independently reproduced the sealed leaked selections
  frame-for-frame.

Each gate certifies exactly the cases it covers and nothing beyond them.

Window-seed level results are in `S113_SCORES.json` and `SLOT_REPAIR_SCORES.json`.

---

## 6. Interpreting the failed repair

Three distinct claims must be kept apart.

**The cause of three-distinct-frame delivery is established.** With NMS disabled the selection is
seeded with `sorted_frames[0]` (the surfel-nearest candidate) and then `len(self.c2ws) - 1` (the
most recent stored frame). **In 10 of the 14 evaluated forward-extrapolation windows those two
coincide.** When it occurs, the duplicated index counts toward the requested context length, so the
fill step cannot recover the slot and only three distinct frames reach four slots. Forward
extrapolation is the setting in which this was observed; it is **not** shown to be a sufficient
condition, since four of the fourteen forward-extrapolation windows do not exhibit it. It is
visible directly in the ranked indices: `[11,11,10,9]`, index 11 being simultaneously the nearest
candidate and the most recent frame. This is a source-level implementation diagnosis, supported by
source and metadata.

**Whether repairing it improves PSNR was tested and the answer did not meet the criterion.**
−0.016 dB over 8 of 10 affected windows.

**Whether repeated information actively harms generation was not tested and cannot be answered
here.** That would require an absent-slot control `(a, −, b, c)` with a genuinely absent context
slot and everything else preserved. Under a four-frame selection-only intervention that leaves the
conditioning interface untouched, no such control exists: a blank image is still an input, any
other existing image changes multiplicity, and removing a slot changes sequence length and target
placement. No substitute was attempted and none is claimed.

**Why a near-zero mean is not a near-zero effect.** With mean −0.016 dB and SD 0.309 over 8
windows, per-window effects of a few tenths of a dB in both directions cancel. Similar PSNR values
also do not imply similar images: two outputs can have comparable error against the target while
differing from each other. Only the byte-identity gates establish exact sameness, and only for the
cases they cover.

**Why the interventions do not identify a distance-sensitivity mechanism.** All three figures below
are signed differences, not magnitudes. Reordering a multiset: **−0.015 dB** (4 windows, clean minus
leaked). Replacing a duplicate with the next ranked nearby frame: **−0.016 dB** (8 windows, in-place
minus movement-path). The NMS policy contrast: **−0.726 dB** (14 windows, clean NMS-on minus
movement-path). Those three have
different interventions, different comparison arms and different window sets, and "same multiset",
"nearby frame" and "distant frame" are not three levels of a controlled variable — a larger frame
index separation does not establish a proportionally larger change in pose, visible content, or the
conditioning tensors. A competing explanation, that this is simply a monotone response to larger
input perturbation, is not excluded. **The defensible statement is only that the tested NMS policy
produced a larger negative mean contrast than the other tested interventions, each on its own
window set.**

---

## 7. Relation to prior work, and limitations

Read at primary source on 2026-09-18; local copies retained. Each of the following occupies a claim
this project might otherwise have made, and each is therefore recorded as a reason **not** to claim
novelty.

- **VRAG** (arXiv:2505.21996v4): *"The History Buffer method performs poorly, with an SSIM score of
  0.188, indicating that naive historical frame retrieval without effective in-context training
  fails to maintain long-term consistency."* Occupies "historical retrieval need not beat
  recent-window conditioning". Its own 300-frame table is not uniformly negative across metrics, so
  it must not be cited as a blanket negative.
- **Context as Memory** (arXiv:2506.03141): context-selection ablation, Random 17.70/17.07,
  FOV+Random 19.17/17.47, FOV+Non-adj 20.11/18.19. A published redundancy-selection ablation in the
  same units used here.
- **RAGME** (arXiv:2504.06672): named deduplication of near-duplicate retrieved videos in
  retrieval-augmented video generation.
- **LongLive-RAG** (arXiv:2606.02553): retrieval collapsing toward temporally local neighbours, with
  a loss that suppresses redundant local similarity.
- **COVRAG** (arXiv:2606.02479): finer geometric evidence with independent selection (MEt3R 0.149,
  LPIPS 0.210) is worse than coarser evidence with independent selection (0.141, 0.198); residual
  selection recovers it (0.100, 0.156).
Two further sources, **PRoPE** (arXiv:2507.10496) on camera reference-frame dependence and **TTAB**
(arXiv:2306.03536, ICML 2023) on episodic versus accumulated evaluation state, closed two directions
that were considered and abandoned before the repair experiment. They are recorded in §A4 rather
than here, because they bear on why other directions were not pursued, not on the result above.

**Relation to VMem's own evaluation.** The paper describes non-maximum suppression as part of its
method: *"To avoid oversampling repeatedly visited regions, we apply a non-maximum suppression
algorithm that reduces redundancy in memory and promotes broader scene coverage among the top-K."*
Its memory demonstration is §4.3, *"Long-term view generation with revisitations"*; its K=4 selector
ablation reports temporal selection at 7.52 dB against VMem at 14.82 dB. **This report's panel
contains no revisitation: every target lies beyond the end of the conditioning bank. This work
therefore does not reproduce, test, or contradict that experiment, and no absolute score from this
panel is comparable with one from it.**

**Limitations.** One consumer cannot establish prevalence across a model family. One dependency
group cannot establish an average effect across environments. Exposed sequences cannot later serve
as untouched validation. Additional seeds, windows or replays would supply no independent scenes and
would not widen the metric's scope. PSNR contrasts establish RGB prediction-error differences under
the stated conditions and nothing about perceived realism, long-horizon scene consistency, or world
model usefulness.

---

## 8. Corrections, disposition, and artifact index

### Corrections made during this work, all retained in the record

1. **A contaminated arm was interpreted as a memory result.** The sealed NMS-enabled arm ran under a
   threshold inherited from a preceding NMS-disabled call. Its −0.729 dB figure was withdrawn as an
   estimate of the independently initialised effect and replaced by `memory_nms_on_clean` at
   −0.485 dB. The original number is retained as the result of a specified order-dependent
   execution.
2. **A positive mean was described with the wrong sign.** The +0.242 dB contrast was written as
   "does not beat fixed-offset context" and "a bounded negative result". Both retracted; correction
   notices are attached to the affected files.
3. **Inferential statistics were reported for a finite panel.** SE 0.340 and t 0.71 withdrawn; SD
   retained as heterogeneity only.
4. **"Held-out" was used for exposed sequences.** Narrowed throughout.
5. **The release's call graph was traced by parameter name rather than by function name.** This
   produced four false claims — that every released call disables NMS, that the config default is
   unreachable, that NMS-on is not shipped behaviour, and that the leak belongs only to comparative
   harnesses. All four are retracted; §3 gives the complete three-site call graph. The procedural
   lesson is recorded in `RESEARCH_PRINCIPLES.md`: a parameter-name search finds only the sites that
   override it, and the count of overrides is never the count of call sites.
6. **A repair mapping mixed a content change with a position change.** The `refill` arm was retained
   and reported, and the in-place arm was added and made primary, with the specification fixed
   before scoring.
7. **A repair denominator was stated without its exclusions.** Corrected to "8 of 10
   duplication-affected windows", with the 2 exclusions and their structural reason documented.

### Disposition

The research branch is closed. No further generation is planned. No novelty claim is supportable
from this work and none is made. `new_method_validated` remains `false`;
`novelty_authorization` remains `NONE`.

An open question to the upstream authors is prepared but **not sent**: whether the per-action
retrieval setting in `navigation.py` is intentional, and which entry point and configuration
produced the selector ablation. It is phrased as a question, scoped to the exact commit and files
inspected, carries no inference about intent, and does not attach this project's measurements.

### Artifact index

| artifact | path |
|---|---|
| Authoritative results | `docs/RETRIEVAL_ARMS_RESULT_20260918.md` |
| Entry-path correction | `docs/ENTRY_PATH_CORRECTION_20260918.md` |
| Leak attribution (superseded, annotated) | `docs/LEAK_ATTRIBUTION_AND_ENTRY_PATH_20260918.md` |
| Earlier results draft (superseded, annotated) | `docs/UNCONTAMINATED_RETRIEVAL_RESULT_20260918.md` |
| Repair specification (pre-scoring) | `work/S103_selector_free_baseline/REPAIR_SPEC_PREDECLARED_20260918.md` |
| Repair window manifest | `work/S103_selector_free_baseline/REPAIR_WINDOW_MANIFEST_20260918.md` |
| Innovation register, primary-source pass | `work/agents/INNOVATION_REGISTER_20260918_PRIMARY_SOURCE.md` |
| Order-invariance gate | `arm_state_isolation_test.py` → job 595599 |
| Leak-regime census | `leak_regime_census.py` → job 595614 |
| Disabled-branch independence | `nms_off_threshold_independence.py` → job 595625 |
| Clean NMS-on generator | `nms_on_clean_s113.py` → job 595887 |
| Repair arms | `slot_utilisation_control.py` → 595891; `slot_repair_inplace.py` → 595902 |
| Scorers | `score_s113.py`, `score_repair.py` |
| Scores | `S113_SCORES.json`, `SLOT_REPAIR_SCORES.json` |
| Literature copies | SuperPOD `/home/yliutz/gwm_litread_20260918/` |

---

# Appendices

## A1. The 14-window table

Window means in dB (the two seeds of a window averaged first). `distinct` is the number of distinct
frames the shipped movement-path retrieval delivered into the four context slots.

| scene | window | static | nms_off | nms_on (leaked) | nms_on (clean) | inplace | refill | distinct | repair status |
|---|---|---|---|---|---|---|---|---|---|
| scene_13 | w050 | 13.027 | 15.082 | 12.485 | 15.066 | 15.075 | 15.066 | 3 | repaired |
| scene_13 | w100 | 15.077 | 16.115 | 12.374 | 12.131 | — | 16.115 | 4 | no-op control |
| scene_13 | w150 | 11.390 | 11.895 | 11.106 | 11.107 | — | 11.895 | 4 | no-op control |
| scene_13 | w200 | 15.379 | 13.807 | 13.789 | 13.789 | — | — | 3 | not instantiable (§A2) |
| scene_13 | w250 | 14.791 | 15.338 | 14.064 | 14.822 | 14.844 | 14.820 | 3 | repaired |
| scene_13 | w300 | 17.155 | 17.025 | 15.462 | 15.433 | 17.208 | 17.210 | 3 | repaired |
| scene_13 | w350 | 15.419 | 15.071 | 13.136 | 13.318 | 15.307 | 15.320 | 3 | repaired |
| scene_14 | w050 | 14.524 | 14.788 | 14.233 | 14.420 | 14.447 | 14.404 | 3 | repaired |
| scene_14 | w100 | 14.969 | 16.622 | 16.641 | 16.641 | — | — | 3 | not instantiable (§A2) |
| scene_14 | w150 | 11.695 | 13.669 | 11.770 | 11.765 | — | 13.669 | 4 | no-op control |
| scene_14 | w200 | 15.292 | 16.270 | 16.256 | 16.417 | — | 16.270 | 4 | no-op control |
| scene_14 | w250 | 15.236 | 14.832 | 15.434 | 15.335 | 14.687 | 14.722 | 3 | repaired |
| scene_14 | w300 | 14.289 | 13.187 | 13.259 | 13.230 | 13.185 | 13.170 | 3 | repaired |
| scene_14 | w350 | 13.290 | 11.217 | 11.315 | 11.274 | 11.663 | 11.578 | 3 | repaired |
| **mean** | | **14.395** | **14.637** | **13.666** | **13.911** | | | | |

The `refill` column is present in the four no-op windows because that arm generated them as its
byte-identity control; `inplace` skipped them by design, and the sealed shipped output is the
control for both. In the two windows of §A2 neither repair arm could be instantiated.

Where a leaked and a clean value are identical to three decimals (w200 scene_13, w100 scene_14)
the two arms received byte-identical input: these are the NULL-stratum windows, and their outputs
are sha256-identical, not merely close.

## A2. The two windows where the repair could not be instantiated

The candidate list is read from the pipeline by requesting a longer selection. In these two windows
the request returns four entries no matter how many are asked for, and those four hold three
distinct frames, so the prespecified policy supplies no fourth distinct candidate.

**scene_13 w200** — bank `[200, 205, …, 255]`, shipped context `[255, 255, 250, 245]`, duplicate at
slot 1, replacement candidates `[]`.

| requested | returned indices | frames | distinct |
|---|---|---|---|
| 5 | `[11, 11, 10, 9]` | `[255, 255, 250, 245]` | 3 |
| 6 | `[11, 11, 10, 9]` | `[255, 255, 250, 245]` | 3 |
| 7 | `[11, 11, 10, 9]` | `[255, 255, 250, 245]` | 3 |

**scene_14 w100** — bank `[100, 105, …, 155]`, shipped context `[155, 155, 150, 145]`, duplicate at
slot 1, replacement candidates `[]`.

| requested | returned indices | frames | distinct |
|---|---|---|---|
| 5 | `[11, 11, 10, 9]` | `[155, 155, 150, 145]` | 3 |
| 6 | `[11, 11, 10, 9]` | `[155, 155, 150, 145]` | 3 |
| 7 | `[11, 11, 10, 9]` | `[155, 155, 150, 145]` | 3 |

This records how the "no candidate" determination arose. It establishes that the intervention as
specified has nothing to insert; it does **not** establish that no fourth frame could ever be useful
in these windows under a different design.

For contrast, a repairable window (scene_13 w050) returns a list that does extend:
`[11,11,10,9,8] ⊂ [11,11,10,9,8,3] ⊂ [11,11,10,9,8,3,4]` at requests 5, 6, 7.

## A3. Run configuration

| item | value |
|---|---|
| upstream repository | `runjiali-rl/vmem`, public HEAD `39291e4f272f6b4f270691d930926ab5930f942e` (2025-07-25) |
| `navigation.py` | sha256 `6d267365d5dcccf9f7cd6d535f19f80521f60a9634dffb35b9af398407389fcf` (byte-identical to public HEAD) |
| `modeling/pipeline.py` | sha256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e` |
| `app.py` | sha256 `02144b511a89c5619a380b0d08e2f62ce0946d7185046d4fd035d9caad28cc31` |
| `configs/inference/inference.yaml` | sha256 `8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3` |
| local patches to upstream | none |
| `vmem_weights.pth` | sha256 `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` |
| `cut3r_512_dpt_4_64.pth` | sha256 `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` |
| `open_clip_model.safetensors` | sha256 `0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5` |
| `diffusion_pytorch_model.safetensors` | sha256 `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815` |
| VAE `config.json` | sha256 `92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e` |
| container | `docker://nvidia/cuda@sha256:63a18dd805367dacfb077aeced8384ab2fb569598ec5f5f5220c3f90a5c23650`, SIF sha256 `5a79221373914393c844cc92c32c89e722003591431f3545fc674c0739c59dd0` |
| apptainer flags | `--nv --containall --no-home --cleanenv`, read-only binds, offline HF/transformers |
| hardware | HKUST SuperPOD, 1 × H800 per job |
| sampler | `create_samplers(guider_types=1, …)` over `DDPMDiscretization`, `DiscreteDenoiser(num_idx=1000)` |
| diffusion steps | 50 (`inference_num_steps`) |
| guidance | `cfg = 2.0`, `cfg_min = 1.2` |
| frames per forward | 8 = 4 context + 4 target, `input_masks = [T,T,T,T,F,F,F,F]` |
| resolution | 576 × 576, latent C = 4 |
| dtype | fp32 parameters with CUDA autocast (upstream default) |
| `context_num_frames` | 4 (native); 5/6/7 used **only** for the zero-diffusion candidate-list read of §4 |
| `use_non_maximum_suppression` | config `true`; effective value per arm as recorded in §4 |
| seeds | 42 and 7, set on `random`, `numpy`, `torch`, `torch.cuda` before each generation |
| threads | `torch.set_num_threads(8)`, `set_num_interop_threads(1)` |

## A4. Directions closed before the repair experiment

Recorded because they explain why other lines were not pursued, not because they bear on the result.

- **Camera reference-frame dependence.** PRoPE (arXiv:2507.10496): *"sensitive to the arbitrary
  choice of reference frame, which can hinder generalization."* Independently, the selector's own
  source shows `sorted_frames[0]` is appended before the threshold loop and never reads the
  threshold, and slot 0 was identical in 14 of 14 windows, so the state leak provably cannot move
  the ray-reference camera. The direction was dead on both counts.
- **Evaluation state and resetting.** TTAB (arXiv:2306.03536, ICML 2023) distinguishes episodic
  adaptation from accumulated state. State isolation therefore remains a necessary control in this
  work, not a contribution.
- **Source-conflict and future-geometry selection candidates** (project-internal, `SOCF-A`,
  `FGB-SI`) were stopped before execution: they proposed selection policies before anything was
  established about what the consumer responds to.

## A5. Project governance flags

`new_method_validated = false`. `novelty_authorization = NONE`. No statement in this report claims
human approval for a method, a novelty finding, or a release. The sequences used are exposed
development data; their target frames are excluded from conditioning but the sequences are not
independent held-out evaluation data.

## A6. Delivery bundle

Accompanying `bundle/`, so that any number in this report can be traced without entering the
working tree:

| file | content |
|---|---|
| `S113_SCORES.json` | per window-seed scores, all four context arms, seal verification, NULL byte-identity record, leak strata |
| `SLOT_REPAIR_SCORES.json` | per window-seed scores for both repair arms, no-op byte-identity record, verdict |
| `LEAK_REGIME_CENSUS.json` | pre-scoring window classification and per-window selections |
| `SLOT_CONTROL_RECEIPT_inplace.json` | in-place arm receipt: candidate provenance checks, repair mapping, output sha256 |
| `SLOT_CONTROL_RECEIPT_refill.json` | refill arm receipt, same fields |
| `NMS_ON_CLEAN_RECEIPT.json` | clean-arm receipt, isolation assertions, threshold recorded at selection |
| `NMS_RECEIPT.json` | sealed three-arm run receipt (job 594957) |
| `REPAIR_SPEC_PREDECLARED_20260918.md` | the repair specification, fixed before any repair output was scored |
| `REPAIR_WINDOW_MANIFEST_20260918.md` | the 14-window accounting |
| `WEIGHTS_SHA256.txt` | checkpoint hashes as listed in §A3 |
| `MANIFEST.sha256` | sha256 of every file above; verify with `shasum -a 256 -c MANIFEST.sha256` |

The JSON receipts and score files were produced on the cluster and copied without modification;
each was confirmed byte-identical to its cluster original on transfer.

---

## 9. Addendum, 2026-09-18: post-hoc target-wise scoring note

Added after the report was finalized. It does not alter the primary results, the prespecified
scoring rule, or the decision to close the duplicate-slot repair branch.

**Post-hoc target-wise analysis.** At target offsets +60, +75, +90, and +105, the mean framewise
PSNR contrasts for NMS-off minus fixed-offset context were +2.950, +0.398, −0.180, and −0.321 dB,
respectively, with seeds averaged within windows. Their arithmetic mean is +0.712 dB. This uses a
different aggregation from the prespecified four-frame pooled-MSE PSNR contrast of +0.242 dB and is
not its additive decomposition. The profile is descriptive and does not isolate temporal distance,
target-slot position, or context clustering as a cause.

The two aggregations differ because the prespecified score pools MSE across the four targets before
taking one PSNR, whereas the framewise figures take one PSNR per target and average. The resulting
gap is non-negative and **arm-dependent** — measured here as +0.227 dB for the fixed-offset arm and
+0.697 dB for the NMS-off arm — so contrasts computed under the two aggregations are not
interchangeable. **§5 remains the primary result and its scoring rule is unchanged.**
