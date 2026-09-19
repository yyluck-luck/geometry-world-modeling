# S48 V6 fresh independent statistical / causal / implementation review

- Review role: fresh non-author review
- Review time: `2026-09-08T09:45:01.682354+00:00` / `2026-09-08T17:45:01.682354+08:00`
- Verdict: **BLOCKED**
- Severity: **3 CRITICAL, 4 MAJOR, 2 MINOR**
- Execution authorization after this review: **NONE**
- Novelty authorization after this review: **NONE**
- Next gate: revise and freeze a new source-only package, then obtain fresh non-author review of the new exact hashes. V6 must not be used to create G7, an arm, or a model run.

## 1. Exact reviewed source set

The four files were hashed before the review and again after both interpreter runs. The values were unchanged and exactly matched the requested frozen set.

| Role | File | Exact SHA-256 |
|---|---|---|
| draft | `S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md` | `6611d5f803740207fcfcec44eae8f756076f0763cb3eff8349fe1065905c03a0` |
| normative spec | `S48_NORMATIVE_ANALYSIS_SPEC_V2.md` | `29014cf8504a5b91040e96074c6d6edf47038814f230cb8d62e5822998d19d2f` |
| reference implementation | `s48_analysis_reference_v2.py` | `af6079dcce32af12b6bd0240e73fce2bae2e7aaeb39fa90dfcf1c99e9b7a5189` |
| tests | `test_s48_analysis_reference_v2.py` | `d05110ab6665eed6912b1ddfd07a00f99490b29d99cd63322d6326a81187c89c` |

This review did not read C1/C2 payloads or image bytes, did not import or run a model, did not create prepare/attach/authorization/execution artifacts, and did not create an S48 arm. All counterexamples used newly constructed in-memory arrays and typed objects.

## 2. Independent execution evidence

The exact frozen test script was run directly with isolated import and bytecode writing disabled.

| Interpreter | NumPy | Result | Wall time reported by unittest |
|---|---:|---:|---:|
| CPython `3.13.0` | `2.4.6` | `44/44 PASS` | `16.409 s` |
| CPython `3.12.14` | `2.3.5` | `44/44 PASS` | `17.145 s` |

The deterministic randomized sections exercised 256 zero-edit cases, 256 scaled-integer cases, and 16 native-output effect/loss cases in each interpreter. An initial generic `unittest` module-name invocation did not discover the path and returned an import error; it executed no tests. The direct frozen script invocation above is the valid run.

Passing the supplied tests is insufficient because the following fresh counterexamples exercise untested identity and estimand boundaries.

## 3. Blocking findings

### C1 — CRITICAL: the typed replay receipt cannot carry or derive the Influence replay floor

The normative definition requires

`tau_output = max(1e-6, all six exact-replay full-frame distances for the same seed and target)`

(`S48_NORMATIVE_ANALYSIS_SPEC_V2.md:101-110`). However, `ReplayPairReceipt` contains only `seed`, `target`, indices, and `ArmGuardMetrics` (`s48_analysis_reference_v2.py:715-721`). `GuardFloors` and `replay_guard_floors` contain displacement and guard fields but no full-frame direct-effect mean (`s48_analysis_reference_v2.py:700-713,792-815`). `influence_value` then accepts an unrelated free scalar `replay_floor` (`s48_analysis_reference_v2.py:468-474`). There is no normative function that derives this scalar from the exact six typed pairs or their output hashes.

Fresh synthetic observation in both interpreters:

- six valid typed pair receipts produced valid guard floors;
- the guard-floor type had no full-frame replay-distance field;
- a target effect of `2/255` with the free argument `replay_floor=0` gave `I=0.00784313725490196`, passing `delta_I`;
- using the actual synthetic replay distance `2/255` gave `I=0`, which fails.

Thus the same supposed replay set can support opposite Influence decisions. This also makes `localization_decision(..., influence_passed=True, ...)` forgeable because that function accepts a bare boolean rather than an Influence receipt.

**Kill condition:** V6 cannot pass Influence or advance to Localization.

**Required repair:** define typed replay-instance receipts that bind state/noise/RNG/snapshot, saved-output SHA and output identity; define each canonical pair from two bound instances and include its exact full-frame direct-effect mean; derive `tau_output` inside a single validator; prohibit a caller-supplied replay-floor scalar and bare `influence_passed` boolean.

