# Memory Mechanisms in Video World Models (2025–2026)

**Sub-area surveyed:** memory *mechanisms* (what is stored, how it is written, how it is updated / invalidated, how it is read) — deliberately **not** benchmarks.
**Compiled:** September 2026. Every row below was read from a page I actually fetched. Where I could not verify something I write **UNVERIFIED**.

**Reading conventions used throughout:**
- "The paper claims X" = X is asserted in the abstract/body of the fetched page. It is not an endorsement.
- All URLs are resolved to `arxiv.org` / official venue pages. Search-result mirrors (`*.ezproxy.*`, `ar5iv`, `semanticscholar`, `huggingface`) were used only for *discovery*; every claim below traces to the primary page.
- Venue labels: "arXiv preprint" means I verified only the arXiv posting, **not** peer review. Where a venue is stated, it came from the paper's own comments/journal-reference field.

---

## 0. Verification of the papers the project already flagged

All six were verified to exist. Two characterisations circulating in the project notes need correction or downgrading.

| Flagged item | Verified | Notes / corrections |
|---|---|---|
| Geometry-Aware Implicit Memory for Video World Models (2606.02436) | ✅ Yes | Real. Method name is **GIM-World**. Submitted 1 Jun 2026, cs.CV, Kling Team (Kuaishou) + Nanjing Univ. Contains the single most GRC-relevant mechanism I found (see §4). |
| "Mirage" / latent spatial memory (2606.09828) | ✅ Yes | The **arXiv title is "Latent Spatial Memory for Video World Models"**, the **method name is LSM-World**, and "Mirage" is the *project* name (project page `aka.ms/latent-spatial-memory`; Microsoft Research + Zhejiang Univ). v1 8 Jun 2026, v2 27 Aug 2026. Cite the arXiv title, not "Mirage", to avoid a mismatch. |
| AlayaWorld (2607.06291) | ✅ Yes | Real, 7 Jul 2026, cs.CV + cs.HC. **The abstract does not describe the memory mechanism at all** — it presents a full-stack framework (data → architecture → training → acceleration → deployment). Characterising it as a *memory mechanism* paper is **UNVERIFIED**; this needs the full text. |
| UCM (2602.22960) | ✅ Yes | Full title: "UCM: Unified Modeling of Camera Control and Memory with Time-aware Positional Encoding Warping for World Models." v1 26 Feb 2026, v2 29 Jun 2026. Also has an ACM DL entry (DOI `10.1145/3799902.3811088`) per search results — **venue not verified by me**, treat as arXiv-preprint-confirmed only. |
| Wonder (2607.26037) | ✅ Yes | Real, 28 Jul 2026. Memory mechanism = "efficient sparse attention-based memory mechanism" attending to a small set of relevant context tokens at inference regardless of context length. |
| Plug-and-play Memory (2511.19229) | ✅ Yes | Real. Method name **DiT-Mem**. v1 24 Nov 2025, v2 27 Nov 2025. Note: it is **appearance/world-knowledge injection**, not spatial-historical memory — weaker fit to this sub-area than the others. |
| ReMind (2605.25333) | ✅ Yes | Full title: "Teaching Video Generators to Remember: Eliciting Dynamic Memory for Out-of-Sight State Evolution." v1 25 May 2026, v2 30 Jul 2026. ⚠️ **The project's description "event anchors + history cache replacement" is only half-supported.** The abstract describes *protected anchors* in a frame graph, degraded intervals, temporal gaps, a node-structured curriculum (node-drop, noisy memory, frontier continuation, reference-cache training), cache adaptation, and PM-RoPE. **"History cache replacement" as a replacement/eviction policy is UNVERIFIED** — I did not read the full text. |
| ViewRope (2602.07854) | ✅ Yes | Full title: "Geometry-Aware Rotary Position Embedding for Consistent Video World Model." v3 21 Feb 2026. Project's description ("geometry-conditioned historical frame selection") is **accurate**: ViewRope + *Geometry-Aware Frame-Sparse Attention* → "selectively attend to relevant historical frames", plus a ViewBench diagnostic suite. |

**Not re-reported as new** (already known to the project, mentioned only where they bear on threats/gaps): GeoVideo, World-consistent Video Diffusion, Geometry-guided Online 3D Video Synthesis, Video World Models with Long-term Spatial Memory, Context-as-Memory, MVD-Fusion, MVGD, MVDD.

---

## 1. Landscape table

