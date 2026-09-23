# Method direction — current (updated 2026-09-23)

Status: **no validated method yet.** `new_method_validated=false`, `novelty_authorization=NONE`.
This file is the single up-to-date summary of where method innovation stands. History lives in
`RESEARCH_MEMORY.md`; this file is rewritten, not appended.

## 1. What counts as method innovation here

The bar (accepted from the R30/R31 reviews): under the same legal state-management protocol and the
same evidence, the method must change what the model **predicts** — future views, content that
reappears after occlusion, cross-view geometry. Changing which frames are read or kept does not count.
Diagnostics, bug findings and evaluation fixes are valuable, but they are not method innovation.

## 2. Ruled out (do not revive under a new name)

| Candidate | Why it is out |
|---|---|
| Lineage-aware memory fusion (proposal v2) | For linear fusion at optimal weights the cross-source covariance term adds zero information (numerical check 4.4e-16). |
| Five selection-layer rerankers (A4, A5, A6, A14, A22) | Adjacent to published work; none supports a standalone method paper; they only change which frames are read. |
| Learned write/merge/decay/rollback gate (B4) | Without write-back rights it is a bystander detector; even with them it is state management, not world modelling. |
| "Support scarcity, not selection" as a premise | Not established. The 5.6 dB figure is earliest-vs-recent; spanning beats recency by only 0.383 dB. |

## 3. The convergent candidate method

Three independent sources (codex R34, and two GPT-6 Pro answers) converged on one direction:

> **Predict the geometry of surfaces that are not currently visible, before they are revealed, and
> condition the generator on that prediction.**

Names in the sources: CAGF (context-to-target geometry/appearance field, R34), BLSC (boundary-linked
scene completion, Pro answer 1), Reveal-Event World Modeling (Pro answer 2).

Common core:
- From only the 4 delivered context frames, infer hidden-surface geometry and appearance
  (e.g. which visible surface fragments continue behind an occluder, and when they become visible).
- Render that prediction into the target cameras and inject it through a zero-initialised adapter
  in the VMem denoiser; train the adapter and denoiser LoRA (authorised: F).
- Never write predicted geometry into the measured-evidence memory.

What must be shown for it to count (all three sources insist on the same control):
- It beats a **capacity-matched generic completion / depth-conditioned adapter trained on the same
  data**. Otherwise the gain is just "more geometry input" or "more parameters".
- The gain must appear in **generated RGB geometry** (depth recovered from generated images vs
  reference RGB-D), concentrated on newly revealed regions, not only in an auxiliary head.
- Evaluation on independent held-out scenes (ScanNet++ application still to be started).

Fit with the original proposal: this is the proposal's "persistent geometric context /
geometry-conditioned generation" with "lightweight geometry-aware adaptation".

## 4. Gating diagnostics (running now, owner decision C8, cap 20 H800-hours)

The method is only justified if the failure is really missing support that must be inferred.

| Diagnostic | Question | Outcome that supports the method | Outcome that redirects |
|---|---|---|---|
| Support audit (B/C/J masks) | Is target support absent from the bank (B), absent from the 4 delivered frames (C), or present but not exposed by the surfel index (J)? | Low B on failure regions: true scarcity, prediction is needed | High B low J: fix indexing. High B low C: fix delivery. High C but poor output: consumption problem |
| Slot-0 factor separation | Is the 0.55 / 0.87 dB slot-0 effect due to ray reference, translation scale, or tensor order? | — (controls a confound in all later method comparisons) | If coordinate/scale explains it, every later comparison must fix slot 0 or canonicalise |

Already known from existing data (zero GPU): with the frame set and slot 0 fixed, reordering slots 1-3
changes PSNR by about zero (4 census windows, -0.015 dB; S107 within-group spread <= 0.04 dB).
Slot 0 sets both the Plucker ray reference (`all_w2cs[:1]`) and the global translation scale
(`camera_scale / norm(camera_dists[0])`) in the pinned code.

## 5. Timeline (semester started 2026-09-01)

| Week | Dates | Plan |
|---|---|---|
| 4 | Sep 22-28 | Diagnostics implemented and run; ScanNet++ application started |
| 5 | Sep 29-Oct 5 | Diagnostic results; pick method variant; pilot data |
| 6-9 | Oct 6-Nov 2 | Method pilot vs matched completion control; go/no-go by end of week 7 |
| 10-12 | Nov 3-23 | Evaluation; CVPR 2027 (reg Nov 10, paper Nov 16 AOE) only if week-8 evidence is strong |
| 13-14 | Nov 24-Dec 7 | Report; TMLR as the realistic target |
