# Remote GPU persistent-launch preflight (2026-09-16)

This is an infrastructure audit, not a model experiment or Gate0 approval. No dataset image/depth/pose bytes were read, no model was constructed, and no Slurm/GPU job was submitted.

At 01:34:01 Asia/Shanghai, SSH reached `slogin-02`. The personal Python environment reports Python 3.11.16; tmux 3.2a and the exact `slurm/slurm/23.02.6` tools are available. The home filesystem reports 152G available, and `/tmp` reports 347G available. The user's Slurm queue and tmux session list were empty at this snapshot.

The read-only import probe passed for torch 2.7.0+cu126, numpy 1.26.4, diffusers 0.32.2, transformers 4.48.3, kornia 0.8.0, open_clip 2.30.0, viser 1.1.1 and trimesh 5.1.0. This proves import availability, not GPU forward correctness. Earlier model-load and CUT3R inference receipts retain their original scope.

The actual checkpoint names are `vmem_weights.pth` and `cut3r_512_dpt_4_64.pth`; the candidate contract names `vmem.ckpt` and `cut3r.pth` were incorrect at the time of inspection. The contract owner was notified. This preflight rehashed all four checkpoint files plus the VAE config; full sizes/hashes are in `REMOTE_PREFLIGHT_RECEIPT_20260916.json`.

The remote model source files and previous smoke entrypoint exist. At inspection time, `/home/yliutz/gwm_source_transport_20260915/validate_gate0_contract.py` and `S103_run.slurm` do not exist. The current launcher deployment uses `/home/yliutz/gwm_remote_tmux_20260916`; the final validator/contract/frozen manifest and real formal baseline entrypoint still need deploying after review. A model-load smoke script must not be substituted for a formal VMem forward run.

The persistent launcher was repaired in a bounded way:

- Arguments are passed with shell-safe quoting instead of nested interpolation.
- The module initializer runs before nounset to avoid the observed `ENABLE_LMOD: unbound variable` failure.
- Each launch owns a non-overwriting receipt directory and saves the Slurm job ID.
- Failed queue/accounting queries do not count as successful experiment completion.
- Formal dispatch requires Gate0 PASS and matching contract/script hashes in a frozen manifest.

Local regression checks use stub tmux only: valid fixture, changed-script rejection, draft-manifest rejection, and real blocked-Gate0 rejection all passed. Local and remote shell syntax checks passed. The three deployed shell-file hashes match the local files. These checks made zero Slurm submissions.

Next: fix contract checkpoint paths; finish scientific Gate0 review; freeze and deploy the real selector-free baseline entrypoint and signed manifest; use the formal launcher only after the real validator returns PASS. Keep the substitute-VAE limitation explicit in any subsequent baseline claim.