| Title | Venue / Year | URL | Mechanism in one sentence | What it does NOT do |
|---|---|---|---|---|
| **GIM-World**: Geometry-Aware Implicit Memory for Video World Models | arXiv preprint, Jun 2026 | https://arxiv.org/abs/2606.02436 | Compresses variable-length history into a **fixed-size set of memory tokens**; a training-only camera-queryable geometry head distils 3D structure from a frozen foundation model into those tokens; **history is pruned before encoding by maximizing mutual information I(S; H\S) subject to \|S\| ≤ K**. | Does not score observations by expected **future** error, never revises already-written memory, and its geometry teacher exists only at training time. |
| **LSM-World** ("Mirage"): Latent Spatial Memory for Video World Models | arXiv preprint, Jun 2026 (v2 Aug 2026) | https://arxiv.org/abs/2606.09828 | Persistent 3D cache of `(world_point, VAE_latent_token)` pairs, built by depth-guided back-projection and read by **z-buffered latent-resolution projection** into a ControlNet-style branch. | Writes are **union-only** (`M ← M ∪ {…}`) — no dedup, merge, eviction, or revision; no per-observation risk score; dynamic objects + sky merely filtered out. |
| **MosaicMem**: Hybrid Spatial Memory for Controllable Video World Models | arXiv preprint, Mar 2026 | https://arxiv.org/abs/2603.17117 | The memory unit is the **patch**: patches are lifted to 3D and **re-composed in the queried view** ("patch-and-compose"), with warped-RoPE and warped-latent alignment; explicitly deletable/relocatable. | Retrieval is not driven by a learned risk or future-error signal; consistency is bought by *avoiding* global reconstruction, not by scoring/correcting individual memories. |
| **VMem**: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory | **ICCV 2025 (highlight)** per paper comments | https://arxiv.org/abs/2506.18903 | Surfel-indexed view memory: each surfel stores `(position, normal, radius, {observing-view indices})`; new views retrieved by rendering visible surfels and **voting on view indices → top-K + non-maximum suppression**. | Assumes a **static** scene; write is additive merge that discards the *older* of two near-duplicate poses; no notion of a memory being *wrong*; no future-error objective. |
| **Mem-World** (W-VMem) | arXiv preprint, Jun 2026 | https://arxiv.org/abs/2606.18960 | 4D wrist-view-centred surfel memory with per-surfel **creation/merge timestep** and a **manipulated-object flag**; historical frames scored by geometric visibility × task relevance × temporal decay, then **Top-K + NMS**. | The score is a **fixed hand-designed heuristic** — not learned, not tied to future prediction error; memory is never corrected. |
| **WorldPlay** | arXiv preprint, Dec 2025 (v2 Jun 2026) | https://arxiv.org/abs/2512.14614 | "Reconstituted Context Memory" **dynamically rebuilds context** from past frames and uses temporal reframing to keep geometrically important long-past frames accessible; "Context Forcing" aligns teacher/student memory context under distillation. | No explicit 3D cache; the retention policy is not risk- or error-scored. |
| **LayerRecall**: A State-Conditioned Memory Router | arXiv preprint, Aug 2026 | https://arxiv.org/abs/2608.28460 | Current-conditioned, **layer-selective router** retrieves historical K/V states and injects them only into backbone layers that prefer long-range context; trained by **Cross-Horizon Prediction Matching (CHPM)** against a privileged long-context reference in prediction space. | Operates on **K/V token memory**, not a 3D/geometric cache; retrieval conditioned on current state, not on per-observation geometric risk. |
| **WorldTrace**: Addressable Memory for Video World Models | arXiv preprint, Aug 2026 | https://arxiv.org/abs/2608.07408 | Training-free: assigns each compressed KV summary slot a **distinct in-distribution virtual RoPE position** so the cache stays addressable; WorldTrace-Field compresses for temporal coherence, WorldTrace-Landmark stores verbatim traces at detected transitions. | An addressability fix, not risk-based selection; no geometric reasoning; shows naively compressing in RoPE space *corrupts* memory by averaging incompatible phases. |
| **AnchorWeave**: World-Consistent Video Generation with Retrieved Local Spatial Memories | **ECCV 2026** per paper comments | https://arxiv.org/abs/2602.14941 | Replaces one **globally fused** 3D memory with **multiple clean local geometric memories** and retrieves them by **coverage along the target trajectory**, reconciling cross-view inconsistency via a multi-anchor weaving controller. | Attacks cross-view *misalignment*, not the riskiness of an observation; retrieval is coverage-driven, not error- or risk-driven. |
| **Memorize When Needed**: Decoupled Memory Control | arXiv preprint, Apr 2026 | https://arxiv.org/abs/2604.18215 | Decoupled lightweight memory branch with a hybrid memory representation; **per-frame cross-attention** conditions each frame only on the most spatially relevant history; a **camera-aware gate** enables memory only when meaningful historical references exist. | Relevance is spatial only; no budget formulation, no geometry-risk estimate, no memory correction. |
| **SlotMemory**: Object-Centric KV Memory for Streaming Long-Video Generation | arXiv preprint, May 2026 | https://arxiv.org/abs/2605.31033 | Shifts the memory abstraction from *"when"* to *"what"*: decomposes the transformer's **KV manifold into discrete reusable semantic slots** used as routing addresses to index/store high-fidelity K/V tokens at entity level. | Object/semantic slots, not geometry; no 3D spatial index; no risk/uncertainty scoring; no invalidation policy is described. |
| **MemLearner**: Learning to Query Context Memory | **ECCV 2026** per paper comments | https://arxiv.org/abs/2606.31734 | **Learning-based adaptive context query** using query tokens to bridge context and predicted tokens, reusing the generator's own visual priors instead of rule-based frame retrieval. | Learned relevance ≠ geometric risk; no explicit compute budget or future-error objective. |
| **ReMind** | arXiv preprint, May 2026 (v2 Jul 2026) | https://arxiv.org/abs/2605.25333 | Elicits KV-cache-as-dynamic-memory via memory-oriented data, event-aware training and cache adaptation: frame graph with **protected anchors / degraded intervals / explicit temporal gaps**, node-structured curriculum, **PM-RoPE** camera-phase RoPE extension. | No explicit 3D/geometric memory; no per-observation risk score; "history cache replacement" unverified. |
| **ViewRope** | arXiv preprint, Feb 2026 | https://arxiv.org/abs/2602.07854 | Injects **camera-ray directions directly into self-attention** as a geometry-aware relative-ray encoding, then uses **Geometry-Aware Frame-Sparse Attention** to selectively attend to relevant historical frames. | Selection is cue-based/heuristic; no risk estimation; no memory store that can be corrected. |
| **UCM** | arXiv preprint, Feb 2026 (v2 Jun 2026) | https://arxiv.org/abs/2602.22960 | Unifies long-term memory and camera control through **time-aware positional-encoding warping**, with a dual-stream DiT and a point-cloud-rendering data-curation strategy simulating revisits. | The abstract describes positional-encoding warping, not a scored/risk-aware memory; no budget or correction mechanism stated. |
| **Wonder**: Video World Model Done Better | arXiv preprint, Jul 2026 | https://arxiv.org/abs/2607.26037 | **Sparse-attention memory mechanism** attending to a small set of relevant context tokens at inference regardless of actual context length, plus dense-coordinate-field camera conditioning. | Token-level sparse attention, not a geometric memory; no risk/error-based selection objective described. |
| **AlayaWorld** | arXiv preprint, Jul 2026 | https://arxiv.org/abs/2607.06291 | Full-stack open-source framework for real-time interactive generative worlds (data preparation → architecture → training → acceleration → deployment). | ⚠️ **Memory mechanism UNVERIFIED** — the abstract does not describe one. Needs full-text read before citing as a memory mechanism. |
| **DiT-Mem**: Learning Plug-and-play Memory | arXiv preprint, Nov 2025 | https://arxiv.org/abs/2511.19229 | Learnable memory encoder (stacked 3D CNNs + low-/high-pass filters + self-attention) maps reference videos into compact memory tokens concatenated inside DiT self-attention; backbone frozen, only 150M encoder params trained. | Injects **appearance/physical-rule world knowledge**, not spatial history; no write/update/invalidate policy; no risk or budget. |
| **Closing the Loop** | arXiv preprint, Jul 2026 | https://arxiv.org/abs/2607.21848 | Training-free revisit consistency: **temporal correspondence** pulls pose-matched historical latent chunks into the KV cache as loop-closure memory; **spatial correspondence** (pose + depth reprojection) biases token attention toward geometrically corresponding regions. | Requires engine-provided depth/pose/correspondence; memory is inserted *for* revisits rather than scored by risk; no maintained 3D cache. |
| **Composition of Memory Experts** | **ICLR 2026** (journal-ref in arXiv record) | https://arxiv.org/abs/2605.18813 | Contrastive **product-of-experts over heterogeneous memories**: short-term (local dynamics), long-term (episodic history in external diffusion weights via lightweight test-time finetuning), and spatial long-term (geometric/spatial coherence) experts. | An architectural composition; the spatial expert enforces coherence but this is not a budgeted risk-based selection over observations. |
| **Towards Error-Free Long Video Generation** | arXiv preprint, Jun 2026 | https://arxiv.org/abs/2606.22370 | Causal (unidirectional) attention **between** clips with bidirectional attention **within** a clip, a **constant-size KV cache**, and truncation-rectified flow (T-RFlow) to suppress error accumulation / attribute drift. | KV cache is constant-size but not selectively scored; no geometric memory; no correction of wrong state. |
| **Future Forcing** | arXiv preprint, May 2026 | https://arxiv.org/abs/2605.30083 | Training-free **future-aware KV policy**: builds a *future query proxy* from the approximately stationary canonical pre-RoPE query distribution, scores KV tokens by importance under that proxy, then merges redundant token pairs in the induced affine subspace. | Token-level KV budget; no geometry, no 3D memory, no per-observation risk. |
| **PaFu-KV**: Past- and Future-Informed KV Cache Policy | arXiv preprint, Jan 2026 (v3 Feb 2026) | https://arxiv.org/abs/2601.21896 | Distils a lightweight **Salience Estimation Head** from a bidirectional teacher to score KV tokens with past- *and* future-informed salience, retaining informative tokens and discarding the rest. | Token salience, not geometric risk; no 3D cache. |
| **Echo-Memory**: A Controlled Study of Memory in Action World Models | arXiv preprint, Jun 2026 | https://arxiv.org/abs/2606.09803 | Fixes backbone/optimizer/sampler and varies **only how history is stored and read**; separates four conflated axes — *capacity, compression, read-out, recurrence* — under a three-branch protocol (replay, in-domain loop revisit, open-domain return). | A controlled study, not a new selection mechanism; proposes no risk- or future-error-driven memory selection. |
| **On Memory**: A comparison of memory mechanisms in world models | arXiv preprint, Dec 2025 | https://arxiv.org/abs/2512.06983 | Taxonomy separating **memory encoding** from **memory injection**, motivated via residual-stream dynamics; measures effective memory span on a state-recall task. | Small-scale analysis of encoding/injection; no geometry, no risk/budget selection. |
| **WorldDirector** | arXiv preprint, Jul 2026 | https://arxiv.org/abs/2607.02517 | Decouples **semantic motion orchestration** (LLM-coordinated 3D trajectories) from visual generation, so dynamic entities keep exact visual identity after prolonged out-of-view periods. | Persistence comes from trajectory orchestration, not a learned/geometric memory store; no risk/budget formulation. |
| **Towards Interactive Video World Modeling** (survey) | arXiv preprint, May 2026 | https://arxiv.org/abs/2606.01164 | Systematic review of interactive world modelling with a dedicated technical-challenge section on **long-horizon interactions and memory**, plus benchmarks across four application fields. | Survey; no mechanism proposal. |

