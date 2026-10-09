# R150 Hostile Check of the R148 END-LINE Verdict

**Access date:** 2026-09-24  
**Allowed evidence:** R148 and only the primary/official sources cited by R148 (via R142). No broader search, project/protected data, code execution, fixture/runner, GPU, Slurm, receipt, or flag mutation was used.

## Challenge

R148 says that no independent benchmark gap is defensible because camera round trips, frame contracts, same-map query reuse, and reprojection consistency are established components. The hostile question is whether those components measure the failure mode that R140 is intended to expose when a producer's output frame is undocumented or misdeclared.

## One concrete unmeasured failure mode

**False unique certification under a hidden producer frame.** A scorer can report a unique frame-convention pass even though the producer map is in an undocumented canonical or transformed frame, because the scorer only tests the producer-declared convention or lets the map/query branch be regenerated consistently. The correct outcome for an unidentifiable or misdeclared frame should be rejection, not a unique pass.

Define a benchmark estimand for a case with hidden producer frame label `h`:

```
FUP = P(score emits exactly one passing convention | h is wrong,
        undocumented, or outside the declared raw/F3 hypotheses)
```

and its complementary safety quantity:

```
AReject = P(score emits H2_UNIDENTIFIABLE | h is outside the declared hypotheses)
```

These are decision errors about *frame-contract certification*, not camera projection accuracy.

## Why the cited checks do not measure it

- COLMAP `models_test.cc` and PyTorch3D `tests/test_cameras.py` test declared camera models and round trips. They do not hide the producer-frame label or score an output map whose true frame is outside the declared hypothesis.
- COLMAP/Nerfstudio/3DGS convention code documents or applies an axis conversion. It assumes the contract supplied by the data reader and does not measure false certification when that contract is wrong.
- NeRF, pixelNeRF, iMAP, and 3DGS establish reuse of one representation for many queries. They do not compare competing frame queries against one immutable producer map with a hidden frame label or an ambiguity-rejection outcome.
- MVS reprojection checks score geometric residuals and masks. They do not require a unique convention decision, distinguish an undocumented canonical frame, or report `FUP`/`AReject`.
- R148 correctly observes that these sources cover the ingredients, but its stronger statement “no independent benchmark gap” conflates component overlap with coverage of this adversarial certification error.

## Verdict

**Verdict (a), narrowly:** a defensible *evaluation* gap survives: no cited source measures hidden-frame false unique certification or ambiguity-rejection rate across producer systems. This does **not** revive a reconstruction, rendering, geometry, or memory method claim. It is a possible benchmark-construction contribution only.

R148's unconditional END-LINE for the benchmark direction is therefore too strong. Its END-LINE decision for a method novelty claim remains correct.

## Minimal falsifiable benchmark protocol

1. **Systems and labels.** Use at least three independently maintained producer families drawn from the cited convention families (raw OpenCV, OpenGL/Blender-style `F3`, and one canonical/common-frame path such as DUSt3R). Generate one map per case and hide the true output-frame label from the scorer.
2. **Cases.** Use multiple synthetic geometries, camera poses, image sizes, intrinsics, pixel-center rules, and depth units. Hold out geometries and poses. Pre-register producer input pose, output frame, units, ID/depth schema, map hash, and rounding/z-buffer rules.
3. **Scorers.** Compare (i) ordinary declared-convention round trips, (ii) a residual-minimization rule, and (iii) the R140 same-map 2x2 raw/F3 scorer with fail-closed `H2_UNIDENTIFIABLE`. Each scorer sees the same immutable map; no branch-specific map generation or outcome-based relabeling is allowed.
4. **Metrics.** Report `FUP`, `AReject`, true unique-identification accuracy on in-hypothesis cases, ID/depth errors, positive-z and in-bounds rates, and fixed denominators with confidence intervals across systems and held-out cases.
5. **Falsification and stop.** The gap is falsified if an existing cited-style baseline already measures the same hidden-label estimands, or if the R140 scorer has no lower `FUP`/higher `AReject` on held-out out-of-hypothesis cases than ordinary declared-convention checks. A single fixture, one producer, a mean residual improvement, or successful round trips cannot establish the gap.
6. **Review.** Require an independent rerun from published manifests/source hashes before making a benchmark claim.

## Final disposition

Retain `new_method_validated=false` and `novelty_authorization=NONE`. Do not implement or execute this protocol in the current research line. If pursued later, treat it as a separately authorized benchmark-construction project with the hidden-label estimands above; the present artifact is a falsifiable challenge, not benchmark evidence.