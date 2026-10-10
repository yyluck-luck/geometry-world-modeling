# Brief R255 — IDEATION (with self-rejection): what should the project do after S141? (2026-10-10)

Read CURRENT_STATUS.md, RESEARCH_MEMORY.md (newest first), docs/report/TECHNICAL_REPORT_20261010.md, and the RESULT.md
of S136-S140, plus work/S141_finetune/PROTOCOL.md. Owner context: this is a CSIT6910 independent project (HKUST MSc),
compute = 2 shared RTX 3090 (TACC gpu13) + 1 H800 job at a time (SuperPOD, Slurm), roughly 1-2 weeks left; the owner
wants the GPUs used fully and wants new ideas tested, not just diagnosed. S141 outcomes are unknown.

Task:
1. For each S141 outcome (A improves / not; B beats the warp / ties / loses), propose the single most informative next
   experiment. Each proposal: hypothesis, the minimal change, one pre-registerable primary contrast with the decision
   threshold, a kill criterion, data needed (no new downloads unless clearly worth it; state size), and a compute
   estimate on the hardware above.
2. Generate at least 6 genuinely different candidate ideas for making a memory-based video world model use retrieved
   or geometric evidence, e.g. trained warp-as-context through the replace channel, epipolar / depth-aware attention
   bias, training-time warp noise augmentation, cross-view attention at full resolution, consistency-distillation from
   the warp, retrieval scored by reprojection coverage instead of pose distance, uncertainty-aware fusion of warp and
   generation in pixel space. Then REJECT them: for each give the strongest reason it would fail or is already
   published (cite arXiv ID + exact title when claiming prior art; verify), and keep at most 3.
3. Include "stop experimenting and write up" as a candidate and judge it against the others honestly. What is the
   strongest paper-shaped claim the existing S133-S140 evidence already supports, and what is the weakest link a
   reviewer would attack?

Output: write exactly one file, work/agents/CODEX_R255_IDEATION_AFTER_S141.md: (i) outcome-conditional plan table,
(ii) idea list with rejection verdicts, (iii) the final ranked shortlist (max 3) with the reasoning, (iv) write-up
option assessment. I prefer a correct negative to an encouraging answer.