### C2 — CRITICAL: Localization accepts invented placebo-tail statistics and can reverse an honest failure

`descriptive_tail` can compute a tail from actual masks (`s48_analysis_reference_v2.py:501-510`), but `localization_decision` does not consume those masks or a typed receipt. It accepts two ordinary mappings and only checks their four scalar fields and ranges (`s48_analysis_reference_v2.py:513-569`). It does not verify that:

- `true_mass` equals the mass computed from the current `target_effect` and `support`;
- `count` equals the number of supplied masks;
- `lower_median` and `tail_rank` follow from those masks;
- the rank lies on the exact `(1+k)/(K+1)` lattice;
- the effect, support, generator, and placebo-library identities match the current cell.

Fresh synthetic observation in both interpreters used a raw target effect with computed true-support mass `0.6666666666665556` and 199 honest placebo masks identical to the true support. The honest tail had median `0.6666666666665556`, rank `1.0`, and failed both shape and camera tails. Replacing only the two tail mappings with `{count:199,true_mass:0.99,lower_median:0.01,tail_rank:0.005}` made the same target effect, negative map, and support return `PASS` with no reasons.

The raw-map formula and independent negative veto are numerically repaired relative to V5, but this unbound receipt permits a direct false Localization claim.

**Kill condition:** V6 cannot pass Localization.

**Required repair:** make tail evidence a typed, identity-bound receipt containing the effect-map SHA, true-support SHA, generator/source SHA, exact ordered placebo-mask SHAs and masses. Recompute the count, lower median and tail rank in the decision path, or verify every bound primitive before accepting the receipt. The current effect/support mass must be recomputed and exactly matched.

### C3 — CRITICAL: the reference contract cannot represent the required held-out / never-conditioned fact

The draft says that only a synchronized observation that never entered memory or conditioning can be a reference (`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md:61-64,218-220`). The normative spec and `ReferenceCandidate` omit this fact. The type contains candidate/file/scene/time/camera and downstream numeric receipts, but no memory-roster exclusion, conditioning exclusion, capture identity distinct from target inputs, target-observation SHA, or held-out provenance (`s48_analysis_reference_v2.py:952-963`). `select_reference` therefore has no argument or branch capable of rejecting a candidate that was already stored, conditioned on, or is the target observation itself (`s48_analysis_reference_v2.py:965-1009`). Exact target cameras are deliberately eligible, so target/capture identity must be checked separately.

A synchronized but leaked reference can make both output loss and source ranking spuriously favorable. Numeric camera, identity, view-pair and hole checks cannot restore independence after leakage.

**Kill condition:** V6 cannot identify Benefit, even if every currently implemented reference check passes.

**Required repair:** bind a complete immutable observation roster, target-input roster and memory/conditioning roster; require a typed exclusion receipt proving the selected reference capture/hash is absent from every model input and memory path; bind sensor/capture identity and forbid target-answer reuse. Preserve the complete eligible/excluded flow.

### M1 — MAJOR: replacement eligibility disagrees across the indivisible package and is under-specified

The draft retains same-scene/identity, target-camera alignment, support IoU `>=0.80`, weighted-area ratio `[0.90,1.10]`, same CAL source-quality quartile, common-valid/hole/view-pair requirements, and use of every eligible P (`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md:283-287`). The normative spec omits scene, camera, support-IoU, area-ratio and source-quality eligibility (`S48_NORMATIVE_ANALYSIS_SPEC_V2.md:286-301`). The implementation has only an integer recency predicate, a generic unselected roster, and reinsert-path invariants (`s48_analysis_reference_v2.py:1217-1334`). `ReinsertReceipt` cannot represent scene, candidate camera, support, support IoU, weighted-area ratio, quality metric/quartile, or the complete P inclusion/exclusion decision.

Moreover, “same CAL quartile” names neither the frozen quality metric nor cut points and tie behavior, and the draft does not define binary versus weighted support IoU. Consequently, two conforming executors can choose different P sets after seeing results. The package itself says prose/code/test disagreement is `BLOCKED` (`S48_NORMATIVE_ANALYSIS_SPEC_V2.md:9-13`).

**Kill condition:** no `B_matched` comparison is eligible under V6.

**Required repair:** add one exact replacement-candidate schema and selector covering every draft criterion; specify all formulas, metric identities, CAL split/hash, quartile cut points and boundary/tie rules; return the full ordered inclusion/exclusion flow; bind that flow to every O/P comparison.

