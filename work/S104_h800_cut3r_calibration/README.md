# S104 CUT3R calibration component

This runner is plan-only until submitted. It accepts four explicit RGB paths in ID order `1,31,61,91`; it rejects paths containing depth/pose/GT markers and never accepts a dataset root or archive glob. It loads the fixed `cut3r_512_dpt_4_64.pth`, runs the upstream `prepare_input` and `src.dust3r.inference.inference`, synchronizes CUDA timing, and saves raw outputs plus a success or exception receipt. No target RGB/depth/pose bytes are specified. The Slurm script is a template and has not been submitted.

Local checks: `python -m py_compile run_cut3r_rgb_only.py`; `bash -n run_s104.slurm`. A successful component run is not a VMem baseline or GRC result.
