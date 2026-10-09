# R48 corrections to the R47 source-boundary contract

Date: 2026-09-24 (Asia/Shanghai)

Status: **prepared for owner review; not yet accepted for execution**.

This addendum records the corrections required by the dedicated R48 hostile review. It
does not run a fixture, read a real-data score, mutate a receipt, submit Slurm/GPU work,
or change validation flags.

## 1. Split H2 into two claims

* **H2-source:** the CUT3R source helper and optimizer algebra are internally consistent
  for an explicitly labelled synthetic pointmap frame. Required evidence is the source
  hash, line-level provenance, and a synthetic identity receipt.
* **H2-model-boundary:** the learned pointmap emitted at the CUT3R/VMem boundary has the
  declared frame. Required evidence is a producer field such as
  `pointmap_frame=optical_cv` or `pointmap_frame=vmem_gl`, plus a CPU-checkable boundary
  artifact containing a known pointmap, known c2w, and expected world point after the
  exact boundary operation. If this evidence is unavailable, the result is
  `H2_UNIDENTIFIABLE`; no candidate is selected from C8 scores.

H1 remains the separate evaluator-map algebra question. A passing H1 fixture does not
provide evidence for H2.

## 2. Freeze conventions before real-data access

The source/synthetic stage must freeze H1/H2 candidate transforms, K, crop, principal
point, units, rounding, and tolerance. Scene_13 may estimate only one positive metric
scale `lambda` after this freeze. It cannot select a transform, intrinsic, crop, unit, or
tolerance by comparing exposed target values.

The declared split is immutable: scene_13, all seven starts, is calibration; scene_14,
all seven starts, is analysis-held-out development. Both scenes are exposed C8 development
data. Scene_14 is not blind, independent, unseen, or a generalization test.

## 3. Denominators and stop rule

For every target `t`, define `N_ray(t)` as the finite positive own-ray pairs before depth
tolerance. Depth consistency is the count satisfying the frozen tolerance divided by
`N_ray(t)`; `N_ray(t)=0` is `UNTESTABLE_NO_RAY`, never zero. Keep `N_eval(t)` separate for
J/J_own/J_cos and report the correlation count. Do not clip or winsorize the calibration
median; report `N_cal_ray`.

## 4. Owner acceptance criteria

The addendum is accepted only when the owner confirms the two H2 evidence requirements,
the predeclared split, the source/synthetic freeze, and the denominator semantics. Until
then the next action is review only. Even after acceptance, the first permitted execution
is the fixture-only CPU check; real-data C8 re-score, GPU/Slurm, S103, S132, and GRC remain
blocked until the fixture receipt passes.

Unchanged declarations: `new_method_validated=false`, `novelty_authorization=NONE`.
