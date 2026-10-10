# Brief R253 — RETRIEVAL: prior art for S141 and for the project's central finding (2026-10-10)

Context (verify in CURRENT_STATUS.md, work/S139_crossseq_revisit/RESULT.md, work/S140_warp_guided/RESULT.md,
work/S141_finetune/PROTOCOL.md). Central finding so far: in VMem (arXiv 2506.18903), surfel-based retrieval finds
geometrically useful history frames on held-out revisits, but the frozen SEVA-style generator does not convert them
into better frames; a plain CUT3R+known-pose forward warp of the same contexts beats generation by about 3 dB PSNR
(though not in SSIM under large disocclusion). S141 now fine-tunes the generator: A = LoRA on attention only (domain
adaptation on 6 other 7-Scenes scenes); B = A + a zero-initialised conv branch that feeds the VAE latent of the
forward warp plus a 72x72 coverage map at the target frames into the first UNet conv.

Task: find and VERIFY (open the arXiv abstract page or the paper; exact arXiv ID and exact title) the prior work a
reviewer would cite against or alongside this, in three groups:
1. Novel-view / camera-controlled video diffusion conditioned on reprojected or warped images, point-cloud renders or
   depth-based warps (training-based and training-free), e.g. GenWarp, ViewCrafter, ReconX, Gen3C, NVS-Solver,
   See3D, CamCo, MultiDiff, LucidDreamer/Text2Room-style warp-and-inpaint, Voyager, and anything newer (2025-2026).
   For each: how the warp enters the network (concat to input / attention / replacement / guidance), whether trained,
   and whether the paper reports a direct comparison against the warp or reprojection itself.
2. Memory/retrieval world models and evidence on whether the generator actually uses retrieved context: VMem,
   WorldMem, Context-as-Memory, spatial-memory / point-map memory video models, long-context video world models,
   and any paper that ablates "retrieved context vs recent context" or shows the model ignores memory.
3. Evaluations that compare generative novel-view synthesis with simple reprojection baselines on real RGB-D data
   (7-Scenes, ScanNet, RGB-D Scenes, Replica), especially under disocclusion, and papers on PSNR vs SSIM/LPIPS
   disagreement for warp-vs-generate.

Then answer, with evidence:
(a) Which single published method is closest to S141 variant B, and is B essentially that method? Say so plainly if yes.
(b) Has any paper already reported "the generator does not use retrieved memory; a geometric warp beats it" for a
    memory world model? If yes, our S139/S140 finding is a replication, and say so.
(c) What, if anything, would remain novel or worth reporting in this project given (a) and (b)?

Output: write exactly one file, work/agents/CODEX_R253_RETRIEVAL_S141.md: a table (arXiv ID | exact title | year |
group | warp/memory entry point | trained? | compares to warp/reprojection? | relevance to S141), then answers (a)-(c),
then a list of items you could not verify. Do not invent IDs; an unverifiable entry must be marked UNVERIFIED.