### M2 — MAJOR: Benefit signs are numerically correct but do not identify “source beneficial versus harmful”

The implemented signs are internally correct:

- `B_local = loss(edit,R)-loss(zero,R)` favors the original source appearance when positive;
- `B_matched = loss(P,R)-loss(O-reinsert,R)` favors O over P when positive;
- values lie in the declared normalized squared-error domain.

But “zero” is zero **edit dose**, not source omission. `B_local` identifies sensitivity/local preference around the existing selected source. `B_matched` identifies O relative to registered replacements. Neither identifies the effect of source presence versus no source/abstention, and a negative value means the edit or P is better; it does not by itself mean that the source is harmful.

Fresh native-uint8 counterexample in both interpreters used a held-out reference and absent-source output of 0 codes, O at 10 codes on support, and edit/P at 20 codes on support, with identical zero-valued outside pixels. It produced:

- `B_local = B_matched = 0.00461361014994233`, both passing `delta_B=0.001`;
- both outside differences `0`, passing outside noninferiority;
- O was nevertheless worse than the absent-source output by MSE `0.0015378700499807767` on support.

Therefore a future result may be called “registered-comparator-relative preference for the original appearance,” not absolute source Benefit or source helpfulness. The draft's broad RQ3 wording remains unidentified.

**Required repair:** either narrow RQ3, all gates and later claims to the exact comparator-relative estimands, or add a same-path, state-matched source-omission/abstention intervention and freeze how it preserves shape/capacity/position without leaking a new treatment difference.

### M3 — MAJOR: common-valid/hole receipts do not bind the required view roles

The prose requires the exact intersection of a specified O/R or O/R/P view set. `valid_domain_receipt` instead accepts any non-empty mapping of arbitrary labels and stores no role set or mask identities (`s48_analysis_reference_v2.py:1136-1149`). `valid_domain_decision` consequently cannot tell whether O, R, P, or any required warp-valid mask participated (`s48_analysis_reference_v2.py:1152-1175`).

Fresh synthetic observation in both interpreters supplied a single all-valid mask under the arbitrary label `UNRELATED_ONLY`; the receipt returned coverage `1.0`, hole ratio `0.0`, and `PASS`. Such a receipt can be attached to a reference candidate because `select_reference` checks only the two domain labels and the scalar decision.

**Required repair:** store and require the exact role/view set for each analysis, bind each validity-mask SHA and its source pair, and recompute common validity and holes from the bound masks. Apply the same provenance binding to view-pair and identity receipts.

### M4 — MAJOR: sequential conjunction and kill conditions exist only in prose

The draft's S48 strategy is statistically conservative: one development unit, technical repetitions do not increase scientific `n`, no pilot p-value/CI, strict per-cell conjunction, and a separately frozen scene-level S49 confirmation (`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md:327-340`). Those boundaries are appropriate for a kill experiment.

The implementation has no typed cell ledger or stage-transition validator. It does not verify the exact Cartesian product of family/seed/sign/target/replacement, same-state identities, positive controls, source-placebo reporting, all-cell conjunction, order `Influence -> Localization -> Benefit`, or stop-on-first-failure. The exposed APIs accept free scalars/booleans for replay, Influence passage, Benefit and outside loss. A caller can omit a failed sign/target/P or advance out of order without an implementation error.

**Required repair:** add a fail-closed typed experiment-ledger validator that derives each stage from bound lower-level receipts, checks exact registered cell identities and completeness, and emits one terminal action. It must reject missing, duplicate, extra, averaged, mixed-state and out-of-order evidence.

## 4. Non-blocking implementation findings

### N1 — MINOR: `_finite` accepts numeric strings despite the “finite real” contract

`_finite` calls `float(value)` after excluding booleans (`s48_analysis_reference_v2.py:82-91`). Both interpreters therefore accepted `benefit_decision("0.001", "0")` and returned `PASS`, although the spec requires published scalars to be finite reals and says invalid inputs raise `SpecError` (`S48_NORMATIVE_ANALYSIS_SPEC_V2.md:56-58`). One-element arrays and other objects with a permissive float conversion can also cross this boundary.

Use an explicit real-number type check (excluding booleans), then convert and test finiteness. Wrap conversion failures in `SpecError` consistently.

### N2 — MINOR: the draft's frozen test-count statement is stale

