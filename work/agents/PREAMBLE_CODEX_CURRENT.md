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
