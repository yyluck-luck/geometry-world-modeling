# Operating instructions (read before the brief below)

You are running inside a checkout of the project repository with read access and network. **Verify, do not trust.** Every factual claim below is checkable from this repo or the public literature. Where you cannot check something, say so explicitly.

## What you can verify here

Pinned VMem source, three byte-identical copies (SHA-256 90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e):
- work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py
- work/S17_cpu_preflight/original/modeling/pipeline.py
- work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py
Anchors: :1249 get_context_info; :1263 torch.cat([context_c2ws, target_c2ws]); :1265 get_translation_scaling_factor(all_c2ws). get_cond uses get_plucker_coordinates(extrinsics_src=all_w2cs[:1], ...), so slot 0 is the ray reference; translation scale = camera_scale / norm(camera_dists[0]) + 0.01, so slot 0 sets global scale; encoder embeddings are mean-pooled.

Ledgers: RESEARCH_MEMORY.md (append-only; newest entries at the end), docs/METHOD_DIRECTION_CURRENT.md (single current summary of method direction), AGENTS.md, docs/report/TECHNICAL_REPORT_20260918.md, docs/RETRIEVAL_ARMS_RESULT_20260918.md, docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md, docs/report/bundle/*.json.

## Hard constraints for THIS run
- No GPU, no training, no weight or dataset downloads, no Slurm submissions. Read, compute on CPU, search the web.
- No contact with anyone. No messages, issues, PRs, emails.
- Write only the output file(s) named in the brief. Modify no other file.
- `new_method_validated=false`, `novelty_authorization=NONE`. Nothing you write changes them.

## Concurrency
Other processes work in OTHER checkouts of this repository at the same time. Do not delete, revert or "clean up" any file you did not create. Report anomalies; leave them alone.

## Evidence standard
Cite file:line for every code claim and arXiv ID / DOI + section for every literature claim. Every "I ran this" claim must include the exact command and its complete output; a previous round printed code that could not have produced its output, so all such claims are rerun before being accepted. I prefer a correct negative to an encouraging answer.

## Language
Work entirely in English and write your output entirely in English.

# Brief R252 — hostile review of S139 (code, results) and report v2 (2026-10-10)

Correction to the preamble: RESEARCH_MEMORY.md has the NEWEST entries at the TOP. The VMem source used by GPU runs is
mirrored at data/S134_tacc/vmem_src (SuperPOD transport). 7-Scenes chess frames used are in data/S139_chess/chess.

S139 has finished. Results: work/S139_crossseq_revisit/RESULT.md, results/S139_ANALYSIS.json, results/S139_BASELINE_CONTRASTS.json,
results/stepA_superpod, results/stepB_*/S139_SCORES_*.json. Report v2: docs/report/TECHNICAL_REPORT_20261010.md. Find bugs, leakage and
protocol deviations, recompute every headline number independently, and list overclaims in RESULT.md and the report.
Files: work/S139_crossseq_revisit/PROTOCOL.md (frozen; commit 27fbfef1, amendment appended later),
build_manifest_s139.py, WINDOW_MANIFEST.json, run_retrieval_s139.py (header copied from
work/S136_repaired_memory/run_retrieval_s136.py), pose_arms_s139.py, POSE_ARMS.json, build_plan_s139.py, gen_s139.py
(derived from work/S134_tacc_fixed_map/gen_s134.py), score_s139.py (from work/S132_C9_convention/score_c9.py),
baselines_s139.py, analyze_s139.py, convention_check_s139.py, CONVENTION_CHECK.json, s139_stepA.slurm, s139_stepB.slurm,
tacc_s139.sh.

Check, citing file:line, rerunning on CPU where feasible
(`PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python ...`):
1. Does the manifest implement the protocol exactly (pairs, starts, bank = 20 H frames then 12 C frames, targets,
   static offsets, priming chunks [15, 12])? Is any target ever inside its own window's bank?
2. run_retrieval_s139.py: does setting cfg.model.target_num_frames = chunk length before construct_and_store_scene
   really give every bank frame surfels (check pipeline.py construct_and_store_scene start_idx logic)? Is it restored?
   Is the NMS threshold initialised at the 5-frame state as in VMem? Any state leakage between windows (reset())?
3. pose_arms_s139.py: is mem_pose a faithful pose-only version of VMem's selection (geodesic, threshold, NMS, fill)?
   Is the history_favourable stratum computed only from poses available before scoring?
4. gen_s139.py / score_s139.py: are cross-sequence refs loaded correctly, conventions applied once (gl), targets scored
   against the right frames, and outputs keyed uniquely?
5. baselines_s139.py: correctness of pose handling for CUT3R (VMem passes get_transformed_c2ws(gl) = OpenCV poses),
   the depth back-mapping, and the copy-nearest baseline.
6. analyze_s139.py: does it implement the pre-registered primary/secondary/strata exactly? Any bug in the bootstrap or
   pairing?
7. Anything in the design that would make a positive or negative result uninterpretable (e.g. 7-Scenes intrinsics,
   pose-frame consistency across sequences, RGB/depth misregistration irrelevance).

Output: write exactly one file, work/agents/CODEX_R252_S139_AND_REPORT_REVIEW.md: findings table (issue | severity
blocker/major/minor | evidence | fix), then details. I prefer a correct negative to an encouraging answer.
8. Recompute the S139 primary/secondary/strata from the score files and plan_v2.json, and the B2 contrasts from
   BASE_*.json; check that the report v2 numbers (all sections) match their source files.