---

## 2. The five most relevant papers — exact mechanism

### 2.1 GIM-World — Geometry-Aware Implicit Memory (arXiv 2606.02436)
*Selected because its pruning rule is the closest existing thing to "select a budgeted memory subset by an information/uncertainty criterion".*

- **Storage.** A fixed-size set of `N_m` learnable **memory queries** `Q_0`; after two encoder blocks the first `N_m` tokens become the memory `m`. Memory size **does not grow with history**; the paper claims the encoder runs in **<0.3% of the diffusion backbone's time**. Stored content is not a 3D structure — geometry is enforced indirectly as a *property* of the tokens.
- **Write.** History patch tokens are camera-tagged (`h̃ = h + E_c(c_i)`) while the memory queries stay **pose-free**. Queries + history are concatenated and passed through the encoder; compact self-attention runs at `(N_m + T·H_p·W_p)/s²` tokens. Conditioned onto the DiT by concatenating along the temporal axis, **following Context-as-Memory**. Critically: the state is **recomputed from history**, not incrementally patched — there is no per-item write/commit decision.
- **What geometry supervision does.** A training-only **camera-queryable geometry head** takes a sampled historical camera, builds per-patch world-space ray queries `ρ = [o_i, d_{i,u,v}]`, cross-attends over the memory, and is aligned by per-patch cosine loss to a **frozen VGGT** feature map. The head + teacher are **discarded at inference**. The paper's own stated reason for querying by camera rather than token-matching is that token matching "would impose an artificial ordering on the memory slots and collapse the representation back toward a frame-indexed cache."
- **The pruning rule (the important part).** To bound encoding cost, GIM-World keeps a subset `S ⊆ H` with `|S| ≤ K` maximizing `I(S; H\S)` — i.e. the **mutual-information sensor-placement criterion of Krause et al.**, optimized greedily. `I(S; H\S)` is evaluated with a **Gaussian process over per-frame observations using a pose-time RBF kernel** `k(c_i,c_j)` over camera position, forward direction, and time. Posterior variance `σ²(h|A)` quantifies "remaining uncertainty about frame h after observing A". So the selection signal is **per-frame uncertainty, geometrically/kinematically parameterised, under an explicit cardinality budget**.
- **Update / invalidate.** **None.** The memory is a function of the current history; nothing is committed, revised, forgotten, or merged. Errors cannot be traced to an individual stored item.
- **What this means for GRC.** This is a *partial pre-emption of the framing*: "geometry-aware + budgeted + uncertainty-scored memory selection" already exists. The remaining differences are (i) the objective is information about **omitted history**, not **future state prediction error**; (ii) the score is a GP posterior variance over a fixed kernel, not a learned risk of a wrong observation; (iii) selection is over **raw frames to be encoded**, not over a persistent 3D cache.

