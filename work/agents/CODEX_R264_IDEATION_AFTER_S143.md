# R264 — Ideation after S143: confirm the retrieval reversal before inventing a retriever

Workspace: local Mac checkout, identified by the supplied environment. Review date: 2026-10-10. Repository snapshot: 532c29ee4d26674634a91d9f6786cbb24978e5cf.

**Recommendation: first run FRESH12_RETRIEVAL, a prospective finite-panel replication on three 12-Scenes rooms. Do not claim a new retrieval method.** If the fixed nearest-4 advantage does not survive new rooms and the native-order control, write up the exposed-panel diagnosis. If it survives, isolate candidate filtering, target-query aggregation, and NMS before attributing the effect to diversity.

This review used repository inspection, independent CPU arithmetic, primary literature, and official dataset pages. No fresh-seed S143 scores were read, no new generation or training was performed, and no dataset/weight archive was downloaded. No cluster was contacted. The only file written by this review is this report. The initial working tree already contained the two untracked R264 prompt files; they were left alone. No external decision-maker was contacted.

State remains **new_method_validated=false; novelty_authorization=NONE**. This is a review and a proposed experiment design, not an executed protocol or a novelty authorization. The brief's introductory “S141 running” description is stale: the current S141 RESULT and analysis contain completed evaluation. Current repository evidence supersedes older memory notes.

Evidence labels below: **MEASURED** = archived experimental measurement, not newly generated here; **DERIVED** = arithmetic over archived measurements or manifests; **ANALYTICAL** = proposed design, threshold, cost calculation, or hypothesis; **UNVERIFIED** = not established by accessible evidence. Appendix A gives exact commands and complete outputs for every new numerical verification reported here.

## 1. What the discovery establishes—and what it does not

The discovery arithmetic is reproducible from POOL.json, WARP_SCORES.json and GEN_SCORES_discovery.json. Independent recomputation recovered the primary, window bootstrap intervals, rule means, and both complete frozen 100,000-draw null simulations. The panel-null numerical discrepancy is only floating-point summation order; the independent-window null agrees exactly at printed precision. This verifies the score-table arithmetic, not the absent raw GPU image arrays or checkpoint execution.

Source evidence: work/S143_context_ranking/PROTOCOL.md:13–58; work/S143_context_ranking/analyze_s143.py:13–100; work/S143_context_ranking/results/S143_ANALYSIS.json:30–112. Complete verification is in Appendix A1–A2.

| Quantity | MEASURED/DERIVED result | Reading |
|---|---:|---|
| R_2seed_hindsight | +0.320443 dB; window bootstrap [0.186214, 0.458037] | Passes the frozen exposed-panel gate |
| Panel null95 / tail | 0.290753 dB / 0.034540 | Model-based sensitivity diagnostic, not an exact randomization p-value |
| Independent-window null95 | 0.098065 dB | Much less conservative than the correlated-panel diagnostic |
| Window selector minus cross-fitted global rule | +0.275301 dB; [0.119792, 0.444961] | Passes its 0.216022 threshold; rule 4 selected in both folds |
| Mean within-window Spearman | 0.159524 | Weak rank agreement in this particular pool |
| Warp spread, best minus worst | 2.838667 dB | Passes the 1 dB assay-spread gate |

The Spearman value is archived at results/S143_ANALYSIS.json:114–141; its tie-aware implementation is analyze_s143.py:103–114. The other values are independently reproduced in Appendix A. Window intervals describe this exposed, dependent panel; three sequence pairs in one room are not independent scene replications. The null uses four observed seed residual directions and a Gaussian equal-mean model, not an empirical proof of universal selector superiority (analyze_s143.py:75–100).

The full rule ranking is:

| S143 rule | Generated PSNR | Warp PSNR | Generated SSIM | Warp-best windows |
|---|---:|---:|---:|---:|
| 1 static_recent | 11.489225 | 13.114016 | 0.486963 | 1 |
| 2 mem_pose | 11.578046 | 14.302340 | 0.483565 | 1 |
| 3 mem_vmem, bank-sorted | 11.190094 | 14.378108 | 0.464563 | 1 |
| 4 nearest-4 | 11.937005 | 14.297765 | 0.500000 | 6 |
| 5 coverage-greedy | 11.917725 | 15.414303 | 0.492741 | 14 |
| 6 random | 11.380289 | 14.051418 | 0.482121 | 1 |

All entries are MEASURED archived means, independently aggregated in Appendix A1; source work/S143_context_ranking/results/S143_ANALYSIS.json:143–185.

Three corrections materially change the ideation:

1. **Coverage is competitive for generation.** DERIVED nearest-4 minus coverage-greedy is only +0.019279 dB, with an exploratory paired window interval [−0.190930, +0.235684]. The evidence does not show that the generator prefers proximity *over the coverage-greedy rule*. Both beat sorted mem_vmem descriptively: +0.746910 and +0.727631 dB, respectively. These new contrasts are post-discovery descriptions, not newly preregistered findings (Appendix A1).
2. **The deployable rule does not recover the reported hindsight gap.** DERIVED generated PSNR at c_W is 11.891863; nearest-4 minus c_W is only +0.045142 dB. The +0.320443 primary uses a target-informed, window-specific selector, not nearest-4. Neither c_W, which uses target RGB to score warps, nor c_G is deployable. Rule 5 itself is deployable from bank RGB/poses and target poses; it must not be conflated with c_W (PROTOCOL.md:16–21,25–36; score_warps_s143.py:28–47).
3. **Historical content and order are substantial confounds.** DERIVED history-frame fractions are 29.17% for nearest-4, 67.71% for coverage-greedy, and 88.54% for mem_vmem; nearest-4 and coverage share only 1.458 frames on average. Thus their similar generation means are not explained by identical memberships, and the nearest/mem comparison also changes the balance of recent versus other-traversal appearance. This is a hypothesis source, not evidence that old images cause the deficit (POOL.json; Appendix A1).

The two geometric utilities also differ operationally. Rule 5 constructs masks from one bank-conditioned depth inference; Q_W reconstructs geometry again from each selected four-frame package. Rule-5 support counts positive, in-bounds projections, without target-depth visibility validation. It is a predicted support proxy, not a measurement of true visible-surface coverage. Therefore a ranking mismatch can arise in the geometry estimator as well as in the generator (build_pool_s143.py:47–54,65–78; warps_s143.py:43–51).

**S141 does not remove these qualifications.** MEASURED adapter A improves original-order memory generation by +0.330456 dB, but A_mem − A_static is −0.331743 dB. B fails its primary PSNR comparison by about −3.558 dB despite better chess SSIM. Nearest-4 plus A is unmeasured; adding the two separate gains would be invalid. Evidence: work/S141_finetune/RESULT.md:23–35,45–68; results/S141_ANALYSIS.json; Appendix A3. The six non-chess 7-Scenes rooms are training data, not a new confirmation set (RESULT.md:8–17).

