# C8 pose-convention audit for job 609623

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only audit of the existing C8 receipt and evaluator; no GPU, no new
data, no re-scoring, and no validation-flag change.  
Status remains `new_method_validated=false`; `novelty_authorization=NONE`.

## Finding

The low `J` result in the frozen C8 mask receipt is not interpretable under the
current evaluator because the render and the CPU projection use different camera
axis conventions. This is a proven evaluator defect; it does not by itself prove
that upstream CUT3R map construction is correct.

The C8 producer records `render_c2w_transformed = render_c2w_dataset @ D`, with
`D = diag(1,-1,-1,1)`.  This is exactly the pinned VMem transform:

* `vendor/vmem_snapshot/modeling/pipeline.py:get_transformed_c2ws` flips c2w
  columns 1 and 2;
* `work/S130_C8_diagnostics/run_support_retrieval_v2.py` passes that transformed
  pose to `render_surfels_to_image` and stores both poses in each window receipt.

The independent evaluator then back-projects target depth with the raw dataset
pose and projects into the retrieval map with the raw pose:

* `compute_support_masks.py` builds `Xw` from `Tt` (the dataset pose);
* it computes `pa = (Xw - Ta[:3,3]) @ Ta[:3,:3]`;
* `retrieval_hits` treats `pa` as the camera point for a map rendered with
  `Ta @ D`.

For the same world point, the transformed render camera coordinates are
`p_v = p_opt @ diag(1,-1,-1)`, while the evaluator supplies the unflipped `p_opt`.
Thus the evaluator sends the render a point in the wrong y/z frame.  This is a deterministic algebraic
mismatch, independent of model quality or physical support.

A separate producer-side risk remains: the retrieval producer passes
`dataset_c2w @ D` into CUT3R, while the adapter contract describes this
right-multiplication as VMem-input-only and CUT3R's depth unprojection uses optical
x-right/y-down/z-forward coordinates. This is a hypothesis requiring a CPU/source
replay; it must not be silently fixed or merged with the proven evaluator defect.

## Evidence checks

The local receipt audit checked all 56 render records in
`remote_support_609623/C8_SUPPORT_RETRIEVAL_RECEIPT.json`:

* every stored transformed pose equals `dataset_pose @ D` exactly (maximum
  absolute error `0.0`);
* a direct rigid-pose calculation gives `p_v = p_opt @ D[:3,:3]`, confirming the
  required y/z flip.

The C8 receipt and mask values remain unchanged.  The observed values are still
`B=0.755--0.984`, high `C`, and `J=0--0.092` with only 3/14 pose checks passing;
this audit explains why the last quantity cannot be used as a physical indexing
diagnosis. The producer-side hypothesis remains unresolved.

## Decision and next action

1. Keep C8 `J` labelled `UNINTERPRETABLE_POSE_CONVENTION`; do not reinterpret it
   as missing surfel support, hidden-surface scarcity, or a method failure.
2. Do not patch or rerun the frozen C8 evaluator retroactively.  A corrected
   projection is a new, owner-reviewed CPU contract and must use the transformed
   pose consistently for both map rendering and point projection, with an
   independent synthetic identity test and a scale check.
3. Audit the producer-side `dataset_c2w @ D` to CUT3R path separately with a
   no-GPU synthetic/source replay. Compare the documented optical-pose path and
   the transformed-pose path; keep this upstream hypothesis separate from the
   evaluator correction.
4. Keep RCA and BRD closed for the current support-driven VMem pipeline. DCR can
   remain only a conditional benchmark-setting candidate until that new contract
   passes.
5. No S103 baseline, same-pool control, adapter, diffusion, or formal GRC is
   authorized by this finding.

## Rejection condition

If a convention-consistent CPU recalculation still cannot establish a common
metric scale and an independent pose/render identity check, stop the
hidden-surface method search and report the evaluation infrastructure limitation.
