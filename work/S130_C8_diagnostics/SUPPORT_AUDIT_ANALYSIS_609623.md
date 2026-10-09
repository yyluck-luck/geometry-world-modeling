# C8 support audit analysis — job 609623

Date: 2026-09-24 (Asia/Shanghai)  
Scope: 14 development windows, scenes 13/14, four target frames per window.  
Remote job: 609623, dgx-45, exit 0:0, `MAPS_COMPLETE_NO_DIFFUSION`.  
Validation flags: `new_method_validated=false`; `novelty_authorization=NONE`.

## Evidence

* Retrieval receipt: `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json`.
* CPU mask receipt: `work/S130_C8_diagnostics/remote_support_609623/C8_SUPPORT_MASKS.json`.
* All 14 harness gates are true (`gate_ok=14/14`); all 56 target maps are present.
* The CPU evaluator used target depth only after the GPU process completed, as required by
  the C8 isolation contract.

## Observed support fractions

Across the 14 windows:

* `B` (visible in at least one of the 12 bank frames) ranges from 0.755 to 0.984;
  mean is 0.888. No window has `B < 0.20`.
* `C` (visible in the four delivered context frames) is high in every arm/window. The
  primary clean arm ranges from 0.491 to 0.972; no window has `B >= 0.50` and primary
  `C < 0.20`.
* `J` (VMem averaged-render surfel/depth hit) is 0.000 to 0.092 in all windows; all
  14 windows satisfy `B >= 0.50` and `J < 0.20`.

## Interpretability check

The preregistered pose-convention check requires, per window, median own-render depth
correlation at least 0.5 and `J_own_ray` at least 0.20. Only 3/14 windows satisfy both;
the overall median per-target depth correlation is about 0.190. Several windows have
retrieval-depth / projected-depth ratios in the hundreds, so `J` cannot be treated as a
valid physical indexing diagnosis for this panel. The low `J` is therefore
`UNINTERPRETABLE_POSE_CONVENTION`, pending a separate convention/scale audit.

## Decision under the frozen C8 contract

The physical-support scarcity premise is **not supported** on this panel: bank and delivered
context support are high. The result does not validate a hidden-surface predictor, RCA, or BRD.
It redirects the next action to a read-only harness convention/scale/indexing audit. Do not
run a geometry-completion adapter or a new GPU method pilot from this result.

RCA and BRD remain design hypotheses only and are currently blocked by the support gate. DCR
is a possible evaluation setting, not an authorized method. If a later convention audit makes
J interpretable, update this decision from the new evidence rather than retrofitting this one.
