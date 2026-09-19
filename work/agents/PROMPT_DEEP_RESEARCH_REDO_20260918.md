# Corrective brief and redo request: the architecture premises were wrong

Copy everything below the line back to the deep-research system.

---

# VERDICT ON THE PREVIOUS OUTPUT

Thank you for the 60+ candidates. **Two load-bearing architecture premises are factually false**,
verified against the pinned source, and they void roughly a third of the list. The schema I
specified was not used, and the FIXED constraints were not respected. One item in your output was
genuinely valuable and is credited in §4.

I am asking for a redo. **Section 2 gives you the verified ground truth so the same error cannot
repeat.**

---

# 1. WHAT WAS FALSIFIED AGAINST THE PINNED SOURCE

## 1.1 The consumer is NOT a VQ-VAE. It is a latent diffusion model.

Your Track C is built on the consumer being a VQ-VAE: a discrete codebook, a fixed "visual
vocabulary", discreteness causing sharper generation, inherent resistance to posterior collapse.
**None of that exists in this system.** Verified in the pinned checkout:

```
from diffusers.models import AutoencoderKL        # continuous KL-regularised VAE
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from utils import do_sample                        # latent diffusion sampling

grep -rilE "vectorquantiz|vq_?vae|codebook"  modeling/   ->   NO MATCHES
```

There is **no vector quantisation anywhere** in the model directory. Checkpoints are
`vmem_weights.pth`, `diffusion_pytorch_model.safetensors`, `open_clip_model.safetensors`,
`cut3r_512_dpt_4_64.pth`.

**Voided by this:** C01, C04, C06, C12, E05, E12, and every argument invoking discreteness,
codebooks, posterior collapse, or "visual vocabulary".

## 1.2 "Frozen consumer" is MY constraint, not a component of the architecture.

The phrase in my brief means: *I am forbidden to train, fine-tune, or modify the model.* You read it
as an architectural module inside VMem and built a track around analysing "the frozen consumer's
latent space". There is no such module. The whole model is frozen because that is my project rule.

## 1.3 Autoregression is over FRAMES, not over patches within an image.

Your A02, A05, A09, A10, B04, B07, C09, E06 and E13 assume sequential patch-by-patch generation
inside one image, with a causal raster path. Verified call:

```
do_sample(..., H=576, W=576, C=4, F=8, T=8, input_masks=[T,T,T,T,F,F,F,F], ...)
```

**Eight frames are denoised jointly in one diffusion pass: four context frames and four target
frames.** Autoregression happens *across successive generation calls*, where generated frames are
written back into the memory bank. There is no within-image generation order.

**E13 is incoherent as written**: you propose testing whether the model under-uses surfels
projected into "the middle" of the generation path, biased toward "the top and bottom of the
image". No such path exists. If you want a spatial-context-utilisation analogue, it must be defined
over the four context slots or over bank position, not over image rows.

## 1.4 Consequences you should draw

Any candidate whose mechanism contradicts §2 is void regardless of how good the idea sounds. **In
the redo, state the source fact your mechanism depends on, and mark it VERIFIED or ASSUMED.**

---

# 2. VERIFIED GROUND TRUTH — build on this, not on inference from the name

| fact | verified value |
|---|---|
| model class | camera-conditioned **latent diffusion**, not token-autoregressive |
| image autoencoder | `AutoencoderKL` (continuous, KL-regularised). No VQ, no codebook |
| sampler | `create_samplers(guider_types=1)` over `DDPMDiscretization`, `DiscreteDenoiser(num_idx=1000)` |
| diffusion steps | 50 |
| guidance | `cfg = 2.0`, `cfg_min = 1.2` |
| one forward pass | 8 frames jointly: 4 context + 4 target, `input_masks = [T,T,T,T,F,F,F,F]` |
| resolution | 576 x 576, latent channels 4 |
| autoregression | across generation calls; generated frames are written back into the bank |
| memory | surfel cloud built by CUT3R; retrieval renders surfels from an averaged query pose |
| retrieval ranking | candidates weighted by surfel relevance, then sorted by **geodesic camera distance** to the query pose |
| selection seeding | `selected_indices = [sorted_frames[0]]`, then `len(self.c2ws)-1` when NMS is disabled; the NMS loop runs only when enabled |
| camera conditioning | Plücker coordinates with the **first context camera** as reference |
| camera normalisation | median-based outlier mask, subtract the **mean** of surviving centres, scale by `camera_scale / ||first camera||`. **Not extrema-based** |
| released entry points | `navigation.py` has **three** call sites: movement (x2) passes NMS `False`; turning passes **no argument** and resolves to config `true` |
| released package | demo only. `app.py`, `navigation.py`, `modeling/*`, `utils/*`. **No evaluation or benchmark script** |