The current exact test file executes 44 tests, while the allowed-conclusion sentence says “41 synthetic tests” (`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md:348-350`). This does not change a scientific result, but a frozen package should report the exact count or avoid hard-coding it.

## 5. Focus-area disposition

| Requested check | Disposition | Evidence boundary |
|---|---|---|
| null-output effect | **BLOCKED as a broad source-effect claim** | zero dose is a null edit, not source absence; nonzero effect is post-selection sensitivity to the registered edit. A zero effect does not prove non-use. |
| geometry support represents the correct position | **NOT ASSESSABLE / still gated** | numeric map formulas cannot prove projection correctness. The draft correctly leaves camera/K, renderer, provenance, occlusion and real support construction for G5/G7 and forbids a geometry-correctness claim. |
| natural revisit reference | **BLOCKED** | held-out/non-conditioning identity is absent from the normative type and validator. |
| Benefit sign/domain | **numeric PASS; causal interpretation BLOCKED** | one `/255`, squared-error domain and sign are correct; the broad helpful/harmful estimand is not identified. |
| raw target-map Localization | **formula PASS; decision BLOCKED** | V5's cross-source pixel subtraction is removed and the registered uniform-map counterexample fails, but unbound tail mappings can reverse the result. |
| independent negative veto | **PASS for the finite formula** | negative is not subtracted from the target map; full-effect ratio and same-support `L_area` are independent vetoes. Receipt/state identity still belongs in the future ledger. |
| same-path dose zero | **PASS for the finite adapter** | both signs/families take the same seven-stage API, strict quantization and both consumer tensor hashes. Real CLIP/VAE preprocessors remain explicitly unimplemented. |
| typed replay | **BLOCKED** | pair indices are typed, but the Influence full-frame replay distance and output identities are absent. |
| strict uint8 | **PASS** | saved-output effect, guard and Benefit APIs reject lists, floats and other integer dtypes; native analysis requires `576x576x3`. |
| finite/domain guards | **mostly PASS, one MINOR** | NaN/domain/P95 and validity checks pass; `_finite` still accepts numeric strings. |
| O/P path fairness | **partial PASS, overall BLOCKED** | listed reinsert invariants are fail-closed, but the complete P eligibility contract is absent/inconsistent and receipts are assertions rather than bound process evidence. |
| sequential statistics and kill conditions | **prose PASS, implementation BLOCKED** | development/confirmation separation is sound; no executable completeness/order/terminal validator exists. |

## 6. What survives this review

The following V5 repairs are real within the finite synthetic scope:

1. saved RGB has one strict uint8-to-float normalization and no second division by 255;
2. Localization uses the raw target edit-versus-matched-zero effect map;
3. the negative map is an independent veto and cannot sculpt target Localization;
4. dose zero follows the same finite edit/quantize/consumer path;
5. output and validity inputs are strict arrays with explicit dtypes;
6. guard statistics are direction-symmetric and the four registered gross attacks fail;
7. Benefit arithmetic, signs and numeric domains are internally consistent;
8. listed O/P reinsert invariants and exact integer recency are enforced by their local validators;
9. S48 technical repetitions are not presented as independent scientific samples, and S49 remains a separately frozen confirmation.

These improvements do not close C1-C3 or M1-M4. They establish implementation progress only, with zero real-data, model, quality, causal-effect, Benefit, method-gain, or novelty evidence.

## 7. Required next door

The immediate next door is **V7 source-only repair and fresh review**, not G0/G1 execution and not G7 binding. The new frozen package must, at minimum:

1. derive Influence replay floors from identity-bound replay outputs and exact canonical pairs;
2. derive Localization tail decisions from identity-bound support/effect/placebo masks;
3. encode and prove reference exclusion from every memory/conditioning/target-input path;
4. unify and fully specify the P selector across draft, spec, code and tests;
5. state Benefit as comparator-relative or add a valid source-absence intervention;
6. bind common-valid/view/identity receipts to exact roles and masks;
7. implement the exact cell grid, stage order, conjunction and terminal kill action;
8. reject non-real scalar types and correct the test-count statement.

Any change invalidates all four V6 hashes and this review does not transfer to the new version. Until a new exact source set passes fresh review: model loads `0`, S48 arms `0`, C1/C2 payload/image reads by S48 `0`, execution authorization `NONE`, novelty authorization `NONE`.
