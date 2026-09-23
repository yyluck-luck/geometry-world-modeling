# Method-invention corpus and candidate derivation

Date: 2026-09-23. This is a research design artifact, not a novelty authorization. The project flags remain `new_method_validated=false` and `novelty_authorization=NONE`.

## Research questions

1. What recurring invention moves turn a measured failure into a top-conference method rather than an incremental module swap?
2. Which of those moves are already occupied around persistent 3D/video world modeling?
3. What smallest falsifiable mechanism remains worth testing after the C8 diagnostics?

## Corpus and reverse engineering

The corpus was assembled from primary proceedings or author-hosted primary papers. The links below are canonical entry points; the one-line reconstructions are based on the papers' stated problem/method/evidence, not on citation counts.

| paper | old assumption and failure | new abstraction and intervention | newly available information / minimal leap |
|---|---|---|---|
| [SlotFormer, ICLR 2023](https://arxiv.org/abs/2210.05861) | A monolithic pixel state hides which entity changed, so object interactions are hard to predict. | Factor video into object slots and learn slot dynamics; representation + state transition. | Object identity and per-entity change become explicit. The leap is “predict entity state, then decode,” not “add attention.” |
| [Diffusion Forcing, NeurIPS 2024](https://openreview.net/forum?id=yDo1ynArjj) | Teacher-forced next-token models accumulate continuous-video error; full-sequence diffusion cannot naturally roll out variable horizons. | Give each token an independent noise level and combine causal prediction with full-sequence diffusion; objective + inference reparameterization. | A single model can expose variable-horizon subsequences and guide a rollout. The interaction is per-token noise with causal conditioning. |
| [DreamerV3, arXiv/Nature 2025](https://arxiv.org/abs/2301.04104) | Pixel-control systems do not share a stable recipe across domains and sparse long-horizon rewards. | A learned latent transition model becomes the planning state; normalization/balancing make one training recipe portable. | Future consequences can be imagined in latent state. The conceptual move is a predictive state used by both actor and critic. |
| [Curious Exploration via Structured World Models, NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/hash/98ecdc722006c2959babbdbdeb22eb75-Abstract.html) | Intrinsic reward alone does not encode relational structure needed for object manipulation. | Structured relational world model couples object relations to exploration and planning; state + interaction. | The model's relational prediction changes what the agent explores. The nontrivial interaction is model quality and exploration reinforcing each other. |
| [Generative Rendering, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Cai_Generative_Rendering_Controllable_4D-Guided_Video_Generation_with_2D_Diffusion_Models_CVPR_2024_paper.html) | 2D diffusion is expressive but a text/video condition does not preserve controllable geometry and correspondence. | Treat a low-fidelity animated 3D mesh and its correspondence as a generative control pathway; geometry + conditioning. | Correspondence becomes available at multiple diffusion stages, so a 2D prior can render a controllable 4D sequence. |
| [MorpheuS, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Wang_MorpheuS_Neural_Dynamic_360deg_Surface_Reconstruction_from_Monocular_RGB-D_Video_CVPR_2024_paper.html) | Dynamic monocular RGB-D reconstruction leaves large unobserved regions that a purely fitted field cannot complete. | Separate canonical geometry/appearance from deformation and distill a view-dependent diffusion prior; representation factorization + generative completion. | A canonical field lets evidence persist while a prior supplies unobserved content. |
| [Lift3D, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/T_Lift3D_Zero-Shot_Lifting_of_Any_2D_Vision_Model_to_3D_CVPR_2024_paper.html) | 2D operators cannot be made 3D-consistent without task-specific optimization. | Lift a 2D model by adding a 3D-consistent interface; representation and geometry intervention. | The same 2D capability can act across views because the interface exposes 3D consistency. |
| [Continuous 3D Perception Model with Persistent State, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Continuous_3D_Perception_Model_with_Persistent_State_CVPR_2025_paper.pdf) | Frame-wise perception forgets a scene and must repeatedly solve geometry; explicit maps are costly and not online-predictive. | Maintain a latent persistent state that is updated by each image and emits metric-scale pointmaps/poses; state innovation. | A new observation can both read and update a scene state, making continuous 3D prediction possible. |
| [Geometry-as-context, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.html) | External memory or separate reconstruction/inpainting loops accumulate inconsistent intermediate outputs. | Make an explicit 3D reconstruction a context signal in an iterative generation/reconstruction loop; geometry + feedback. | Generated views and scene geometry constrain each other. The leap is moving geometry into the context loop, not merely adding depth. |
| [WorldStereo, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.html) | Camera-guided video can look plausible while its views disagree in 3D. | Split global geometric memory from spatial-stereo memory with 3D correspondence; factorized memory + attention routing. | Coarse global structure and fine local correspondence are available as different pathways. |
| [GeoMIM, ICCV 2023](https://openaccess.thecvf.com/content/ICCV2023/html/Liu_GeoMIM_Towards_Better_3D_Knowledge_Transfer_via_Masked_Image_Modeling_ICCV_2023_paper.html) | Image features and LiDAR geometry differ, so ordinary masked modeling transfers semantics poorly. | Add a camera-aware geometry reconstruction branch and cross-view attention; supervision + factorization. | Dense depth becomes a training signal that bridges domains; the gain is not just another loss but a missing target. |

The patterns recur across domains: (i) replace the unit of state (pixels/frames → objects or predictive latent state); (ii) separate variables with different update laws (canonical geometry vs deformation, global vs local geometry); (iii) expose a missing invariant or correspondence; (iv) introduce a feedback path so later evidence can correct prediction; (v) derive supervision from an existing structure such as future observations or multi-view geometry; and (vi) reparameterize inference so the model can represent variable horizon or uncertainty. Strong papers explain why the old assumption destroys information and then measure the capability enabled by the new state. A module swap with a small metric gain does not meet that bar.

## Project evidence and occupied local search

The repository's current rule is that a method must change what the model predicts under the same legal state and evidence, such as future views, reappearance after occlusion, or cross-view geometry (`docs/METHOD_DIRECTION_CURRENT.md`, lines 5-16). Retrieval/reranking and state-management candidates were already ruled out there. The pinned VMem path uses slot 0 as the Plücker reference (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`, lines 1135-1140), derives translation scale from camera 0 (1098-1119), mean-pools context embeddings (1123-1125), and retrieves from an averaged pose with `0.65*K` (635-645). S107/S113 show a finite-panel slot-order effect and near-zero slot permutations after slot 0 is fixed, but those are diagnostics, not a method.

Prior art makes broad claims such as “persistent 3D state,” “geometry as context,” “geometric memory,” and “occluded-region completion” already occupied. Therefore a proposal cannot claim novelty merely by predicting hidden depth, adding a geometric adapter, or storing a point cloud. The defensible gap must specify a previously absent information pathway and an experiment that distinguishes it from generic completion or extra capacity.

## Candidate derivations across distinct axes

### Candidate 1 — Delayed-observation belief smoothing (state, latent variable, correction)

1. **Observed failure:** C8 may find target regions absent from the delivered context; the current generator has no measured distinction between an observed surface and a guessed continuation. The claim is presently unmeasured.
2. **Broken assumption:** a single causal memory state is sufficient even when future re-observation can contradict a hidden-surface guess.
3. **Missing quantity:** a persistent belief over hidden surface geometry/appearance, separate from measured evidence and with an update when the surface reappears.
4. **New abstraction:** maintain `(E_t, B_t, U_t)`: immutable observed evidence, predictive belief, and uncertainty; a later observation performs a retrodictive smoothing update on `B_t` while preserving the causal timeline of generated frames.
5. **Mechanism:** a compact 3D belief field queried by target rays, a reveal-event update that compares rendered belief with the newly observed RGB-D, and a correction pathway used for subsequent views; train with future reappearance pairs and a matched generic completion control.
6. **New capability:** the model can make a hidden-surface prediction before reveal and revise the persistent state after reveal, then improve the next reappearance. This is stronger than “more context” because it changes state semantics and enables a falsifiable correction curve.

Main risk: generic belief-state and persistent-state papers already exist. The narrow claim must be *retrodictive smoothing of a camera-conditioned generative world model under delayed re-observation*, with explicit before/after belief error and a no-write-to-evidence control. Kill it if a review finds an existing method with the same two-track state and delayed re-observation objective, or if C8 shows the failure is indexing/delivery rather than missing support.

### Candidate 2 — Reveal-event predictive geometry field (representation, geometry, generative conditioning)

1. **Observed failure:** if B is low while C is low, newly visible surfaces have no measured support in the delivered frames.
2. **Broken assumption:** geometry is only a retrieved metadata channel; the generator may infer it implicitly at denoising time.
3. **Missing quantity:** a target-queryable prediction of hidden surface geometry tied to the future reveal event.
4. **New abstraction:** a predictive geometry/appearance field distinct from the surfel evidence map.
5. **Mechanism:** infer a field from four context frames, render it into target cameras, inject it through a zero-initialized adapter, and supervise only on newly revealed regions with a capacity-matched generic completion/depth adapter.
6. **New capability:** before seeing a surface, the model predicts where it will appear and how it should align across views; evaluation measures generated RGB geometry and reappearance, not only auxiliary depth.

Prior-art risk is high: MorpheuS, Geometry-as-context, WorldStereo, GeoNVS/ORCA, and generic depth-conditioned diffusion occupy broad geometric completion. Kill it if the matched generic completion control closes the gain or if hidden-region gains are not concentrated at reveal events.

### Candidate 3 — Evidence–belief factorized memory with asymmetric updates (factorization, state transition)

1. **Observed failure:** the current evidence list, surfel memory, and generated content share lifecycle and conditioning paths; the project has documented lifecycle/state contamination risks and no validated persistent state.
2. **Broken assumption:** one representation can both preserve sensor evidence and absorb predictions with the same update rule.
3. **Missing quantity:** separate variables for measured evidence, persistent geometry, appearance dynamics, and uncertainty.
4. **New abstraction:** a factorized state with asymmetric writes: evidence is append-only, geometry is slow/persistent, appearance is fast, uncertainty contracts only after independent re-observation.
5. **Mechanism:** factorized memory slots with typed update operators and a cross-view consistency transition; supervise each factor with geometry/appearance/reappearance targets.
6. **New capability:** a later view can change appearance without erasing geometry or identity, and uncertainty can remain high for unsupported surfaces.

Prior-art risk: canonical/deformation fields and persistent-state models already implement parts of this. Kill it if factors cannot be identified with paired controls, or if gains reduce to a normal multi-branch network with no distinct update law.

### Candidate 4 — Identity-preserving geometric tracks through occlusion (identity, representation)

1. **Observed failure:** RGB context selection and camera-coordinate rays do not expose an explicit persistent identity for a surface/object across occlusion.
2. **Broken assumption:** cross-view geometry alone is enough to maintain identity through a long occlusion.
3. **Missing quantity:** a view-invariant identity track attached to geometry and uncertainty.
4. **New abstraction:** identity-bearing 3D tracks that survive absence and reconnect on reappearance.
5. **Mechanism:** query-independent track tokens built from geometric correspondences, with an association/reappearance decoder and hard negatives that swap similar objects.
6. **New capability:** the model can state that a reappearing surface is the same entity and preserve its geometry despite changed view/appearance.

Prior art risk: SlotFormer/object-centric models and tracking systems occupy identity factorization; this survives only if the contribution is a generative 3D reappearance capability with hard geometric identity tests. Kill it if identity labels or correspondence are unavailable or if a generic tracker plus generator matches it.

### Candidate 5 — Counterfactual re-observation supervision (objective, information pathway)

1. **Observed failure:** endpoint RGB PSNR cannot tell whether a model predicted a hidden surface for the right geometric reason or hallucinated a plausible texture.
2. **Broken assumption:** one endpoint reconstruction loss is enough to train persistent geometry.
3. **Missing quantity:** a supervision signal that couples a pre-reveal prediction to the later observation and tests consistency under a counterfactual camera.
4. **New abstraction:** a reveal/re-observation cycle: predict hidden geometry at time t, render a future camera, compare after reveal, and require the state update to explain the residual.
5. **Mechanism:** a cycle-consistency objective with masked future observations, hard negative camera paths, and a matched generic completion baseline; no auxiliary loss is accepted unless it changes the state transition and predicts a new capability.
6. **New capability:** the model learns from how errors are corrected after reveal, not merely from final pixels, enabling calibrated pre-reveal uncertainty and improved subsequent views.

Prior-art risk: multi-view/self-supervised geometry and cycle consistency are broad predecessors. Kill it if the cycle loss improves only an auxiliary head or if a standard future-frame objective produces the same correction behavior.

## Surviving set and ranking

1. **Candidate 1, delayed-observation belief smoothing:** strongest conceptual claim and clearest distinction from retrieval; high prior-art and data-contract risk.
2. **Candidate 2, reveal-event predictive geometry:** closest to the current proposal and easiest pilot, but the most crowded prior-art space; retain only with the matched generic-completion control.
3. **Candidate 5, counterfactual re-observation supervision:** a useful training principle if it changes state correction; do not present it as “another loss.”
4. **Candidate 3, factorized evidence/belief memory:** plausible architecture-level route, but only after a real lifecycle and re-observation oracle exists.
5. **Candidate 4, identity tracks:** keep as a fallback axis; it needs data and hard negatives that are currently missing.

Candidates 2 and 5 can be composed later only if Candidate 1's evidence/belief distinction is explicit. Candidates 3 and 4 should not be merged into a large architecture before an information-path ablation identifies the causal variable.

## Highest-information next experiment

Run the owner-approved C8 pair as one decision gate: (i) the CPU RS/N equivalence test followed by the 16-cell slot-factor diagnostic, and (ii) the 14-window B/C/J support audit with no diffusion. The support audit has the highest branch-elimination value because the outcomes separate physical scarcity, delivery, surfel indexing, and consumption before any training expenditure. The slot-factor test is a necessary confound control: if RS removes the effect, later order comparisons cannot support a temporal-position method.

The preregistered implementation is in `work/S130_C8_diagnostics/`. It sets `new_method_validated=false`, uses exposed development windows only, and stays below the 20 H800-hour cap. A low-B pattern with no dominant indexing/delivery explanation permits a pilot of Candidate 1 or 2; a high-B/low-J or high-B/low-C pattern kills those candidates and redirects to infrastructure; high-C/poor-PSNR redirects to consumption. No C8 result by itself establishes novelty.