---

# 3. PROCESS FAILURES TO FIX IN THE REDO

**3.1 The mandatory schema was not used.** Every candidate was Problem / Solution / Innovation —
which my brief explicitly forbade as a topic list. The required fields were: ID, one-line claim,
mechanism, nearest prior work with the specific passage, **occupancy verdict**, **verification
status**, **relaxations needed**, smallest decisive experiment with arms, what must be true, kill
criterion, venue fit, cost. **A candidate without these does not count.**

**3.2 The FIXED constraints were violated at scale.** My brief marked these as not relaxable: no new
architecture, no modification of the upstream source. A06 proposes replacing the transformer with
Mamba; most of Tracks A, B and C require training or architectural surgery; D08 (medical imaging)
and D10 (non-visible spectrum) are different domains and datasets entirely. **In the redo, every
candidate must carry its relaxation list, and candidates needing FIXED items must be marked
INADMISSIBLE rather than presented as options.**

**3.3 The occupied list was re-proposed.** B11 ("VMem as RAG with advanced reranking") and E13
("lost in the middle") are the exact claims I listed as occupied by RAGME (arXiv:2504.06672),
LongLive-RAG (arXiv:2606.02553) and COVRAG (arXiv:2606.02479). Re-proposing an occupied claim wastes
a slot.

**3.4 Citation quality is mixed.** I spot-checked eight suspicious identifiers — 2607.27036,
2605.07897, 2603.11768, 2609.08084, 2605.18754, 2602.04439, 2603.21167, 2601.13048. **All eight
resolve to real papers. Nothing was fabricated, and I credit that.** But there are content
mismatches: 2609.08084 is *"Marigold V2: Revisiting Diffusion Transformers for Monocular…"*, a
monocular depth paper, cited to support multi-view prediction (D12) and scene identifiability (E07).
A large share of the remaining references are Medium posts, YouTube videos and vendor blogs, which
cannot establish occupancy or method detail. **In the redo: peer-reviewed or arXiv primary sources
only for any occupancy or mechanism claim; mark anything else as background.**

---

# 4. WHAT WAS GENUINELY VALUABLE — credit where due

**TSED.** You cited the thresholded symmetric epipolar distance. I verified it: arXiv **2304.10700**,
*"Long-Term Photometric Consistent Novel View Synthesis with Diffusion Models"*, which states
*"we introduce a new metric, the thresholded symmetric epipolar distance (TSED), to measure the
number of consistent frame pairs in a sequence."* It targets long-range geometric consistency in
**autoregressive conditional diffusion NVS** — the same model class as my consumer.

This mattered: my project had built its own cross-view reprojection consistency evaluator **without
first searching for the established metric on this task line**, which violates my own standing rule.
The evaluator has never been used for any published number, so nothing had to be withdrawn, but the
process failure is now recorded. **This single pointer was worth more than the 60 candidates.**

Two further genuinely relevant papers from your list, which I will read:
**arXiv:2605.18754** *"Can These Views Be One Scene? Evaluating Multiview 3D Consistency"*;
**arXiv:2607.27036** *"Mitigating Compounding Error via Video Representation Regularization"*.

**This is the kind of contribution I want more of: a specific, verifiable pointer that corrects
something I am doing wrong.**

---

# 5. THE REDO

Same six tracks, same schema, same minimum counts. Three additions:

1. **Architecture-fact gate.** Before proposing, state which §2 fact your mechanism depends on. Any
   candidate contradicting §2 is void. If you believe a §2 entry is wrong, say so and give the file
   and line you would check — do not quietly proceed.
2. **Admissibility flag.** Every candidate gets `ADMISSIBLE` (needs only relaxable levers) or
   `INADMISSIBLE` (needs a FIXED item). Report the counts. I expect most to be INADMISSIBLE, and
   that is a useful answer.
3. **A second deliverable I value at least as much as the 50:** a list of **specific things this
   project is doing wrong or missing**, in the style of the TSED finding — established metrics not
   used, standard controls not run, known failure modes not checked, published baselines not
   compared against. **Five well-verified items here beat fifty candidates.**

If your honest conclusion after the redo is that no ADMISSIBLE candidate supports a top-venue paper
under any single relaxation, **state that plainly.** It will be acted on, not argued with.
