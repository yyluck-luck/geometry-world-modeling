# C8 diagnostic design handoff (2026-09-23)

I created `work/S130_C8_diagnostics/` with the preregistration, source-preserving conditioning wrapper, CPU equivalence gate, support-mask analysis, remote retrieval-map producer, two reviewed sbatch templates, and a runbook. I did not submit a GPU job or modify a pinned VMem source.

Files:

- `DESIGN_AND_PREREGISTRATION.md`: exact S107 slot-0 factorial, 14-window B/C/J support audit, numeric predictions, cutoffs, and kill rules.
- `factorized_conditioning.py`: N/R/S/RS wrapper. It copies the pinned centering/scale logic and patches only the `get_plucker_coordinates` reference argument at runtime.
- `cpu_equivalence_test.py` and `CPU_EQUIVALENCE_OUTPUT.txt`: fail-closed CPU proof for RS permutation equivalence and native N non-equivalence.
- `run_slot_factor.py`: remote 16-forward slot-factor runner (2 multisets × 2 orders × 4 conventions × seed 42), unscored outputs only.
- `run_support_retrieval.py`: remote surfel-map producer following the existing S111 priming/two-stage construction, with no diffusion call.
- `analyze_support.py`: CPU-only mask aggregation and predeclared decision table.
- `slot_factor.sbatch`, `support_audit.sbatch`, `RUNBOOK.md`: existing Apptainer/Conda/Slurm recipe, tmux requirement, receipts, output paths, and budget.

The CPU gate was run in the recorded remote VMem runtime with the derived real-pose receipt (the original job receipt stores context IDs but not matrices):

```text
apptainer exec --containall --no-home --cleanenv --env C8_RUN_ROOT=/home/yliutz/gwm_source_transport_20260915 --env C8_S107_POSES=/mnt/input/S107_pose_receipt.json ... /home/yliutz/.conda/envs/gwm-cut3r-py311-20260915/bin/python3.11 /opt/c8/cpu_equivalence_test.py
```

Full output (the image setup warnings are included):

```text
INFO:    squashfuse not found, will not be able to mount SIF
INFO:    fuse2fs not found, will not be able to mount EXT3 filesystems
INFO:    Converting SIF file to temporary sandbox...
INFO:    underlay of /etc/localtime required more than 50 (75) bind mounts
There was a problem when trying to write in your cache folder (/home/yliutz/.cache/huggingface/hub). Please, ensure the directory exists and can be written to.
There was a problem when trying to write in your cache folder (/home/yliutz/.cache/huggingface/hub). You should set the environment variable TRANSFORMERS_CACHE to a writable directory.
WARNING:matplotlib:Matplotlib created a temporary cache directory at /tmp/matplotlib-d84inv0e because the default path (/home/yliutz/.config/matplotlib) is not a writable directory; it is highly recommended to set the MPLCONFIGDIR environment variable to a writable directory, in particular to speed up the import of Matplotlib and to better support multiprocessing.
INFO:matplotlib.font_manager:generated new fontManager
[N] permuted_condition_max_abs_diff=2.77108526
[R] permuted_condition_max_abs_diff=3.54927111
[S] permuted_condition_max_abs_diff=1.59954214
[RS] permuted_condition_max_abs_diff=5.96046448e-08
[PASS] RS is exactly a slot permutation; N is not invariant.
INFO:    Cleaning up image...
EXIT_CODE=0
```

The result is a PASS in the remote runtime: RS is invariant up to 5.96e-8 float32 error, while N is not invariant.

The original S107 job receipt did not contain matrices, so the remote gate used a derived receipt whose matrices are copied byte-for-byte from the exact S107 stage bank/query pose files, with source hashes and provenance recorded in `S107_pose_receipt.json`. The test did not use target RGB or depth.

Budget estimate: 0.5–2.0 H800-hours for the 16 slot-factor forwards, 0.5–2.0 H800-hours for 14-window retrieval-map construction without diffusion, plus a 1.0 H800-hour retry reserve. Expected total is below 5 H800-hours and therefore below the 20-hour C8 cap.

Execution blockers and assumptions that remain explicit:

1. The original S107 job receipt lacks pose matrices; the derived receipt explicitly records the exact stage files and hashes. A future stricter audit may still require the original job-side matrix dump.
2. The remote checkout is behind the local main branch, but the C8 directory is synced as a reviewed working tree; no remote commit or job submission has been made.
3. `run_support_retrieval.py` relies on the exact pipeline API and stage-bank layout used by `nms_s111.py`; any API/hash mismatch must stop the job.
4. The retrieval map is defined at VMem's averaged-target render (`target_K*0.65`) and mapped back to target 3D points by the independent evaluator; it is not sensor ground truth.
5. The sealed S113 scores remain development finite-panel evidence. No C8 output can validate a new method or change `new_method_validated=false` / `novelty_authorization=NONE`.
