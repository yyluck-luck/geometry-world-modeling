# Gate0 TUM metadata and Slurm audit (2026-09-16)

## Scope

This is a read-only review of `work/S102_gate0_tum/run_tum_gate0_metadata.py` and `run_tum_gate0.slurm`. It does not run VMem, CUT3R, video generation, or any formal GRC experiment.

## Slurm correction

The first submission was rejected with `QOSMinGRES` because account `mscitspod2026` on the `normal` partition requires a GPU allocation even for a metadata-only job. The current script contains:

```text
#SBATCH --gpus=1
```

This is consistent with the already successful H800 jobs S103 and S104. A remote `sbatch --test-only` after loading the Slurm module accepted the script and scheduled it on `dgx-09` (job 588522 test allocation, start time 2026-09-16 00:34:37). Therefore the correction is safe and exact. The Python process still performs metadata and one-depth-sample inspection only; the GPU is an accounting/QOS requirement, not scientific inference.

If the cluster later rejects the `--gpus` spelling, use the same resource shape as the successful jobs or the site equivalent `--gres=gpu:1`; do not silently remove the GPU request.

## Data-qualification logic audit

The script correctly keeps this run below formal Gate0:

- It hashes the archive and records byte size.
- It checks presence of `rgb.txt`, `depth.txt`, and `groundtruth.txt`.
- It reports timestamp monotonicity, uniqueness, and duration for each index.
- It measures nearest RGB-depth matches within a fixed 20 ms tolerance.
- It inspects one depth image's dimensions, mode, dtype, and raw nonzero median.
- It explicitly emits `gate0_status: CONDITIONAL_DATA_QUALIFICATION_ONLY`.
- It explicitly leaves `future_gt_isolation: NOT_YET_FROZEN` and `independent_heldout_scene: NOT_YET_ACQUIRED`.

The 20 ms result is an availability rate based on nearest-neighbour timestamp matching. It is not a one-to-one assignment, a pose interpolation result, or proof that the depth scale and coordinate convention are correct. The script also does not read target future ground truth for scoring, so this run cannot leak a scientific outcome.

## Remaining qualification gaps

Before declaring formal Gate0 or launching S103 VMem baseline, freeze and record all of the following in a versioned manifest:

1. RGB/depth timestamp pairing policy, including one-to-one behavior and duplicate handling.
2. Depth raw-unit conversion (for TUM this must be verified from the dataset documentation/metadata, not inferred from one sample) and invalid-depth policy.
3. Camera intrinsics, distortion handling, image resize/crop, and coordinate-frame/pose convention.
4. Ground-truth pose association/interpolation and the exact future-horizon definition.
5. An independently held-out scene or sequence, with its target RGB-D/pose files sealed from model selection and tuning.
6. Synthetic versus real-scene scope and the cross-scene generalization table.
7. Candidate-pool identity, input/history allowance, fixed memory/compute budget, random seeds, and failure/kill criteria.

The current `names={Path(m.name).name: m ...}` map keys archive members by basename. It is adequate for the known TUM archive layout if the required files are unique, but a production Gate0 checker should detect duplicate basenames or resolve exact root paths instead of silently overwriting a member. This is a robustness recommendation, not a reason to block the metadata-only qualification run.

## Decision

**S102 metadata audit may be submitted with `--gpus=1`, but it is not a Gate0 pass.** Accept its output only as candidate-data qualification evidence. The next scientific gate remains a frozen held-out manifest plus the implementation contract; only then may the formal VMem baseline and same-pool innovation tests start.

## Post-review execution receipt

After the audit, the corrected script was submitted and completed as SuperPOD job **588524**. The copied result is `work/S102_gate0_tum/remote_receipts_588524/RESULTS.json` (SHA-256 `3455151c990c44763898e534f5fc2e387036ae419599491a5164e49144fec35f`). It reports 2,585 RGB rows, 2,509 depth rows, 8,710 ground-truth rows, and 2,488/2,585 RGB-depth nearest matches within 20 ms (96.2476%). This confirms the metadata audit executed successfully; it does not change the Gate0 decision or authorize model inference.
