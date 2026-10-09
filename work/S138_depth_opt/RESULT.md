# S138 result — VMem never optimises depth; turning optimisation on makes the map worse

Protocol: `PROTOCOL.md`. CPU only. `new_method_validated=false`, `novelty_authorization=NONE`.

## The bug (found by codex R250, verified here)
VMem's CUT3R fork keeps `im_depthmaps` as an `nn.ParameterList`. `get_depthmaps` re-stacks it through
`ParameterStack(is_param=False)`, which detaches (`cloud_opt/dust3r_opt/optimizer.py:245-249`, `:303-317`; the dust3r
line that stacked once as a Parameter is commented out at `:49-51`).
Verified (scene_13 w50, gl): after 50 iterations the depth maps are bit-identical to niter 0 (max |Δ| = 0.0, all
5 frames), every `im_depthmaps[i].grad` is None, and `pw_poses` does receive gradients. The 400-iteration global
alignment that VMem runs at every construct never changes depth. This is the third VMem integration defect in the
series, after the S133 PnP fallback and the S135 priming holes.

## Fix and test
`optfix.py` makes `get_depthmaps` stack without detaching, so preset depths stay frozen and the others are optimised.
Smoke test: depths now change (max |Δ| ≈ 0.19–0.25 m after 50 iterations) and shrink by 11–16%.

## Results (stage 1, 14 windows, gl, niter 400; pixel-aligned metric as S135; `ARMS_SUMMARY.txt`)
| arm | in [0.5, 2] | in [0.8, 1.25] | median ratio | median \|log r\| | median corr |
|---|---|---|---|---|---|
| KPS, optimisation no-op (VMem as is) | 14/14 | 13/14 | 0.946 | 0.055 | 0.977 |
| KPS + real optimisation | 14/14 | 13/14 | 0.931 | 0.072 | 0.977 |
| S133 fix, no-op | 12/14 | 3/14 | 0.665 | 0.410 | 0.977 |
| S133 fix + real optimisation | **8/14** | 1/14 | **0.578** | 0.548 | 0.977 |

- With KPS init, real optimisation worsens |log r| in **12/14** windows and improves the correlation in only 8/14
  (median change 0.000). **Verdict (pre-registered): harms** (scale shrinkage).
- With the S133 init it worsens 11/14 and cannot rescue a poor init.
- Downstream (S137 B2, corrected mapping): B2-kps+optfix − B2-kps = **−0.203 dB [−0.358, −0.064]**, 5/16 windows,
  WORSENS.

## Reading
dust3r's alignment loss uses absolute 3D distances, so with fixed known poses and a weak scale constraint it pays to
shrink the scene. Depth shape does not improve. VMem's accidental detach therefore preserves whatever scale the
initialisation sets. The right repair is a good initialisation (KPS) with no depth optimisation, or a scale-invariant
loss (not tested). "Re-enabling" dust3r optimisation is not a fix.

## Files
`optfix.py`, `ARM_gl_{kps,fix}_{noop,optfix}.json`, `ARMS_SUMMARY.txt`, `B2_kps_optfix.json`, logs.