Amendment 2 supersedes Amendment 1's confirmation language: the pending seeds produce a descriptive frozen-selection estimate, not formal confirmation of R or new-scene generalization. Amendment 3 adds exploratory fixed-rule contrasts. No outcome of that pending block is assumed here (work/S143_context_ranking/PROTOCOL.md:60–104).

## 2. Reconciliation with VMem Table 4

### Paper claim versus executable definitions

Verified paper: **arXiv:2506.18903v3, “VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory.”** Table 4/§4.4 reports K=4 PSNR 14.82 for VMem versus 13.27 for camera distance. The distance baseline selects closest cameras; its exact aggregation, NMS and ordering are not fully specified. §3.1 and Appendix B describe average-target-pose surfel voting with redundancy suppression. §4.3 uses autoregressive outward-and-return cycles; §4.1 fine-tunes the reduced-context generator on RealEstate10K. These are material differences from a fixed real-image-bank assay. The camera-distance row is absent from v1; use v3 for this comparison. [Verified paper and sections](https://arxiv.org/html/2506.18903v3).

The answer to “same baseline?” is **no established exact equivalence**. S143 nearest-4 shares the closest-camera idea, but the checked paper does not specify enough to equate it to our all-target fp64/no-NMS algorithm. The commented-out distance branch in the transport code is not proof of which executable produced Table 4.

For all code claims below, the source is the transport mirror at the local repository snapshot above. Its pipeline.py SHA-256 is 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 (Appendix A3). Do not substitute the older 90a45f45… pinned-copy hash or attach its upstream commit to this mirror without verification.

| Component | S143 nearest-4 | S143 mem_vmem and native retrieval |
|---|---|---|
| Candidates | All 32 bank identities | Weighted surfel-visible candidates; top K+10 when the visible list is larger |
| Target query | Mean of four individual pose distances | Last target at K=4 |
| Ranking | fp64 angle + 0.1 × translation | Pose distance after surfel filtering, in pipeline tensor precision |
| Diversity | None | Adaptive pose NMS |
| Membership provenance | Constructed by S143 | Imported from archived S139 clean NMS-on retrieval |
| Output order | Bank index | S143 re-sorts native membership by bank index |

The exact source trace:

- **Nearest rule:** work/S143_context_ranking/build_pool_s143.py:24–26 defines the distance; :58–62 averages it over targets and selects four. Mean of distances is not distance to an averaged pose.
- **Surfel query:** data/S134_tacc/vmem_src/modeling/pipeline.py:635 slices the target list by context_num_frames; at K=4 only the last target remains. Configuration: data/S134_tacc/vmem_src/configs/inference/inference.yaml:9–17.
- **Candidate score and truncation:** pipeline.py:466–485 accumulates cos/(1+depth) over rendered visible contributions; :492–494 and :422–429 select at most K+10 weighted identities. At K=4 this is a top-14 candidate cap when enough identities are visible. Visibility is not discarded: it defines the candidate set.
- **Final ranking:** pipeline.py:663–670 sorts candidates by pose distance. It does not simply output the four highest surfel vote counts.
- **NMS:** pipeline.py:681–698 initializes a median pairwise-distance threshold at the five-frame state; :710–740 greedily enforces separation and relaxes the threshold. The “25th percentile” comment conflicts with the implemented 0.5 multiplier; trust the code.
- **Native-off trap:** pipeline.py:704–716 appends the latest bank frame when NMS is off. Calling get_context_info(..., use_non_maximum_suppression=False) is not a clean closest-four/no-NMS intervention.
- **Actual project call:** work/S139_crossseq_revisit/run_retrieval_s139.py:92–116 installs KPS, primes memory in chunks, initializes the threshold, and explicitly requests NMS-on retrieval. Its :118 can repeat a short raw list, whereas S143 build_pool_s143.py:84 requires four distinct identities; future qualification must reject insufficient distinct candidates.
- **Order modification:** work/S143_context_ranking/build_pool_s143.py:80–87 sorts packages; build_plan_s143.py:11–16 preserves them. mem_pose is itself last-target pose-NMS over the full bank, not nearest-4 (work/S139_crossseq_revisit/pose_arms_s139.py:31–51).

Thus S143 mem_vmem is **native retrieved membership from a repaired project memory, under a changed slot policy**. It is neither a Table 4 reproduction nor an untouched native ordered package.

### Why opposite orderings are plausible

The following are ANALYTICAL explanations to discriminate, not measured causes:

- **Different estimand:** supplied real history plus nearby observations can support pixel reconstruction; autoregressive generated memory has a different error distribution. S139 banks explicitly combine another traversal and recent real frames (work/S139_crossseq_revisit/PROTOCOL.md:16–30); the generation harness consumes those fixed frames rather than generating an entire outward-return history (work/S141_finetune/gen_s141.py:163–190).
- **Filtering can remove useful nearby frames.** The top-14 visibility filter may trade appearance alignment for rendered relevance. The current rule-2 versus rule-3 comparison is informative but also crosses precision and archived retrieval implementations; it is not a perfectly isolated filter intervention.
- **Query mismatch can matter along a changing trajectory.** A set selected for the last target can be less useful for the first three. Four-target average distance and distance to a mean target pose are also different objectives.
- **NMS can trade aligned redundancy for wider evidence.** That might hurt copying or help occlusion handling. No single sign follows from the current comparison.
- **Order changes more than a label.** DERIVED memberships are identical in all 24 comparisons, but their order changes in 22 and slot 0 changes in 20. The archived mean warp difference is −0.194280 dB; original-order versus bank-sorted generated means differ by −0.084800 dB (Appendix A3). These cross-stage comparisons motivate a controlled rerun; they are not a proof that only order changed in every numerical path.
- **Generator anchoring is an explicit mechanism.** Translation normalization depends on camera 0 and Plücker coordinates use the first camera as reference (pipeline.py:1099–1119,1136–1141). Sorting can therefore alter camera conditioning, not merely temporal token order. CUT3R input order is a separate intervention.
- **Domain, camera scale, and precision differ.** The local configuration uses cfg=2.0 (data/S134_tacc/vmem_src/configs/inference/inference.yaml:20–23), whereas the paper Appendix A states guidance 3. This is another unmatched setting, not an established cause. S141's domain-adaptation gains support checking domain sensitivity, but not assigning all of the retrieval reversal to it. The fixed 0.1 translation weight acts on dataset pose units; keep units declared rather than silently tuning the weight for a new dataset.

The reconciled statement should be: **“In our exposed, real-history chess assay, closest-camera and coverage-greedy packages outperform the bank-sorted memberships returned by this repaired VMem implementation. This does not contradict its reported cycle-rollout result, and the responsible retrieval component remains unidentified.”**

## 3. Divergence: fourteen falsifiable candidates

All predictions here are ANALYTICAL. None is a claim of novelty or a demonstrated effect.

| # | Candidate and prediction | Smallest useful discriminator | Disposition |
|---|---|---|---|
| 1 | Fix nearest-4 as the cheap deployment rule; its gain survives new rooms | Freeze the rule before new-scene scores; compare both sorted and native-order mem_vmem | First experiment; baseline correction, not new method |
| 2 | Coverage-greedy is as useful to generation as proximity | Paired rule 5 − rule 4 with SSIM and scene means | Mandatory strong control; current data do not establish superiority either way |
| 3 | Diversity suppression discards aligned content | NMS on/off with identical candidate pool, query, precision and slots | Strong mechanism test |
| 4 | Surfel candidate truncation, rather than NMS, causes the loss | All-32 versus frozen surfel-candidate identities at the same query and NMS | Strong mechanism test |
| 5 | Last-target querying mismatches four-target generation | Last-target versus mean-of-four-distance ranking at fixed candidates/NMS | Strong mechanism test; do not call mean-distance “average pose” |
| 6 | Native retrieval order is helpful | Same memberships, native versus bank order; independently permute geometry and generator inputs | Confound control, not permutation search |
| 7 | Slot-0 camera normalization mediates apparent order sensitivity | Reuse identical conditioning geometry while changing only latent slots, versus full native anchoring recomputation | Only after #6; interface diagnostic |
| 8 | Nearest-4 gains mainly from recent-traversal appearance | Pose-distance-matched history/recent substitution; report balance before generation | Defer; matching can become a new tuned selection problem |
| 9 | Adapter A makes nearby context easier to exploit | Base/A × nearest/mem/static factorial with frozen final A | Third experiment if fresh reversal survives |
| 10 | Warp and generator need distinct evidence packages | Generator contexts nearest-4, warp contexts coverage-4, compared with shared nearest and shared coverage | Defer; fixed budgets and total information must be controlled |
| 11 | A future-blind selector can learn the hindsight headroom | Scene-held-out learning beats fixed nearest and coverage; no target pixels at inference | Reject current chess-only version; directly crowded prior art |
| 12 | Q_W ranking is partly unstable subset-depth estimation | Score identical selected memberships with bank-derived fixed depths versus four-view recomputed depths | Cheap geometry diagnostic; not true-geometry attribution |
| 13 | The distance metric is unit-sensitive | Controlled unit-rescaling invariance check before considering normalized-distance variants | Engineering audit; no post-score weight sweep |
| 14 | Generation is dominated by deterministic alternatives in this assay | Same-set copy, whole-bank copy, each set's warp, PSNR plus SSIM | Stop rule / honest write-up, not another adapter search |

The copy control is not hypothetical motivation: archived whole-bank copy is 12.218325 dB, above nearest-4 generation at 11.937005; within-nearest-set copy is 12.187744. These are MEASURED PSNR comparisons, not perceptual superiority or equal-output-model claims (results/S143_ANALYSIS.json:197–205; Appendix A1). Keep whole-bank versus four-context information budgets explicit.

### Prior-art check of the five most promising directions

**P1: Proximity selection, including its combination with adapter A (#1/#9).** arXiv:2405.10314, **“CAT3D: Create Anything in 3D with Multi-View Diffusion Models,”** §3.2 already uses nearest-view conditioning when the input set exceeds the context budget. arXiv:2106.09685, **“LoRA: Low-Rank Adaptation of Large Language Models,”** §§4.1–4.2 supplies the established adaptation mechanism. Combining these is not a new principle. The remaining question is an interaction in this consumer: does A change the relative utility of retrieval? [CAT3D](https://arxiv.org/html/2405.10314v1#S3.SS2), [LoRA](https://arxiv.org/html/2106.09685v2#S4).

**P2: Causal NMS/candidate/query decomposition (#3–#5).** arXiv:2504.12369, **“WorldMem: Long-term Consistent World Simulation with Memory,”** §3.4/Algorithm 1 combines view-overlap and temporal relevance with greedy similarity filtering. Redundancy control is established, not inherently wrong. The defensible contribution would be identifying a specific failure under a controlled implementation, with a counterexample to overly broad retrieval claims. VMem's own comparison does not substitute for this factorial. [WorldMem](https://arxiv.org/html/2504.12369v1#S3.SS4).

**P3: Split geometry and appearance evidence (#10), or combine coverage and proximity (#2).** arXiv:2608.16863, **“SplatGuide: Geometric Priors from 3D Gaussians for Pose-Free Novel View Synthesis,”** §§3.1–3.2 explicitly distinguishes coverage from informative conditioning, combines visibility with DeDup and pose-proximal PoseAug, and ablates them in Appendix D/Table A3. It also distinguishes reconstruction inputs from selected diffusion context. This is close prior art, not a merely similar title. A precisely controlled pair of four-frame consumers remains an ablation question; “coverage plus proximity” is not a defensible standalone novelty claim. [SplatGuide](https://arxiv.org/html/2608.16863v1#S3.SS2).

**P4: Ordered packages and first-view anchoring (#6/#7/#12).** arXiv:2501.12387, **“Continuous 3D Perception Model with Persistent State,”** §3.1/Eq. 2 describes recurrent updates and first-view coordinates; Appendix B's shuffled static training does not guarantee permutation invariance. arXiv:2506.03141, **“Context as Memory: Scene-Consistent Interactive Long Video Generation with Memory Retrieval,”** §3.2 treats context positional encoding explicitly. Neither proves the direction of S143's effect. Our local camera-normalization code is stronger evidence for a specific generator-side intervention than an analogy to another architecture. [CUT3R](https://arxiv.org/html/2501.12387v1#S3.SS1), [Context as Memory](https://arxiv.org/html/2506.03141v1#S3.SS2).

**P5: Learning utility rather than geometry relevance (#11).** arXiv:2609.34677, **“Learning What to Recall: Adaptive Multi-Cue Episodic Memory for World Models,”** §§3.1–3.3/Appendix C.1 defines FAR, trains recall using downstream predictive utility, and keeps inference future-blind. Its utility surrogate is negative diffusion prediction loss. A PSNR-labelled variant changes the surrogate, not the underlying contribution. Hindsight headroom alone does not establish learnability from permitted cues. **Write up now / defer this method candidate** until multiple untouched scenes support a stable gain over both fixed strong rules. [FAR](https://arxiv.org/html/2609.34677v1#S3).

The five checks are bounded prior-art retrieval, not proof of exhaustive novelty absence. They nevertheless reject the strongest broad novelty slogans suggested by this discovery.

## 4. Fresh data: exposure audit and actual access conditions

“Fresh” here means **no recorded project image/score-driven design exposure**, then a manifest/hash check before execution. It does not mean unseen by every pretrained component. No remote inventory was accessible under this brief; therefore no dataset is certified globally uncontaminated.

Known exclusions:

- S141 trains on fire, heads, office, pumpkin, redkitchen and stairs; chess has supplied S139–S143 evaluation. Exclude all seven rooms (work/S141_finetune/RESULT.md:8–17,84–87).
- RGB-D Scenes v2 scene_13 and scene_14 are explicitly exposed development sequences (docs/RETRIEVAL_ARMS_RESULT_20260918.md:11–19).
- TUM fr2_desk and fr1_xyz have prior experiments (RESEARCH_MEMORY.md:2029–2030; docs/S21_BASELINE_PROTOCOL.md:7).
- TUM fr3_long_office_household was previously qualified (RESEARCH_MEMORY.md:1596; research_events.jsonl:1888).
- TUM fr1_room was downloaded and used for pose/window design; its return windows belonged to a single return episode. It is not untouched merely because generation stopped (research_events.jsonl:2046).
- fr3_teddy/fr2_xyz already appear in candidate-selection records (research_events.jsonl:2036,2039). Metadata exposure is weaker than score exposure, but must be disclosed.

A targeted review of docs/, RESEARCH_MEMORY.md, research_events.jsonl and the current stage records found no experimental exposure record for 12-Scenes, Cambridge Landmarks, or RGB-D Scenes v2 scenes 01–12. This is an absence-of-record conclusion, not a claim about unlogged work or aliases in remote storage.

| Candidate | Official availability / size / licence | Assay suitability and decision |
|---|---|---|
| **12-Scenes** | Public posed RGB-D; repeated scans aligned in a common scene frame. Apartment 1 1.4 GB, apartment 2 2.8 GB, office 1 5.9 GB, office 2 1.7 GB as listed. CC BY-NC-SA 4.0. [Official release](https://graphics.stanford.edu/projects/reloc/) | Best fit. Use captured images, actual info.txt, and verified traversal boundaries. HEAD access checks are in Appendix A4; archive integrity is unverified. |
| RGB-D Scenes v2, 01–12 | 5.5 GB image archive plus 189 MB point-cloud/estimated-pose package. An explicit dataset licence was not located on the checked page/README. [Official release](https://rgbd-dataset.cs.washington.edu/dataset/rgbd-scenes-v2/), [README](https://rgbd-dataset.cs.washington.edu/dataset/rgbd-scenes-v2/README.txt) | Potentially fresh by project record, but distinct cross-scan revisits and licensing remain insufficiently established for the first choice. A pose file alone does not guarantee the required revisit assay. |
| TUM RGB-D, new sequences | Official table lists freiburg2_pioneer_slam at 1.82 GB; posed RGB-D and looping trajectories are available. CC BY 4.0 unless otherwise stated. [Downloads](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download), [Licence](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license) | A possible new sequence, not proven new physical room. Check pose coverage and episode dependence. Do not use validation recordings without public ground truth or recycle fr1_room as fresh. |
| ScanNet test scenes | RGB-D/camera-pose streams are documented, but access normally requires signed Terms of Use via institutional email. Exact test-subset size and existing approved access were not verified. Data terms differ from code MIT. [Official repository](https://github.com/ScanNet/ScanNet) | Not the one-day choice without existing access. No request/email is authorized in this run. “Test” does not itself prove pretrained-model cleanliness. |
| Cambridge Landmarks | King's College package is listed at 5.64 GB, with video, RGB frames and poses; CC BY-NC-SA 2.0 UK. [Official record](https://www.repository.cam.ac.uk/handle/1810/251342) | A posed-RGB alternative with no measured depth in this record; outdoor appearance changes, camera calibration, and traversal parsing add avoidable work. Not first choice. |

The numbers in this table are **MEASURED as official published download metadata**, not measured transfer sizes. The selected three 12-Scenes packages total **DERIVED 6,339,770,881 bytes** by live HEAD headers (Appendix A4); no archive body was read.

Named proposed rooms are **apt1/kitchen, apt2/bed, office2/5a**. These identifiers occur in Figure 10 of the supplement to arXiv:2109.00524, **“On the Limits of Pseudo Ground Truth in Visual Camera Re-localisation.”** This establishes published identities, not their integrity in today's ZIPs. [Primary supplement](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Brachmann_On_the_Limits_ICCV_2021_supplemental.pdf).

The release is associated with arXiv:1603.05772, **“Learning to Navigate the Energy Landscape.”** Its identity/title is verified; the current release page is the authority used here for data format and licensing. It explicitly says default intrinsics and no performed calibration. Use actual release metadata and captured RGB; do not silently substitute refined poses or rendered training images. [Paper identity](https://arxiv.org/abs/1603.05772), [Current release format](https://graphics.stanford.edu/projects/reloc/).

## 5. Convergence: three bounded experiments

All specifications and numerical thresholds in this section are **ANALYTICAL proposals**, not results. A dated protocol must freeze resolved archive identities, source/checkpoint hashes, device/software settings and manifest before any generation. The present run creates no such stage file and launches nothing.

### E1 — FRESH12_RETRIEVAL (first)

**Question:** Does the fixed nearest-4 rule beat this VMem retrieval package on new recorded rooms, and is that conclusion robust to restoring native retrieval order? Separately, does the S143 geometric/generative ranking mismatch recur?

**Data and windows.**

1. Fix the three rooms above, one from each named scene collection, without substitutions after results. Use only original captured RGB. Before decoding target images, verify scene identities against all project exposure manifests and available stored hashes. If a chosen room has prior project evaluation, stop and amend the protocol before inspecting any replacement.
2. Require two distinct captured traversals identified by original scan/split metadata. Sort their documented identifiers lexicographically and take the first as H and the second as C; make H available before C is queried in the assay. This is an assay ordering, not an assertion about physical acquisition chronology. Validate their common pose frame using bank-only checks. If traversal boundaries cannot be established, declare INELIGIBLE rather than cut arbitrary files into artificial visits.
3. Define N_H and N_C as the full original frame counts of those traversals, without selecting a shorter span. Require at least 20 unique valid H frames and enough C frames for the frozen windows. Sample H indices as floor(j × (N_H−1)/19), j=0…19. Use eight starts s_i=floor(i × (N_C−106)/7), i=0…7, in C's original ordered frame indices. Require distinct starts, distinct target identities across windows, and finite poses for every selected frame. Do not silently compress invalid-frame gaps or search alternate starts; failure is a metadata failure. This is an explicit prospective dataset adaptation, not the literal old chess start list.
4. For each start, bank = those 20 H frames followed by C[s+0,5,…,55]; targets = C[s+60,75,90,105]; static = C[s+0,15,30,45]. H is available before C is queried. No target belongs to its own bank. Context sharing across windows is reported as dependence, not as extra independent samples. The offsets and 20+12 structure come from work/S139_crossseq_revisit/build_manifest_s139.py:10–13.
5. Before scoring, report the pose-only history-favourable stratum using the already defined S139 last-target distance test (pose_arms_s139.py:52–57). Do not select windows by this statistic. If no genuine cross-traversal overlap can be established from permitted inputs, stop the revisit interpretation; do not manufacture it from room labels.
6. Decode RGB dimensions and apply one declared, metadata-consistent color-intrinsic crop/resize contract to the S143 input geometry. Transform color intrinsics by the same pixel affine map; preserve the existing 576×576 scoring/model grid. Require finite positive focal lengths, a verified coordinate convention and bank-only projection sanity checks, while retaining default-intrinsics uncertainty as a limitation. These checks do not establish true physical calibration. Do not copy chess K or assume JPG images are 640×480. Current hard-coded mappings are at gen_s141.py:75–83 and build_pool_s143.py:42–54; transport must be tested on already exposed fixtures before fresh scoring. Target depth remains unused.

**Rules and computation frozen from S143.**

Retain all six rules, K=4, four targets, all-32 candidate nearest distances in fp64, weight 0.1, bank-index ties/order, rng 259 random rule in the declared room/window order, duplicate-set merging, context-only bank CUT3R/KPS construction, niter=0, quarter-resolution union masks, four-frame Q_W reconstruction, SPLAT=1 and nearest fill. Retain the current sampler and scorer, gl conversion, paired seed resets, distinct ctx_group per ordered package and exact-cell validation. Source: S143 PROTOCOL.md:13–47; build_pool_s143.py:56–90; build_plan_s143.py:11–16; gen_s141.py:134–155,170–190.

Mem_vmem must be newly constructed for these banks using the repaired S139 priming contract, with candidates and thresholds saved once. No H800 membership should be guessed or emulated for fresh rooms; compute/cache retrieval under the declared 3090 configuration. This device-specific retrieval provenance is a transport difference from S143's imported H800 memberships.

Add **one robustness arm only: original native order of the same mem_vmem membership**. It stays outside the six-rule selector pool. This does not change the S143 pool's definition or allow a new score-selected package. If identical to sorted order, merge it for generation. Save its geometry separately if needed.

**Seeds and leakage.**

Generate discovery block 3,4,5,6 and evaluation block 42,7,1,2 unconditionally. These are the S143-disjoint blocks, not globally unused seeds. Primary nearest-4 is frozen from chess now; never reselect it on new-room targets. Complete and hash all package predictions before target RGB scoring. Then c_W and c_G may use target scores only as explicitly target-informed assay references. Cache new-scene discovery selectors before reading the evaluation-block score table.

**Primary contrast and threshold.**

Let d_room,s be the mean over that room's eight windows of PSNR(nearest-4) − PSNR(bank-sorted mem_vmem). Average rooms equally, and use the evaluation block for the primary prospective gate:

- overall mean at least +0.20 dB;
- all three room means positive;
- at least three of four seed-panel means positive;
- the same sign and at least +0.20 dB overall against native-order mem_vmem for the broader “retrieval-membership correction” wording.

If only the sorted comparison passes, report a **slot-policy-dependent correction**, not nearest retrieval beating native VMem. Three rooms are too few for a broad population significance claim; report room and seed panels, range/leave-one-room-out sensitivity, and any window bootstrap as descriptive. These are fixed-panel replication criteria.

Mandatory secondary contrasts: nearest − static, nearest − coverage, coverage − mem, rule-selected generation versus same-set copy and warp, and generated SSIM. Do not call nearest better than coverage unless its own paired evidence supports that. Report SSIM regressions explicitly; use an overall decline beyond 0.01 as a predeclared practical reason not to recommend a quality improvement, while retaining the PSNR outcome.

Run the original R_2seed_hindsight and local-versus-global analyses on the six-rule pool with the same folds, bootstrap RNG and null algorithm. Recompute its null thresholds from the new panel; do not transplant chess's realized 0.290753 number. Report frozen four-seed choices on the evaluation block per Amendment 2. These secondary target-informed analyses do not validate a deployable learned selector.

**Controls and stopping.**

Include same-set and whole-bank copy, pure warp, rule 5, original-order mem_vmem, zero-adapter replay on an archived exposed input, and explicit sampler/source/weight hashes. Require four distinct contexts, finite geometry, correct bank coverage, the verified metadata/intrinsic transform, fresh output directories, and exact expected cells. Missing cells, invalid poses, insufficient candidates or geometry failure mean INVALID_ASSAY/INELIGIBLE, not a negative scientific result.

Stop without retuning at the budget cap. If the fixed-rule gate fails, write up no replicated advantage on the new panel. If only R survives, write up target-informed headroom without a usable rule. If generation remains below same-set copy/warp in PSNR, restrict practical claims accordingly. Keep all outcomes.

**Cost.**

Upper bound: 24 windows × 7 packages × 8 seeds = **1,344 four-target generations**, before deduplication. The six-rule core alone is 1,152. Archived S143 medians are 38.42 and 41.18 seconds per generation; logs measure the sampling interval, not all loading/scoring overhead (gen_s141.py:189–199; Appendix A1). At a conservative planning value of 45 seconds, generation is **16.8 GPU-hours**; reserve a **24 GPU-hour total cap** for retrieval, generation and checks. On two available 3090s that is about 12 hours of allocated GPU wall time at the cap. Allow at most roughly eight additional elapsed hours for downloading, metadata qualification, loader transport and CPU scoring/geometry; if the interface/access gates do not fit, do not promise a one-day result. This is a conditional one-day budget, not a benchmark measurement.

### E2 — Identify the cause: candidate pool × query × NMS, with an order control

Run only if E1 establishes a useful fixed correction. This is a mechanism diagnostic on now-exposed data, not another fresh confirmation.

Use the same 24 windows and bank snapshots, base generator, four seeds 42,7,1,2. Cross:

- candidates: all 32 versus the frozen native surfel-filtered list;
- distance-reranking query: last target versus mean of four individual distances;
- diversity: NMS on versus exact top-four without NMS.

Use a common fp64 distance calculation, stable bank-index ties, one saved first-five threshold and fixed bank-order slots. The filtered candidate list remains frozen from native last-target surfel rendering: this factor tests distance reranking, not a change to the surfel render query. Average-target surfel rendering remains untested. This deliberately standardizes numeric behavior; retain archived native results as a reference, and require a documented replay/membership comparison before attributing any discrepancy to the factors. Do not use the stock NMS-off switch, which adds the latest frame.

Primary: NMS-off minus NMS-on averaged over the candidate/query factors. Prespecify simple effects and interactions; inspect candidate-filter and reranking-query contrasts regardless of sign. A claim that NMS is harmful under these tested settings requires at least +0.20 dB, positive room means, and no sign reversal in the matched candidate/query cells. This does not establish that NMS dominates the other factors. If only one cell benefits, report that interaction, not a general NMS defect. No threshold sweep.

Order subcontrol: for fixed native memberships, generate bank order, native order, and a predetermined tail reversal that keeps slot 0 fixed. Hold memberships/geometry fixed for generator-order checks; independently recompute geometry under its order changes without altering generator inputs. Log camera-0 normalization. Full order changes measure an ordered-package effect; they do not isolate temporal attention from coordinate anchoring. Require a practical order effect of at least 0.20 dB before promoting it beyond a numerical confound. Do not enumerate permutations and select a winner.

Cost bound: factorial 24×8×4 = 768 generations; three order policies add at most 288, conservatively counting possible reuse again. At 45 seconds, **13.2 GPU-hours**, plus a **16 GPU-hour cap** including overhead/geometry. If identical selections collapse factorial cells, report non-identifiability and the reduced execution, not an invented zero-effect mechanism. If no component explains a stable advantage, stop the NMS narrative and write up the regime-specific package comparison.

### E3 — Frozen adapter A × retrieval

Optional after E1, only if resolving adaptation versus evidence selection matters to the report. No new training, adapter tuning, or B revival.

On the same 24 windows, cross base versus the final S141 A checkpoint with nearest-4, bank-sorted mem_vmem and static. Use seeds 42,7,1,2, matched hashes and slots. Primary interaction:

I = (A_nearest − A_mem) − (base_nearest − base_mem).

Report A_nearest − base_nearest, A_nearest − A_static, and A_nearest versus same-set copy/warp. A_nearest beating base_mem alone confounds two interventions and cannot establish synergy.

Gate for a positive interaction: I at least +0.20 dB with positive means in all three rooms and at least three seed panels; additionally require A_nearest to exceed A_static by at least +0.20 dB before saying adapted retrieval adds value. A useful additive gain without interaction is reported as additive, not synergistic. Freeze an SSIM practical-loss threshold of −0.01, as in E1. Failure or a nonpositive interaction closes the synergy claim; a wide interval remains inconclusive rather than equivalence.

Upper bound 24×6×4 = 576 generations, **7.2 GPU-hours** at 45 seconds; cap **10 GPU-hours**, potentially less if base cells are exactly reusable. A's checkpoint hash must be verified against the S141 receipt before use; the local result reports only a prefix (work/S141_finetune/RESULT.md:11–12). No claim of weight-byte verification is made by this review.

## 6. Candidates to close now and wording to change

**Write up now:** a generic generator-aware selector, a generic coverage/proximity hybrid, renewed B training, and a learned chess-only utility model. Their novelty is weak, the current scene is exposed, or the immediate predecessor already failed its frozen branch. S141's prescribed B/WORSENS write-up remains intact (work/S141_finetune/RESULT.md:60–68).

The current evidence warrants replacing “retrieval is exhausted; only the consumer can change” with “the tested native retrieval package is not the strongest fixed context rule on this exposed panel.” It does not warrant replacing it with “NMS is the cause,” “geometry is useless,” or “nearest-4 solves memory.”

The three experiments are a bounded decision tree, not an invitation to keep searching. E1 is the next result worth buying. E2 explains a replicated effect; E3 measures an interaction with an already trained adapter. If E1 fails, further tuning consumes the fresh panel without establishing a useful correction, and the correct deliverable is a carefully scoped negative/diagnostic write-up.

Changed by this review: work/agents/CODEX_R264_IDEATION_AFTER_S143.md only. During final inspection, work/S143_context_ranking/RESULT.md also appeared as untracked, consistent with the brief's concurrent-work warning; this review only read it and left it untouched. Suggested follow-up session: freeze and implement E1 after metadata qualification; otherwise incorporate the verified definition differences, order caveat and existing S141/S143 findings into the report. No repository tests or linter were run because no executable source changed; the relevant checks were read-only CPU recomputations, not model tests.

## Appendix A — Exact new verification commands and complete outputs

Commands ran from the repository root. The numerical scripts read archived JSON only, use the existing .venv-cut3r environment, suppress Python bytecode writes, and do not import or execute model code. File reads used for source inspection are cited at their locations above. The four complete command transcripts below are the basis of the new “recomputed/checked” numerical claims. No raw prediction re-score is claimed.

### A1. Discovery arithmetic, package checks, descriptive contrasts and timings

Exact command:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import json, hashlib, subprocess
from pathlib import Path
import numpy as np
P=Path('work/S143_context_ranking')
files=['POOL.json','PROTOCOL.md','build_pool_s143.py','analyze_s143.py','results/WARP_SCORES.json','results/GEN_SCORES_discovery.json','results/S143_ANALYSIS.json']
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
for f in files: print('SHA256',f,hashlib.sha256((P/f).read_bytes()).hexdigest())
pool=json.loads((P/'POOL.json').read_text())['windows']; ws=json.loads((P/'results/WARP_SCORES.json').read_text())['windows']
gs=json.loads((P/'results/GEN_SCORES_discovery.json').read_text())['runs']; saved=json.loads((P/'results/S143_ANALYSIS.json').read_text())
lookup={}
for r in gs.values():
 k=(r['window_id'],r['ctx_key'].split('__')[1],r['seed']); assert k not in lookup; lookup[k]=r
expected={(w['window_id'],s['set_id'],sd) for w in pool for s in w['sets'] for sd in [3,4,5,6]}
assert set(lookup)==expected
Q=np.empty((24,6,4)); W=np.empty((24,6)); S=np.empty_like(Q); copies=np.empty_like(W)
for i,w in enumerate(pool):
 assert len(w['bank'])==32 and len(w['sets'])==6
 assert not set(w['targets'])&set(w['bank'])
 assert len(w['kps_log'])==1 and w['kps_log'][0]['kps']=='OK'
 for ru in range(1,7):
  s=next(s for s in w['sets'] if ru in s['rules']); refs=s['ctx_refs']; order=[w['bank'].index(r) for r in refs]
  assert len(set(refs))==4 and order==sorted(order)
  W[i,ru-1]=ws[w['window_id']]['sets'][s['set_id']]['warp_psnr']
  copies[i,ru-1]=ws[w['window_id']]['sets'][s['set_id']]['copy_set_psnr']
  for j,sd in enumerate([3,4,5,6]): Q[i,ru-1,j]=lookup[(w['window_id'],s['set_id'],sd)]['psnr_db']; S[i,ru-1,j]=lookup[(w['window_id'],s['set_id'],sd)]['ssim']
assert np.isfinite(Q).all() and np.isfinite(W).all() and np.isfinite(S).all()
a=Q[:,:,:2].mean(2); b=Q[:,:,2:].mean(2); wi=np.arange(24); cw=W.argmax(1)
ca=a.argmax(1); cb=b.argmax(1); ra=a.mean(0).argmax(); rb=b.mean(0).argmax()
R=((b[wi,ca]-b[wi,cw])+(a[wi,cb]-a[wi,cw]))/2
G=((b[wi,ca]-b[:,ra])+(a[wi,cb]-a[:,rb]))/2
boot=lambda x: np.percentile(np.random.default_rng(0).choice(x,(10000,len(x))).mean(1),[2.5,97.5])
print('VALID',len(pool),'windows',len(expected),'discovery cells; ordered sets and target exclusion pass')
print('R',round(R.mean(),9),'CI',np.round(boot(R),9).tolist(),'positive',int((R>0).sum()))
print('G',round(G.mean(),9),'CI',np.round(boot(G),9).tolist(),'global_rules',[int(ra+1),int(rb+1)])
assert np.allclose(R,saved['R_2seed_hindsight']['per_window'],atol=1e-12)
assert abs(G.mean()-saved['global_rule_gap']['mean'])<1e-12
for ru in range(6):
 assert abs(Q[:,ru].mean()-saved['per_rule_means'][str(ru+1)]['Q_G'])<1e-12
 print('RULE',ru+1,'QG',round(Q[:,ru].mean(),9),'QW',round(W[:,ru].mean(),9),'SSIM_G',round(S[:,ru].mean(),9),'warp_wins',int((cw==ru).sum()),'copy',round(copies[:,ru].mean(),9))
for left,right in [(4,3),(4,5),(4,1),(5,3)]:
 d=Q[:,left-1].mean(1)-Q[:,right-1].mean(1)
 print('EXPLORATORY',f'{left}-{right}','mean',round(d.mean(),9),'CI',np.round(boot(d),9).tolist(),'wins',int((d>0).sum()))
print('QG_at_cW',round(Q[wi,cw].mean(),9),'rule4_minus_cW',round((Q[:,3]-Q[wi,cw]).mean(),9))
print('historical_context_fraction', {str(ru+1):round(np.mean([sum(r.split('/')[0]!=w['targets'][0].split('/')[0] for r in next(s for s in w['sets'] if ru+1 in s['rules'])['ctx_refs'])/4 for w in pool]),6) for ru in range(6)})
print('nearest_coverage_overlap_mean',round(np.mean([len(set(next(s for s in w['sets'] if 4 in s['rules'])['ctx_refs'])&set(next(s for s in w['sets'] if 5 in s['rules'])['ctx_refs'])) for w in pool]),6))
for f in sorted((P/'results/tacc').glob('gen_part*/RUNS*.jsonl')):
 rows=[json.loads(x) for x in f.read_text().splitlines()]; sec=np.array([r['seconds'] for r in rows])
 print('TIMING',str(f),'n',len(rows),'sum_seconds',round(sec.sum(),2),'median',round(np.median(sec),2),'p95',round(np.percentile(sec,95),2),'first',rows[0]['recorded_utc'],'last',rows[-1]['recorded_utc'])
print('Saved null diagnostics (not rerun)',json.dumps(saved['nulls'],sort_keys=True))
PY
```

Complete output:

```text
HEAD 532c29ee4d26674634a91d9f6786cbb24978e5cf
SHA256 POOL.json 0eea09978b17f71491a459651e9c39a2925af97f948c9b597406b48d7957cad5
SHA256 PROTOCOL.md 84285e175c259d16a54b1bd3addc45e25db756b601bf05b239d83ef536795ac5
SHA256 build_pool_s143.py a338a7cc54fc9d64701f11c5c9c2de6e56f9cd6f12d175069275d2a80f6165d1
SHA256 analyze_s143.py 0ca8aed655e70016b4b4fa449cd28c7428f8ebed4e06400f9c282a6dd3b2b1b6
SHA256 results/WARP_SCORES.json d0d4ded32f166e53bdabf9aeacde6675a12f3ede4a127f283d35d607951b3982
SHA256 results/GEN_SCORES_discovery.json f479da778246dc2475bd405db4c1b3a28920ad7f65b3dc90c4faa80175ac9fe8
SHA256 results/S143_ANALYSIS.json 22c5b75a4d7783d93da307d6b5bb725b2dd92755280401b9b550bb15b05eeed3
VALID 24 windows 576 discovery cells; ordered sets and target exclusion pass
R 0.320442655 CI [0.186214069, 0.458037416] positive 18
G 0.275301071 CI [0.119792048, 0.444961054] global_rules [4, 4]
RULE 1 QG 11.489224924 QW 13.114015641 SSIM_G 0.48696299 warp_wins 1 copy 11.637885959
RULE 2 QG 11.578046204 QW 14.302340102 SSIM_G 0.483564847 warp_wins 1 copy 11.776925324
RULE 3 QG 11.190094111 QW 14.37810791 SSIM_G 0.464563165 warp_wins 1 copy 11.44233028
RULE 4 QG 11.937004554 QW 14.297765238 SSIM_G 0.499999993 warp_wins 6 copy 12.187744242
RULE 5 QG 11.917725371 QW 15.414303471 SSIM_G 0.492740843 warp_wins 14 copy 12.193852652
RULE 6 QG 11.380289371 QW 14.051417766 SSIM_G 0.482121305 warp_wins 1 copy 11.688496021
EXPLORATORY 4-3 mean 0.746910443 CI [0.487574408, 1.01574103] wins 19
EXPLORATORY 4-5 mean 0.019279183 CI [-0.190929986, 0.23568366] wins 14
EXPLORATORY 4-1 mean 0.44777963 CI [0.184680404, 0.731572476] wins 17
EXPLORATORY 5-3 mean 0.727631259 CI [0.431829556, 1.019175058] wins 18
QG_at_cW 11.89186297 rule4_minus_cW 0.045141584
historical_context_fraction {'1': 0.0, '2': 0.791667, '3': 0.885417, '4': 0.291667, '5': 0.677083, '6': 0.614583}
nearest_coverage_overlap_mean 1.458333
TIMING work/S143_context_ranking/results/tacc/gen_part0/RUNS_gpu13_4044496.jsonl n 288 sum_seconds 11858.73 median 41.18 p95 41.3 first 2026-10-10T19:19:00.416747+00:00 last 2026-10-10T22:37:00.671395+00:00
TIMING work/S143_context_ranking/results/tacc/gen_part1/RUNS_gpu13_4045107.jsonl n 288 sum_seconds 11063.7 median 38.42 p95 38.46 first 2026-10-10T19:19:14.219420+00:00 last 2026-10-10T22:24:00.273936+00:00
Saved null diagnostics (not rerun) {"indep": {"G_null95": 0.08941226954177786, "G_tail_p": 1.999980000199998e-05, "R_null95": 0.09806461395305924, "R_null_mean": 0.0002212577073788809, "R_null_sd": 0.05821715743261258, "R_tail_p": 1.999980000199998e-05}, "panel": {"G_null95": 0.21602161861872626, "G_tail_p": 0.014669853301466985, "R_null95": 0.2907530525956509, "R_null_mean": 0.0005868273947215826, "R_null_sd": 0.17644989905087666, "R_tail_p": 0.03453965460345396}}
```

### A2. Independent vectorized recomputation of both frozen nulls

Exact command:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv-cut3r/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np
P=Path('work/S143_context_ranking'); pool=json.loads((P/'POOL.json').read_text())['windows']
gs=json.loads((P/'results/GEN_SCORES_discovery.json').read_text())['runs']; ws=json.loads((P/'results/WARP_SCORES.json').read_text())['windows']; saved=json.loads((P/'results/S143_ANALYSIS.json').read_text())
lookup={(r['window_id'],r['ctx_key'].split('__')[1],r['seed']):r['psnr_db'] for r in gs.values()}
Q=np.array([[[lookup[(w['window_id'],s['set_id'],sd)] for sd in [3,4,5,6]] for s in w['sets']] for w in pool])
W=np.array([[ws[w['window_id']]['sets'][s['set_id']]['warp_psnr'] for s in w['sets']] for w in pool]); cw=W.argmax(1)
E=Q-Q.mean(2,keepdims=True); rng=np.random.default_rng(143); B=100000
for name in ['panel','indep']:
 rr=[]; gg=[]
 for offset in range(0,B,1000):
  if name=='panel':
   z=rng.standard_normal((1000,4,4)); x=np.einsum('wrk,bsk->bwrs',E,z)/np.sqrt(3)
  else:
   z=rng.standard_normal((1000,24,4,4)); x=np.einsum('wrk,bwsk->bwrs',E,z)/np.sqrt(3)
  a=x[:,:,:,:2].mean(3); b=x[:,:,:,2:].mean(3)
  ai=a.argmax(2); bi=b.argmax(2); ar=a.mean(1).argmax(1); br=b.mean(1).argmax(1)
  take=lambda v,ix: np.take_along_axis(v,np.broadcast_to(ix,(1000,24))[:,:,None],axis=2)[:,:,0]
  r=((take(b,ai)-take(b,cw))+(take(a,bi)-take(a,cw)))/2
  g=((take(b,ai)-take(b,ar[:,None]))+(take(a,bi)-take(a,br[:,None])))/2
  rr.extend(r.mean(1)); gg.extend(g.mean(1))
 rr=np.array(rr); gg=np.array(gg)
 out={'R_null95':float(np.percentile(rr,95)),'R_tail_p':float((1+(rr>=saved['R_2seed_hindsight']['mean']).sum())/(B+1)),'G_null95':float(np.percentile(gg,95)),'G_tail_p':float((1+(gg>=saved['global_rule_gap']['mean']).sum())/(B+1))}
 print(name,json.dumps(out,sort_keys=True)); print('max_abs_difference_from_archive',max(abs(v-saved['nulls'][name][k]) for k,v in out.items()))
PY
```

Complete output:

```text
panel {"G_null95": 0.21602161861872632, "G_tail_p": 0.014669853301466985, "R_null95": 0.29075305259565093, "R_tail_p": 0.03453965460345396}
max_abs_difference_from_archive 5.551115123125783e-17
indep {"G_null95": 0.08941226954177786, "G_tail_p": 1.999980000199998e-05, "R_null95": 0.09806461395305924, "R_tail_p": 1.999980000199998e-05}
max_abs_difference_from_archive 0.0
```

### A3. Membership/order comparison, S141 primary and source hashes

Exact command:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import json,hashlib
from pathlib import Path
import numpy as np
P=Path('work/S143_context_ranking'); pool=json.loads((P/'POOL.json').read_text())['windows']; a=json.loads((P/'results/S143_ANALYSIS.json').read_text()); old=json.loads(Path('work/S139_crossseq_revisit/plan.json').read_text())['contexts']; b=json.loads(Path('work/S141_finetune/results/S141_ANALYSIS.json').read_text())
changes=anchors=0
for w in pool:
 x=next(c['ctx_refs'] for c in old if c['window_id']==w['window_id'] and 'mem_vmem' in c['arms']); y=next(s['ctx_refs'] for s in w['sets'] if 3 in s['rules']); assert set(x)==set(y)
 changes+=x!=y; anchors+=x[0]!=y[0]
print('mem_vmem_memberships_identical',len(pool),'order_changed',changes,'slot0_changed',anchors)
for key,oldkey in [('Q_G','base_mem'),('Q_W','B2_warp_mem')]:
 oldv=b['means']['psnr_db'][oldkey]; newv=a['per_rule_means']['3'][key]
 print(key,'original',round(oldv,9),'bank_sorted',round(newv,9),'difference',round(newv-oldv,9))
print('S141 PSNR primary', json.dumps(b['contrasts']['psnr_db']['PRIMARY_A: A_mem - base_mem'],sort_keys=True))
for p in ['data/S134_tacc/vmem_src/modeling/pipeline.py','work/S141_finetune/gen_s141.py','work/S141_finetune/RESULT.md']:
 print('SHA256',p,hashlib.sha256(Path(p).read_bytes()).hexdigest())
print('GPU-hour projections at 45 seconds per generation:',{str(n):n*45/3600 for n in [1152,1536,576]})
PY
```

Complete output:

```text
mem_vmem_memberships_identical 24 order_changed 22 slot0_changed 20
Q_G original 11.274894431 bank_sorted 11.190094111 difference -0.084800319
Q_W original 14.572387742 bank_sorted 14.37810791 difference -0.194279832
S141 PSNR primary {"ci95": [0.07821663972646646, 0.5848574621557386], "history_favourable": {"ci95": [0.2970626731535926, 0.8363898586329375], "mean": 0.5722030823447285, "n": 16, "verdict": "IMPROVES", "wins": 13}, "mean": 0.330455947375833, "n": 24, "per_pair": {"seq-01->seq-02": 0.5226408204889166, "seq-04->seq-03": 0.2092937154595227, "seq-06->seq-05": 0.2594333061790597}, "verdict": "IMPROVES", "wins": 17}
SHA256 data/S134_tacc/vmem_src/modeling/pipeline.py 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255
SHA256 work/S141_finetune/gen_s141.py c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121
SHA256 work/S141_finetune/RESULT.md 9e86f2384e3d9e3d066339cf212f6ca6d7c9452e3e97e1e9cf495f05ad3fe6be
GPU-hour projections at 45 seconds per generation: {'1152': 14.4, '1536': 19.2, '576': 7.2}
```

### A4. Official 12-Scenes archive HEAD requests; no archive bodies

Exact command:

```sh
python3 - <<'PY'
import urllib.request
for name in ['apt1','apt2','office1','office2']:
 u=f'https://graphics.stanford.edu/projects/reloc/data/{name}.zip'
 try:
  with urllib.request.urlopen(urllib.request.Request(u,method='HEAD'),timeout=20) as r:
   print(name,'status',r.status,'content-length',r.headers.get('Content-Length'),'content-type',r.headers.get('Content-Type'))
 except Exception as e: print(name,type(e).__name__,str(e))
PY
```

Complete output:

```text
apt1 status 200 content-length 1489122810 content-type application/zip
apt2 status 200 content-length 3001378406 content-type application/zip
office1 status 200 content-length 6298846857 content-type application/zip
office2 status 200 content-length 1849269665 content-type application/zip
```
