# R106 END-LINE closure audit and reopen criteria

Date: 2026-09-24 (Asia/Shanghai)  
Scope: read-only closure audit. No runner/fixture execution, no GPU/Slurm, no
protected C8/evaluation reads, and no flag or frozen-contract changes.

## Closure finding

**R105 END-LINE is justified now.** The final GSCR/RCA pivot is already covered
by the cited threat set: R39 identifies robust SLAM/data association,
3D-Belief, and INGRID as closest families, while SceneSense/SC-Explorer cover
measured/predicted geometry reconciliation
(`work/agents/CODEX_R39_REDTEAM_PIVOT_20260923.md:43-53`). R105 therefore
changes residual attribution and validation hygiene, not a new generator state
transition (`work/agents/CODEX_R105_FAILURE_DRIVEN_PIVOT_20260924.md:31-42`).

The empirical prerequisite is also missing. R45 records high bank/context
support, only 3/14 pose checks passing, and low `J` as
`UNINTERPRETABLE_POSE_CONVENTION`; it closes RCA/BRD on this panel and says a
CPU routing exercise would be disconnected from the observed VMem failure
(`work/agents/CODEX_R45_SUPPORT_IMPLICATIONS_20260924.md:8-23,42-56`). R46
establishes the evaluator H1 frame mismatch but leaves the upstream CUT3R H2
convention unresolved, allowing DCR only as a benchmark setting
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:7-10,37-54,79-103`).
Finally, R100 finds all owner/H2/fixture artifacts and a supported runner
absent on both roots (`work/agents/CODEX_R100_POST_R99_READINESS_RECHECK_20260924.md:8-30`).
No mechanism can be claimed or fairly tested under these conditions.

## Exact evidence that would reopen a mechanism search

Reopening requires **all** of the following, in one independently reviewed,
content-addressed packet; one item alone is insufficient:

1. **H2 closure:** owner-reviewed `h2_source_manifest`, `h2_packet`, and
   `boundary_artifact` that declare the producer pointmap frame, compare
   `T_cv` and `T_cv F` at the CUT3R boundary, and report finite bidirectional
   identity error `<=1e-6`. A missing or ambiguous packet remains
   `H2_UNIDENTIFIABLE` before scoring.
2. **Convention-controlled support evidence:** the CPU identity fixture passes;
   a frozen transform/depth-unit/intrinsic registry and calibration-held-out
   scale pass; and an independently held-out reveal panel establishes a valid
   hidden-surface or contradiction precondition without selecting conventions
   from target RGB or `J`. This is the R46 contract, not a new method claim.
3. **Mechanism-level distinction:** a source-pinned CPU runner and canonical
   fixture pass the R62 owner gate, computed visibility/hash checks, and
   complete controls. A candidate must beat matched generic/robust controls on
   future RGB/depth while surviving a primary-paper comparison against the
   R39/R40 threat set. A conformance pass alone is not novelty evidence.
4. **Independent review and provenance:** `OWNER_ACCEPTED` identity, exact
   code/fixture/H2 hashes are present and independently checked. Provide the supported CPU command text and discovery evidence for review only. Until the complete packet and every gate are independently accepted, do not execute, dispatch, schedule, or expose the command as runnable. Until then remain
   `NO_COMMAND_AVAILABLE`; do not reinterpret historical C8 numbers.

If any item fails, retain END-LINE and report an infrastructure/evaluation
limitation. These criteria do not authorize GPU work by themselves.

## One cheap falsifier for benchmark-only DCR

Use one CPU-only plane/cube fixture with known `K`, metric depth, and three
known cameras. Render the map using `T_cv F`; back-project a target point with
raw `T_cv`, apply the prescribed `F_3=diag(1,-1,-1)`, and require exact
pixel/depth agreement within the declared tolerance. If the corrected hit set
or depth changes under this analytically equivalent frame conversion, the DCR
benchmark is falsified and must be rejected before any model or C8 replay. This
is the first R46 synthetic identity gate
(`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:68-77`), and its
failure triggers the no-go condition at
`work/agents/CODEX_R46_POSE_CONVENTION_DCR_AUDIT_20260924.md:91-103`.

## Final state

Keep DCR as a conditional benchmark only; do not rename or combine mechanisms.
The hidden-surface method search remains END-LINE until the complete evidence
packet above exists. Preserve `new_method_validated=false`,
`novelty_authorization=NONE`, and `NO_COMMAND_AVAILABLE`.

## R116 wording addendum (2026-09-24)

Provide the supported CPU command **text and discovery evidence for review only**. Until the complete packet and every gate are independently accepted, do not execute, dispatch, schedule, or expose the command as runnable.
