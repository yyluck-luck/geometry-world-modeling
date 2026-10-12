# Experiment map — evidence before method claims

Snapshot: 2026-10-10 America/Los_Angeles. Base repository commit `52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c`; live jobs remain separate from this versioned summary. This is a scientific map of the accumulated stages, not a claim that every historical memo was re-audited. Original protocols/results remain intact. [Machine-readable ledger](EXPERIMENT_LEDGER.csv).

## The question

Can a video generator use geometric information in past observations to predict the same physical scene better than recent-frame conditioning, pose-nearest retrieval and direct geometric rendering, without amplifying reconstruction mistakes? Geometry quality, selection quality and generated-video quality are distinct endpoints. A correct map is not automatically useful conditioning, and a better PSNR is not automatically better perceptual or temporal quality.

## What survives

1. **MEASURED mechanism:** the catastrophic scale failure was traced to confidence-gated PnP failure, silent identity fallback and unstable similarity registration. It is no longer an unknown focal/baseline mystery. KPS substantially repaired the original panel, while fresh multi-area banks later failed different validity checks. [S133](../../work/S133_scale_debug/RESULT.md), [S135](../../work/S135_scale_init/RESULT.md), [S146](../../work/S146_fresh12/PROTOCOL.md).
2. **DERIVED useful evidence, limited scope:** on the original chess revisit panel, the same historical contexts yield a warp advantage of +1.46dB over static contexts, but the generator memory-minus-static contrast is -0.181dB and inconclusive around practical zero. The warp is +3.21dB above the generator on those memory contexts. This motivates testing consumption; it does not prove retrieval is universally solved. [S139](../../work/S139_crossseq_revisit/RESULT.md).
3. **DERIVED adaptation without established memory benefit:** S141 A beats the original model by +0.33046dB, 95%window-bootstrap CI[+0.07822,+0.58486]; A memory versus A static is -0.33174dB, CI[-0.66936,+0.00572]. B loses the warp by -3.55774dB. A is a useful adapted baseline, B is stopped. [Independent final review](evidence/S141_FINAL_REVIEW.md).
4. **DERIVED stronger simple controls:** S143 nearest4 beats VMem retrieval by +0.738dB on fresh seeds in the same exposed room. Geometry-favored and generator-favored context packages differ. S144's release mechanism fails; development-fitted global blending beats its candidate. These require stronger controls, not another weak-baseline gain. [S143](../../work/S143_context_ranking/RESULT.md), [S144](../../work/S144_A_wgs/RESULT.md).
5. **DERIVED positive geometry mean is insufficient:** W1's answer-informed candidate oracle has headroom. W2's actual source-only selector reduces mean correspondence error by27.5966%, yet fails its unchanged concentration gate (top2share59.6497%, cap50%). P1 adds only0.005742dB over the strong frequency control. W2/P1 stay stopped. [W1](evidence/W1_RESULT.md), [W2](evidence/W2_RESULT.md), [P1](evidence/P1_RESULT.md).

All numbers above are reported from the linked measured-output summaries; this reset reuses completed independent checks rather than rerunning experiments. Per-pixel counts and repeated seeds are not independent scenes. NO_MATERIAL_CHANGE is not an equivalence result. The S140 PSNR failure coexists with a positive SSIM result; do not erase it. [S140](../../work/S140_warp_guided/RESULT.md).

## The work that remains active

- **P2:** one existing UC observed-source diagnostic, frozen original protocol; queue waiting is not a result. No duplicate submission or threshold change.
- **S145:** other-agent branch ablation explaining B failure; allow the already-running diagnostic to finish, without optimizing B.
- **S146:** other-agent operational retrieval comparison after the original geometry-qualified assay was invalid. Its later result must retain the amended scope.
- **Next method:** a design candidate only until its own minimal causal assay has been frozen and passed. Do not run it concurrently with P2.

## What to stop doing

Stop treating infrastructure fixes, review counts, oracle gains or isolated PSNR improvements as method innovation. Stop expanding independent experiment branches before a current candidate produces a pass/fail. Stop retuning B, W2, P1 or the failed S144 release. Keep the raw failures and original protocols, but use this map for navigation rather than reading hundreds of audit memos.

## Repository reading order

Read this map, then NEXT_DIRECTION_AND_PLAN.md, then the result for the active question. README and the September18 report are historical documents; their old 'current' text and incomplete acquisition reports must not override later completed results. The full per-stage source links and uncertainty are in EXPERIMENT_LEDGER.csv. Scientific evidence, live execution state and literature are separate records.