### 2.2 VMem — Surfel-Indexed View Memory (ICCV 2025, arXiv 2506.18903)
*Selected as the canonical geometric-memory read/write architecture that most later 2026 work extends.*

- **Storage.** Surfel set `S^(s) = {s_k}`, each `s_k = (p_k ∈ R³, n_k ∈ R³, r_k, I_k)` where `I_k ⊆ {1..T}` is the **set of past view indices that observed this surfel**. Plus an **octree** for fast geometric retrieval, and a view database `V^(s)` of `(RGB image, camera params)`. The stored payload is *indices into views*, not features — a deliberate indirection.
- **Read.** Compute the **average pose** `c̄_s` of the target cameras; render/splat visible surfels from it **with occlusion and relative depth**; each rendered pixel votes for view indices; **rank view indices by frequency across all rendered pixels** and take **top-K**. The stated intuition: "views observing the largest portion of the scene from the perspective of the novel camera are most relevant."
- **Read-time dedup.** To avoid oversampling repeatedly visited regions, a **non-maximum suppression** step keeps "only the most frequently referenced view among those with similar poses" — i.e. **memory redundancy is suppressed at read time by pose similarity**.
- **Write.** Estimate point maps for new views **jointly with the retrieved past views** (using an off-the-shelf point-map estimator, CUT3R) so new geometry lands in the **existing coordinate frame**; downsample by `σ`; derive normals by cross-products of neighbouring-pixel displacements; set a heuristic radius `r = (½·D/f) / (α + (1−α)|n·(p−O)|)` that is depth-proportional and inverse-focal/inverse-cosine-scaled.
- **Write-time merge / invalidation.** A new surfel is matched to an existing one if **centres are within `d` and normal cosine similarity exceeds `θ`**; on match, append the frame index (`I_k ← I_k ∪ {t}`) and discard the new surfel; otherwise add it with `I = {t}`. Separately: "we merge surfels by comparing their associated camera poses — **if two poses are highly similar, we discard the older one**."
- **What it does NOT do.** The memory has **no representation of being wrong**. There is no confidence, no residual, no correction: a surfel that was born from a bad depth estimate persists and keeps attracting view votes. Eviction is by **pose redundancy**, never by error or surprise. Scene assumed static (Mem-World's whole contribution is relaxing exactly this).
- **Key quantitative claim (paper's):** comparable performance with **4× fewer context views** and a **12× speedup**; the paper also argues explicitly that "it does not require highly accurate scene geometry. As long as we successfully retrieve the most relevant past views, our method remains robust."

### 2.3 Mem-World / W-VMem (arXiv 2606.18960)
*Selected because it is the most explicit attempt to **score** historical observations geometrically and select a budgeted, non-redundant subset for a *future* prediction.*

- **Storage.** Extends VMem's surfel `(p, n, r, I)` with **temporal and task attributes**: `s_k = (p_k, n_k, r_k, t_k, m_k)` where `t_k` is the set of timesteps at which the surfel was created/updated and `m_k ∈ {0,1}` flags **manipulated-object** surfels (obtained via a VLM reading the instruction + first frame, then segmentation). Initialised from the **first frame of three camera views**.
- **Write policy (notable asymmetry).** Updates use **only the wrist-view frame**, not the third-person views. The paper's stated reason is instructive: if third-person observations updated surfels, "their global field of view would cause most visible surfels to be repeatedly refreshed and assigned almost all timestamps", destroying the timestamp→observation association. This is an explicit **"which sensor is allowed to write"** policy — a write-gating decision by information specificity.
- **Read / scoring.** Future wrist-camera poses are obtained from future **actions** by forward kinematics (wrist camera rigidly mounted to end-effector), then transformed into the point-cloud frame. Surfels are rendered **per-timestep individually** rather than jointly (deliberately, so temporal cues are not blurred), and each rendered surfel gets
  `score(s,t) = ⟨n_s, v̄_w⟩ / (1 + d_s) · ln(e + m_s) · [λ_min + (1−λ_min)·2^(−(T−t)/H)]`
  i.e. **geometric visibility** (normal alignment × inverse depth) × **task relevance** (object flag) × **temporal recency** (half-life `H`, floor `λ_min = 0.1`).
- **Selection.** Per-timestep scores → **`TopK-NMS`** over candidate observations, explicitly "to avoid redundancy … mitigates oversampling of repeatedly visited regions, such as cases where the wrist camera hovers above the manipulated object during a pick operation, and promotes broader scene coverage".
- **Update.** Surfels from predicted observations are merged back into memory each rollout step (iterate render → score → select → generate → update).
- **Why this matters for GRC.** It is a genuine **geometry-aware, budgeted (top-K), redundancy-suppressed memory selection for future-state prediction** — and its own ablation shows the retrieved context beats stride-based (Ctrl-World/EVAC) and short-term (Interactive World Simulator) memory substantially (wrist view PSNR 18.97 vs 17.06 vs 15.04). The residual gap for GRC is that the score is a **hand-designed closed-form product of three heuristics**, has **no learned notion of risk that an observation is misleading**, and is **never validated against a predicted-error target** — it optimises expected informativeness, not expected error reduction.

### 2.4 LSM-World / "Mirage" — Latent Spatial Memory (arXiv 2606.09828)
*Selected as the current state of the art in 3D-cache-based conditioning — the architecture GRC's pipeline most resembles, and the one whose write policy most plausibly produces ghosting.*

- **Storage.** `M = {(p_i, f_i)}` — each memory element pairs a **world-space 3D coordinate** with a **VAE latent token `f_i ∈ R^C`** drawn directly from the diffusion VAE encoder, i.e. memory lives in the backbone's native latent space rather than RGB. One element per latent-grid cell. Claimed **55× smaller cache footprint** and up to **10.57× faster end-to-end** generation vs RGB point-cloud memories.
- **Write (initialise).** Initial frame → VAE latent `z`; downsample depth `D` to the latent grid and rescale intrinsics; back-project each cell `p_uv = π⁻¹(u,v,D(u,v); K,E)`; store `F_uv = z[:,v,u]`. One memory element per latent cell.
- **Read.** Project all memory points onto the target latent grid; **z-buffer** to keep the frontmost point per cell; return its latent token; produce a **binary visibility mask** so the denoiser can distinguish "genuinely unseen" from "observed but zero". Concatenate readout + mask into a **ControlNet-style side branch**; segment-aware rotary encodings mark noisy-target / clean-preceding / clean-reference frames. Cells with no projection are **zero-filled**.
- **Update.** `M ← M ∪ {(p_uv, F_uv)}` over `Λ^t` = latent cells with valid depth **outside dynamic objects and sky**, detected by an open-vocabulary entity extractor and video segmenter. The paper's stated rationale: "This filtering prevents transient or geometrically unreliable content from contaminating the persistent memory." Also carries the current chunk latents forward as short-term context.
- **There is no correction, merge, dedup, or eviction.** The only defence against bad memory is the *dynamic-object / sky filter at write time*. Consequences the paper does not test: (a) two conflicting latent tokens for the same physical surface can coexist, with the z-buffer silently arbitrating; (b) memory grows monotonically; (c) a wrong depth estimate writes a *permanently* wrong `(p, f)` pair that future readouts will confidently project.
- **Adaptation.** Two-stage: stage 1 freezes backbone + VAE, trains only the side branch; stage 2 freezes the branch, attaches **rank-32 LoRA** to the backbone; both stages use flow matching.
- **Relevance to ghosting.** This is the most direct architectural candidate for cause (1) "wrong geometry" and cause (3) "conditional averaging": the readout supplies zero-filled cells and a visibility mask but **no confidence weighting**, and duplicated/conflicting memory elements are resolved by nearest-depth only. That is a plausible mechanism for the same object appearing at two world positions.

### 2.5 MosaicMem — Hybrid Spatial Memory (arXiv 2603.17117)
*Selected because it is the only fetched work that treats memory as **directly manipulable/deletable** and diagnoses global-reconstruction fusion as the contaminating step.*

- **Storage.** The memory unit is the **patch**, deliberately intermediate between explicit memory (points/splats) and implicit memory (whole frames): "explicit methods store scene evidence as points or splats, whereas implicit methods retain memory at the granularity of entire video frames. We observe an intermediate representation—patches—that has been unexplored in prior work."
- **Write.** A 3D estimator infers depth + camera; each patch is **lifted into 3D** (the "front half" of an explicit pipeline).
- **Read.** On revisit, the retrieved patch is supplied to the DiT as **context** and a modified RoPE conveys the patch↔noised-latent correspondence (the "back half" of an implicit pipeline). Retrieved mosaic patches are flattened and concatenated to the token sequence as conditioning.
- **Read/write alignment (the core technical contribution).** Two complementary warpings: **warped RoPE** (back-project the patch with its source `(K_i,T_i)` and re-project into the target camera `(K_j,T_j)`, keep the **fractional** part of the reprojected coordinate and sample RoPE at higher resolution to preserve precision) and **warped latent** (differentiable bilinear grid sampling of the source latent at those fractional coordinates). Training with a **mixture of both** is claimed best.
- **Property claims relevant to invalidation.** The paper claims a **"deletable and manipulable memory space in which individual object patches can be explicitly displaced, duplicated, or removed"**, and claims **"robust long-horizon updates"** because "MosaicMem stores independent localized patches rather than maintaining a globally reconstructed structure, [so] it avoids the accumulation of cross-view misalignment". It also claims **flexible retrieval** — dense or sparse — because "distributing memory from the same scene across different spatiotemporal locations often suffices to reconstruct the entire sequence."
- **Explicit critique of the alternative.** Implicit, posed-frame memory "is highly redundant, effectively converting context into memory frame-by-frame, which slows generation and caps persistence under finite context windows", while store-compressed patch tokens "degrade retrieval fidelity … leading to blurrier or less reliable revisits."
- **What it does NOT do.** There is **no scoring function, no budget, and no error signal**. Deletion is a user/editing affordance, not an automatic invalidation triggered by detected inconsistency. ⚠️ A search snippet attributed "learned confidence and visibility modeling … uncertainty-aware attention weights that incorporate depth confidence" to this paper; **I could not find that in the fetched arXiv HTML (which was truncated before the conclusion/future-work sections). Treat that specific attribution as UNVERIFIED** — it may be a future-work bullet rather than an implemented mechanism.

---

## 3. WHAT APPEARS UNCOVERED

Each is phrased as a falsifiable question. Collectively these are the mechanism-level holes I could not fill from any fetched page.

**On risk and error-targeted selection**
1. Does any system compute a **per-historical-observation scalar representing the probability that conditioning on it will increase error in a *future* target region** — as opposed to an informativeness, salience, visibility, or coverage score? (GIM-World scores information about *omitted history*; Mem-World scores heuristic informativeness; Future Forcing/PaFu-KV score token importance; AnchorWeave scores coverage. A *predicted-error* score on a *3D/geometric* memory was not found.)
2. Is there any work that **supervises the memory-selection signal with the realised future prediction error** of the generator it feeds? (LayerRecall's CHPM is the nearest: it supervises a router in *prediction space* against a privileged long-context reference — but on **K/V tokens**, not geometric memory. Whether CHPM could be lifted to a 3D cache is untested.)
3. Does an explicit **cardinality/compute budget interact non-trivially** with geometric risk — i.e. is the optimal memory subset under a tight budget *different in kind* (not just size) from the optimal subset under a loose one? No fetched paper sweeps budget × selection criterion jointly.
4. Can a **risk score be calibrated** — i.e. does stated memory risk correlate with measured downstream error, in a reliability-diagram sense? No fetched paper reports calibration of any memory-importance score.

**On memory correctness, revision, and forgetting**
5. Does any video world model **revise or delete an already-committed memory item when later evidence contradicts it**? Across VMem, LSM-World, MosaicMem, Mem-World and GIM-World, the answer appears to be **no**: writes are additive/union or index-appends, and the only removals are (a) dynamic-object/sky filtering, (b) pose-redundancy eviction of the *older* item, (c) free-form user editing. A search for an inconsistency-triggered invalidation rule returned nothing verified.
6. Does **repeated observation of the same wrong content reinforce the error**? VMem's merge rule (`I_k ← I_k ∪ {t}`) and LSM-World's union write both mean a surfel/token that is *frequently* revisited accumulates *more* supporting indices — so **confirmation is measured by visitation count, which is exactly the quantity that correlates with an object being a persistent error source**. Is there any work that weights evidence by *disagreement* rather than *count*? Not found. This is a concrete, testable failure mode and, to my reading, a genuinely open and well-posed one.
7. Is there any **conflict-detection / arbitration policy** when two memory items project to the same latent cell with materially different content? LSM-World resolves this with a **z-buffer** (nearest wins) and zero-fills unseen cells; no confidence, no voting, no cross-item consistency check.
8. Does any memory have an **error/uncertainty decay** for unobserved-but-stored content — i.e. does a memory item's trust decrease when it is contradicted by newer views, or only when it ages out? Not found.

**On what is stored and at what granularity**
9. Is there work that stores memory at **object/instance level with geometric anchoring** — i.e. simultaneously object-centric (like SlotMemory) *and* 3D-anchored (like VMem/Mem-World)? SlotMemory is object-centric but on the KV manifold, not geometry; VMem/Mem-World are geometric but surfel-level, not instance-level with identity. The intersection appears **empty** in my corpus.
10. Do **cross-view / multi-observation consistency checks** exist as a *write-time* gate — "commit only if ≥k views agree within tolerance"? AnchorWeave *reconciles* cross-view inconsistency after the fact via a weaving controller; no fetched paper uses agreement as a **write admission test**.
11. How should memory handle **dynamic objects** as first-class stored entities rather than as filtered-out noise? LSM-World **excludes** dynamic objects from memory; Mem-World adds a binary manipulated-object flag; WorldDirector sidesteps the memory question by orchestrating trajectories. No fetched paper maintains *geometric* memory for moving objects with update semantics.

**On measurement of the specific failure the project cares about**
12. Is there a metric or diagnostic that isolates **duplication/ghosting specifically** (same object instance rendered at two world positions), as distinct from blur, drift, or attribute change? The closest names in my corpus are: "identity drift" (SlotMemory), "attribute drift" (Towards Error-Free), "geometric drift"/"memory drift" (ViewRope, GIM-World), "revisit inconsistency" (Closing the Loop), "cross-view misalignment" (AnchorWeave), and **ViewBench**'s loop-closure-fidelity / geometric-drift suite (ViewRope). **No fetched paper names object duplication or ghosting as its target failure.**
13. Is memory quality **decomposable** into cause (1) wrong geometry vs (2) bad memory selection vs (3) diffusion conditional averaging? AnchorWeave's diagnosis — "cross-view misalignment, as pose and depth estimation errors cause the same surfaces to be reconstructed at slightly different 3D locations across views. When fused, these inconsistencies accumulate into noisy geometry that contaminates the conditioning signals" — is the closest thing to a causal decomposition I found, and it targets cause (1) not (3). Warnings about cause (3) appear only indirectly: WorldTrace shows that "naively compressing the cache in the RoPE-rotated space **corrupts memory by averaging together incompatible positional phases**" — an averaging-corruption result, but in KV space, not the diffusion conditioning path.

**On evaluation methodology the project would need**
14. Echo-Memory's headline finding is a warning worth internalising: its three evaluation branches "**routinely disagree**, showing that replay fidelity is not a sufficient proxy for remembering a world", and "aggressive spatial and hybrid-compression memories lose the salient evidence needed for return". **Does GRC's proposed memory-selection objective show a measurable gain on an open-domain *return* probe, or only on replay-style metrics?** This is the single most likely way a GRC result could look positive and be misleading.
15. "Compactness is not a free substitute for capacity" (Echo-Memory) directly challenges any claim that a smarter selection policy dominates simply by being more compact. **Does GRC's risk-based selection beat a raw-context capacity baseline at matched compute?**

---

## 4. THREATS to the GRC candidate

Ordered by how much damage each does to "risk-based, budgeted, geometry-aware memory selection for future-aware generation".

### Tier 1 — serious, partial pre-emption

**T1. GIM-World, arXiv 2606.02436** — *the most dangerous single item.*
It already does **geometry-aware, budgeted, uncertainty-scored memory selection**: subset `S` with `|S| ≤ K` maximizing mutual information, evaluated via a **GP posterior variance over a pose-time (i.e. geometric/kinematic) kernel**. Read the project's own framing — "estimate a *geometric risk* for each historical observation … then select, under a FIXED compute budget, the subset that maximally reduces FUTURE state prediction error" — against this. Two of the three clauses are already there, and the third (uncertainty/risk per observation, geometrically parameterised, under a budget) is very close.
**GRC survives only if it can articulate these differences and defend them empirically:**
- GIM-World's criterion is *information about the omitted history* (`I(S; H\S)`), **not** expected error of the *generated future*. Information gain about the past is not error reduction in the future.
- Its score is a **fixed-kernel GP posterior variance**, not a learned/targeted risk of an observation being *wrong*. A frame can be highly informative and still be geometrically wrong.
- Selection is over **raw history frames to be encoded**, not over a **persistent 3D cache to be conditioned on**. GRC's stated setting (choose which stored 3D memory to condition on) is not the same object.
- It has **no invalidation/update semantics**, so the "revise a stored memory when it is wrong" half of the project's interest is untouched.
**Recommended action:** treat GIM-World as the primary baseline. A GRC paper that does not beat GIM-World's pruning on a future-error metric, at matched budget, is not defensible.

**T2. LayerRecall, arXiv 2608.28460** — *the most dangerous on the training objective.*
**Cross-Horizon Prediction Matching** supervises a memory **router** using a privileged long-context reference **in prediction space**, explicitly to avoid needing "explicit memory-allocation labels". That is, in spirit, "learn which memory to use by matching future predictions" — the same supervision idea GRC would want. It also reports "memory-guided self-correction, whereby initially mismatched local attributes return to their historical appearance", which is a *correction* phenomenon.
**Differences GRC must hold:** it routes **K/V token memory**, not a 3D/geometric cache; there is **no per-observation geometric risk**; retrieval is conditioned on the **current** state (not on a target region's future risk); and it is layer-selective rather than budget-subset-selective. Also note the reported caveat that it "match[es] its backbone on VBench-Long" — i.e. gains are on memory benchmarks, not universal.

**T3. Mem-World / W-VMem, arXiv 2606.18960** — *closest on the mechanism.*
A **geometry-aware, budgeted (top-K + NMS), redundancy-suppressed selection of historical observations for future prediction**, whose ablation beats stride and short-term retrieval baselines (wrist-view PSNR 18.97 vs 17.06 vs 15.04). If GRC's headline is "geometry-aware budgeted memory selection helps", this is largely already shown.
**GRC's wedge:** Mem-World's score is a **hand-designed closed-form product** (normal alignment × inverse depth × object flag × recency) with **no learning and no error target**; it selects **whole historical frames** for context, not items from a geometric cache; and it is robotics-specific (wrist-view occlusion, forward kinematics for future poses). GRC should position against it as *learned/target-driven risk* vs *fixed heuristic informativeness* — and must show the learned version wins at matched K.

### Tier 2 — constrains the design space / must be cited and distinguished

**T4. VMem (ICCV 2025)** — already provides geometric indexing, top-K retrieval, **read-time NMS dedup**, and **write-time merge with older-item discard**. Any claim that geometric memory selection is novel fails. What VMem genuinely lacks: any notion of a memory being *wrong*, and any error/risk target.

**T5. Future Forcing (2605.30083) and PaFu-KV (2601.21896)** — **future-aware, budgeted memory selection already exists**, just on KV caches. Future Forcing constructs a **future query proxy** from historical statistics and scores tokens by importance under it (training-free); PaFu-KV distils a **Salience Estimation Head** from a bidirectional teacher to score tokens past- *and* future-informed. Someone will ask "isn't this GRC on a KV cache?" The honest answer must be: *not geometry-aware, and the budget is a KV size rather than a selected subset of 3D observations* — but the conceptual novelty of "select memory for the future under a budget" is gone.

**T6. AnchorWeave (ECCV 2026)** — attacks the **root cause GRC attributes to "wrong geometry"**: it explicitly argues that fusing one globally reconstructed 3D memory produces "cross-view misalignment … the same surfaces reconstructed at slightly different 3D locations across views", which "accumulate[s] into noisy geometry that contaminates the conditioning signals". Its fix is architectural (multiple **local** memories + coverage-driven retrieval + a weaving controller), not risk-scored selection. This is a competing explanation-and-fix for the same symptom, and it is peer-reviewed. **If ghosting is mostly caused by fused global geometry, AnchorWeave's fix may dominate a selection-based fix.**

**T7. MosaicMem (2603.17117)** — argues global reconstruction accumulates cross-view misalignment and that **patch-local memory avoids it**, and demonstrates explicit **memory removal** as an affordance. Directly competes on "prevent bad memory from contaminating generation".

**T8. Closing the Loop (2607.21848)** — a **training-free** loop-closure memory that inserts pose-matched historical chunks into the KV cache, reporting it "outperforms existing training-free baselines on revisit consistency without losing overall video quality". Any GRC claim must beat a training-free baseline, which is a low-cost bar for reviewers to demand.

**T9. LayerRecall + WorldTrace + Composition of Memory Experts** — the "memory routing / memory expert" framing is getting crowded fast (Aug 2026 alone: LayerRecall 2608.28460, WorldTrace 2608.07408). GRC should assume a "learned memory router for long-horizon video" paper will appear at a major venue within months and must differentiate on **geometry + explicit error objective + invalidation**, not on "learned selection" alone.

### Tier 3 — methodological threats to the *validation* plan

**T10. Echo-Memory (2606.09803)** — its controlled matrix separates **capacity / compression / read-out / recurrence** and finds the branches **disagree**; additionally "block-wise state-space recurrence is the strongest open-domain return mechanism in our matrix, showing that the structure of implicit memory matters as much as the decision to use it", and "compactness is not a free substitute for capacity".
**Why this threatens GRC:** it is a direct empirical prior that (a) **better selection may not be where the wins are**, and (b) gains measured on replay-style metrics may not transfer to return probes. A GRC evaluation that reports only replay/PSNR gains would be exactly the mistake Echo-Memory warns about.
**Mitigation:** GRC must report a **matched-compute comparison against a raw-context capacity baseline** and use an **open-domain return / loop-revisit probe**, not just replay fidelity.

**T11. "On Memory" (2512.06983)** — provides an encoding-vs-injection taxonomy and shows simple memory mechanisms already extend effective memory span and enable loop closure. Raises the bar for claiming a *new* mechanism class.

**T12. The survey (2606.01164)** — "long-horizon interactions and memory" is already a named technical challenge with its own section and benchmark comparison across four application fields. Novelty framing must be narrower than "memory is a problem in world models".

### The honest bottom line on GRC's novelty
I could **not** find a verified paper that does all three of: (i) a **per-observation geometric *risk* estimate**, (ii) **budgeted subset selection over a persistent 3D memory**, and (iii) an objective tied to **future state prediction error**. Each *pair* is covered — (i)+(ii) by GIM-World, (ii)+(iii) by LayerRecall's CHPM (on K/V), (i)+(ii) on frames by Mem-World. **The triple appears open**, but it is a *narrow* gap defended by distinctions of the form "information ≠ error", "learned risk ≠ fixed kernel", and "3D cache ≠ raw frames ≠ KV tokens". Two specific risks to the framing:
- **Risk A (novelty collapse):** a reviewer treats GIM-World's GP posterior variance as "geometric risk" and its `I(S;H\S)` as "budgeted selection", and declares GRC an incremental objective swap. Counter by *measuring* that information-gain selection and error-reduction selection pick **different subsets**, and that the difference is causally attributable to error.
- **Risk B (no headroom):** if Tier-3 is right that capacity/recurrence dominate selection (Echo-Memory), GRC's gains may be small at matched compute. **Test this early on a fixed budget, before investing further** — it is the cheapest experiment that can kill the project.

---

## 5. Search queries used (to extend the survey)

**Flagged-paper verification**
- `Geometry-Aware Implicit Memory for Video World Models arXiv 2606.02436`
- `Mirage latent spatial memory video world model arXiv 2606.09828`
- `AlayaWorld Long-Horizon and Playable Video World Generation arXiv 2607.06291`
- `Learning Plug-and-play Memory for Guiding Video Diffusion Models arXiv 2511.19229`
- `Wonder Video World Model Done Better arXiv 2607.26037`
- `UCM Unifying Camera Control and Memory time-aware positional encoding warping`

**Mechanism themes**
- `video world model memory write policy what to store commit long-term memory 2026`
- `memory forgetting invalidation video generation error accumulation drift 2026`
- `object-level slot memory video world model persistent 3D memory objects`
- `memory compression merging deduplication video world model keyframe selection budget`
- `memory deduplication merge overlapping 3D observations video generation consistency`
- `memory update invalidation stale geometry correction video world model 2026`
- `3D memory cache eviction policy video generation unbounded growth`
- `memory bank replacement policy video world model anchor event`
- `3D cache invalidation loop closure correction video world model depth error`
- `error accumulation reinforced by repeated memory writes video generation`

**Threat hunting (risk / budget / future-aware selection)**
- `risk-aware uncertainty-guided memory retrieval video diffusion geometry`
- `budgeted keyframe selection video world model future prediction error`
- `risk-based memory selection video world model predict future error`
- `memory subset selection fixed budget video diffusion world model geometry risk`
- `future-aware memory retrieval scoring video generation which history to condition on`
- `supervise memory selection by future prediction error video world model training signal`
- `world model memory selection future state prediction error supervise retrieval budget`
- `sparse attention memory retrieval learned relevance video world model 2026`
- `diffusion model ghosting duplicate object conditional averaging long video generation artifact`
- `ghosting duplicate object artifact 3D memory conditioned video generation`

**Discovery of specific works**
- `surfel memory video generation world model 2026`
- `long-horizon video world model memory mechanism survey 2026 arXiv`
- `Towards Interactive Video World Modeling Frontiers Challenges Benchmarks survey arXiv 2606.01164`
- `LayerRecall state-conditioned memory router long-horizon consistency video generation arXiv`
- `WorldTrace addressable memory video world models NVIDIA`
- `Composition of Memory Experts for Diffusion World Models arXiv`
- `AnchorWeave memory-augmented video generation arXiv`
- `Echo Memory controlled study of memory in action world models arXiv`
- `"On Memory" comparison of memory mechanisms in world models arXiv survey`
- `slot memory object-centric KV memory streaming long video generation`
- `Steady-Forcing balancing spatial persistence motion continuity long-horizon video diffusion arXiv`

**Method notes / limitations of this survey**
- The **arXiv API** (`export.arxiv.org/api/query`) was attempted for systematic recall and returned **HTTP 429 (rate exceeded)**; this survey therefore leans on web search for discovery and on direct fetches for verification. A systematic extension should retry the API with delays, and should sweep `arxiv.org/list/cs.CV/2606`–`2608` and `cs.GR`.
- **Not read in full** (abstract-only, flagged where they matter): AlayaWorld 2607.06291 (memory mechanism unknown), UCM 2602.22960, Wonder 2607.26037, ReMind 2605.25333, WorldPlay 2512.14614, SlotMemory 2605.31033, MemLearner 2606.31734.
- **Discovery-only, not fetched, therefore not cited as findings** (candidate leads for a follow-up pass): arXiv 2606.00664 (event coverage), 2603.02049 (pose-sampled nearest-neighbour retrieval), 2603.24835 (DCARL), 2605.31158 (Light Interaction), 2607.21686 (Persistent Computational State), 2605.26316 (E³C), 2606.14732 (Steady-Forcing), 2608.27328 (R2M-Bench), 2602.08025 (memory-consistency benchmark), 2602.00268 (temporal drift). **All are UNVERIFIED.**
- One OpenReview PDF (`openreview.net/pdf?id=21XSQF0dmM`) was **blocked by a browser-verification challenge**; the equivalent arXiv record (2512.06983) was fetched instead. Whether the OpenReview submission is the same work is **UNVERIFIED**.
