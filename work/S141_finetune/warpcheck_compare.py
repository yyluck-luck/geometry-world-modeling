#!/usr/bin/env python3
"""Compare S141 GPU warps (warps_s141.py on chess check clips) with the S140 CPU warps. usage: <check_clips.json> <s141_dir> <s140_warp_dir>"""
import json, math, sys
from pathlib import Path
import numpy as np
cl = json.loads(Path(sys.argv[1]).read_text())['clips']; A, B = Path(sys.argv[2]), Path(sys.argv[3])
for c in cl:
    z = np.load(A / f"{c['id']}.npz")
    for i, wf in enumerate(c['warp_files']):
        r = np.load(B / wf); d = z['filled'][i].astype(np.float64) - r['filled'].astype(np.float64)
        psnr = -10 * math.log10(max((d * d).mean(), 1e-9) / 255 ** 2)
        print(c['id'], i, f"psnr(gpu vs cpu warp) {psnr:.2f} dB  valid agree {(z['valid'][i] == r['valid']).mean():.4f} cov {z['valid'][i].mean():.3f}/{r['valid'].mean():.3f}")
