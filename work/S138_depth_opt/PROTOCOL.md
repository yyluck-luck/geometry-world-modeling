# S138 protocol — VMem's global alignment never optimises depth; does fixing it help?

Owner standing authorization (2026-10-09). CPU only. `new_method_validated=false`, `novelty_authorization=NONE`.

## Finding that motivates it (codex R250, then verified here)
VMem's CUT3R fork keeps `im_depthmaps` as an `nn.ParameterList` (the dust3r line that stacked them as one Parameter
is commented out, `cloud_opt/dust3r_opt/optimizer.py:49-51`). `get_depthmaps` then re-stacks them with
`ParameterStack(..., is_param=False)`, which calls `.detach()` (`optimizer.py:245-249`, `:303-317`).
Verified on CPU (scene_13 w50, gl): after 50 iterations the depth maps are bit-identical to niter 0 (max |Δ| = 0.0
for all 5 frames), and every `im_depthmaps[i].grad` is None while `pw_poses` receives gradients. The 400-iteration
"global alignment" therefore never changes depth. Map scale and shape come entirely from initialisation.

## Question
If depth is actually optimised (`get_depthmaps` = `torch.stack(list(im_depthmaps)).exp()`, keeping the graph;
preset depths stay frozen), is the stage-1 map more accurate? Does it improve the downstream warp predictor?

## Arms (stage 1, 14 windows, gl, niter 400, lr 0.01, as VMem; S135 harness `repro_kps.py --optfix`)
kps (current behaviour; optimisation is a no-op) vs kps+optfix. Also fix+optfix (S133 centre-registration init) to see
whether real optimisation can rescue a poor init.

## Metrics and decision (pixel-aligned, as S135; window = median over 5 bank frames)
Primary: median |log ratio| and median per-pixel depth correlation vs dataset depth.
- Optimisation helps if kps+optfix lowers median |log r| or raises median corr, in ≥ 10/14 windows for that metric.
- Optimisation harms if it worsens either in ≥ 10/14 windows. dust3r's loss is not scale-invariant, so shrinkage is
  a known risk.
Downstream (S137 B2, corrected mapping): B2-kps+optfix vs B2-kps, window-bootstrap CI, ±0.2 dB rule.
