# Brief R270 — IMPLEMENTATION follow-up to R269 figures (2026-10-11)

You MAY modify only files under docs/report/figures/ (make_figures.py, its outputs, README.md). Use the committed snapshot at
HEAD (the S139/S140 result files are now committed: work/S139_crossseq_revisit/results/*.json and subfolders,
work/S140_warp_guided/results/*.json and subfolders). Same rules as R269 (trace every number to a file/key; print values;
CPU only; verify exports).
1. Add Figure 1 (S139/S140 chess): arm means for PSNR and SSIM — VMem static_recent, mem_vmem, mem_pose; B2 warp (from
   static and from mem_vmem contexts); S140 WGS — plus the key contrasts with CIs (mem_vmem − static_recent, B2(mem_vmem) −
   VMem(mem_vmem), WGS − B2). Check the JSON schemas first and report exactly which keys you used.
2. Redesign fig04 (S144 development): plot each arm/control as a difference from B2 (dB) on a zoomed axis (dot plot, no bars
   from zero), mark the +0.20 dB gate line relative to A_R where relevant, and show A_none (context-only, ~11.19 dB) as an
   annotated off-scale value rather than squashing the axis. Keep the "blends fitted on development, optimistic" note.
3. fig02a: move value labels so they never overlap the zero line or markers.
Rerun the script and update README.md. Output summary in docs/report/figures/README.md (overwrite).
