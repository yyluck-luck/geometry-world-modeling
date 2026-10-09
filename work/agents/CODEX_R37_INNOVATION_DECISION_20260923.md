# R37 innovation decision: narrow the claim before spending GPU

Date: 2026-09-23

This is a design and prior-art decision record. It does not authorize a method, a novelty claim, a training run, or a paper claim. The project remains `new_method_validated=false` and `novelty_authorization=NONE`.

## Decision

The broad proposal is rejected as too occupied. The following are not defensible novelty claims by themselves:

- persistent 3D memory or an unseen-region completion module;
- uncertainty-guided depth/appearance completion;
- generic belief update or multi-hypothesis 3D prediction;
- occlusion consistency, re-entry continuity, or out-of-sight forward evolution;
- delayed observation plus smoothing as a generic state-estimation algorithm;
- a geometry adapter, extra depth channel, or retrieval/reranking change.

The only candidate worth a bounded pilot is:

> In a camera-conditioned generative 3D world model, maintain an auditable predictive belief for a currently hidden surface; when a later observation reveals that surface and conflicts with the prediction, apply a local posterior correction to that same belief, use the corrected belief for a future novel view or reappearance, and preserve an untouched region that received no contradictory evidence.

This is deliberately narrower than “belief update,” “scene completion,” or “persistent memory.” The unit of novelty is the *reveal-event correction pathway* from a delayed contradictory observation to a later generated view. It must be compared with an append-only context/retrieval control and a capacity-matched generic completion control.

## Hostile prior-art occupancy

| Occupied claim | Primary evidence | Consequence for this project |
|---|---|---|
| belief inference, multi-hypothesis 3D, sequential updating, unseen-region prediction | [3D-Belief](https://arxiv.org/abs/2605.11367) | Do not claim generic 3D belief maintenance or unseen completion. |
| hidden-state evolution while out of sight and re-entry | [LiveWorld](https://arxiv.org/abs/2603.07145), [ReMind](https://arxiv.org/abs/2605.25333), [Hybrid Memory/HyDRA](https://arxiv.org/abs/2603.25716) | Do not claim occlusion continuity or forward out-of-sight dynamics. |
| persistent 3D state and unseen-view pointmap prediction | [Continuous 3D Perception with Persistent State](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Continuous_3D_Perception_Model_with_Persistent_State_CVPR_2025_paper.pdf), [Learning 3D Persistent Embodied World Models](https://arxiv.org/abs/2505.05495) | A persistent map is infrastructure, not the contribution. |
| completion, local repair, and uncertainty-guided novel-view synthesis | [CompNVS](https://arxiv.org/abs/2207.11467), [GenVS](https://arxiv.org/abs/2304.02602), [ORCA](https://arxiv.org/abs/2609.17450), [Novel View Synthesis from a Few Glimpses](https://web.eecs.umich.edu/~stellayu/publication/doc/2025nvsNIPS.pdf) | A confidence map or geometry-conditioned adapter is not enough. |
| retroactive smoothing of delayed observations | [Continuous-Time Fixed-Lag Smoothing for LiDAR-Inertial-Camera SLAM](https://arxiv.org/abs/2302.07456), [OR-LIM](https://www.sciencedirect.com/science/article/pii/S0924271624003745) | Separate scene-belief correction from pose/trajectory smoothing. |

## Claim and evidence contract

The candidate is allowed to survive only if a three-stage episode is measured on independent scenes:

1. **Hidden:** a target surface is not visible in the delivered context. The model emits a belief mean, uncertainty, and a predicted target rendering.
2. **Delayed reveal:** a later RGB-D observation exposes the surface and is selected so that its residual against the pre-reveal prediction is nonzero. The update is local to the revealed region.
3. **Reappearance:** a later held-out camera queries the corrected state.

Required measurements, all reported against matched controls:

- pre-reveal calibration and error of the hidden-surface belief;
- local posterior correction magnitude and recovery of the revealed surface;
- future novel-view RGB and geometry quality after correction;
- preservation of an untouched region with no contradictory evidence;
- comparison with append-only “add the new frame/retrieve more” and capacity-matched generic completion/depth-adapter controls;
- an ablation that forbids writing the prediction into measured evidence memory.

The pilot is killed if any of the following occurs: the gain is explained by more context, generic completion, or parameter count; the correction is global rather than local; untouched regions drift; the effect disappears when slot-0 reference/scale are canonicalized; or an existing method is found with the same delayed-reveal posterior target and evaluation.

## Relationship to C8

C8 is a prerequisite diagnostic, not evidence for the candidate. The slot-factor CPU gate passed remotely (`RS` max absolute difference `5.96e-08`; native `N` difference `2.77108526`), so later order comparisons must canonicalize the slot-0 reference and scale. The support audit remains necessary to determine whether hidden-surface support is actually missing or whether the failure is delivery/indexing/consumption. No C8 output validates novelty.

## Immediate action

1. Finish the static C8 audit fixes and keep the jobs unsubmitted until the owner reviews the preregistration.
2. Do not implement a large “belief memory” architecture. First define the three-stage episode and the matched controls as a zero-GPU data contract.
3. If C8 shows low bank support without a delivery/indexing explanation, run a tiny reveal-event feasibility pilot. If it does not, close this candidate and redirect to the measured infrastructure failure.

