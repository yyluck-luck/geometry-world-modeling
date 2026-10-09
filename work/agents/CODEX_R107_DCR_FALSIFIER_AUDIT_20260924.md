# R107 audit of the R106 DCR falsifier

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only falsifier audit. No fixture execution, no GPU/Slurm, no
protected C8/evaluation reads, and no flag or contract changes.

## Verdict: REVISE once

R106 correctly selected the first cheap gate: a CPU plane/cube identity test
for `T_cv F` and `F_3` before any model or C8 replay
(`work/agents/CODEX_R106_ENDLINE_REOPEN_CRITERIA_20260924.md:57-68`). The
remaining hidden assumption is that one point/one projection implementation
will exercise the full convention. A centered or symmetric fixture can pass
with an incorrect intrinsic, depth-unit, crop, rounding, or even a shared
projection bug. R46 explicitly requires checking units, K mapping, crop,
principal point, focal convention, rounding, and tolerance
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:65-77`).

## One minimal correction

Replace the single-point plane/cube check with one **asymmetric independent
fixture**:

* use off-axis plane/cube points at at least three positive metric depths, three
  cameras with nonzero rotations/translations, and an asymmetric `K`
  (`fx != fy`, noncentral `cx,cy`) plus explicit resolution/crop and
  nearest-even pixel rounding;
* store depth in integer millimetres and decode to metres through the declared
  unit conversion, so a wrong scale fails rather than being absorbed by a
  shared metric convention;
* implement the forward map renderer and evaluator projection independently
  (no shared projection helper), then compare camera-keyed pixel, positive-depth,
  front-facing, nearest-depth/occlusion, and metric-depth records;
* run the prescribed `T_cv F` + `F_3` path and negative controls (raw `T_cv`,
  `F T_cv`, and inverse-pose parsing). Require only the source-supported path
  to match; if two paths match because the fixture is symmetric, return
  `H2_UNIDENTIFIABLE`/reject the benchmark.

This is still a cheap CPU falsifier and remains independent of protected data.
It mirrors R46's synthetic identity, source-boundary, scale, depth-unit, and
intrinsic checks (`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:68-77`)
and the camera-keyed rounded/quantized visibility rules
(`work/agents/CODEX_R56_R54_ORACLE_FREE_CORRECTION_20260924.md:31-37,122-126`).

## Remaining blocker and stop rule

Even after this correction, no DCR benchmark execution is authorized: R100
still reports the owner/H2/fixture/runner packet absent and
`NO_COMMAND_AVAILABLE` (`work/agents/CODEX_R100_POST_R99_READINESS_RECHECK_20260924.md:8-46`).
If the asymmetric independent fixture fails, if depth/K/crop/rounding cannot
be frozen, or if a negative-control transform also passes, reject DCR and keep
END-LINE. If it passes, DCR remains an evaluation setting only; it does not
reopen a mechanism search or alter `new_method_validated=false` or
`novelty_authorization=NONE`.

