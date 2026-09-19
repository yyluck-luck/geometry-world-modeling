from pathlib import Path
import ast, hashlib, json
from datetime import datetime, timezone
R=Path.cwd();W=R/'work/S86_fixed_warp_consumer'
def spec(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def put(name,x):
 with (W/name).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
for name in ['generate_with_fixed_warp.py','supervise_generation.py']:
 ast.parse((W/name).read_text())
warps=[(20,162235122,'c5a00ca9b20131cfdfa571d9aca8084346251374de0f47ac31325894729acb8a'),(21,157968034,'471e618e73a2f793cdefe46ac8e2f7466c35de79ece12faaeb0f3f47a847207e'),(22,146338446,'ba127ac8bd5fac5cbded242fabc1fa39444be9b72fc1c955b91e2cab4882efd3'),(23,138865338,'582ab7c20a18596917b0425ede50dfa50800f6dfc7c6c151c8363b17f2c9616e')]
contract=dict(schema='S86_FIXED_WARP_FOUR_ARM_EXPLORATORY_V1',created_utc=datetime.now(timezone.utc).isoformat(),
 runner_sha256=spec(W/'generate_with_fixed_warp.py')['sha256'],supervisor_sha256=spec(W/'supervise_generation.py')['sha256'],
 output_directory=str(W/'execution_01'),s70_helper=spec(R/'work/S70_fixed_context_generation/generate_fixed_contexts.py'),
 s70_inputs=spec(R/'work/S70_fixed_context_generation/INPUTS.json'),hooks=spec(W/'sampler_hooks.py'),
 fusion=spec(R/'work/S82_history_geometry_guidance/latent_geometry_guidance.py'),
 acceptance_metadata=[spec(R/'work/S85_fixed_geometry_warp/ROOT_RESULT_ACCEPTANCE.json'),spec(R/'work/S69_tum_camera_conditioning/ROOT_FINAL_RESULT_ACCEPTANCE.json')],
 warps=[dict(target_id=i,path=str(R/f'work/S85_fixed_geometry_warp/execution_01/TARGET_{i}.npz'),bytes=n,sha256=s) for i,n,s in warps],
 strengths=[.25]*50,final_strength=.25,
 controls=dict(history_order=[19,18,13,12],target_order=[20,21,22,23],geometry_condition_only=True,
  full8_slots=True,num_steps=50,resolution=[576,576],device='cpu',dtype='float32',threads=8,interop_threads=1,
  original_multiview_cfg=2.0,original_cfg_min=1.2,original_churn=0,seed=44,
  actual_rng='Restore Python/NumPy/Torch CPU stream after shared warp encoding; save initial unscaled noise, entry and all50 step states plus terminal',
  warp_encoding='Original S85 RGB01 black holes 0 -> 2*RGB-1; original ft-mse wrapper deterministic mean*0.18215; chunk1 four targets once',
  latent_mask='576 bool support -> nonoverlapping avg_pool2d 8x8 -> 72 fractional support; history front4 zero; not confidence',
  G0='One unmodified original 50-step sampling chain via transparent hooks, no clean fusion',
  Gguide='One original 50-step chain, after every original CFG clean prediction fuse at lambda .25; all descendants recompute',
  Gpaste='Same G0 raw target RGB, original branch conversion/clamp RGB01, image mask*.25 fixed warp mixture, no model',
  Gterminal='Same actual G0 last x_tilde/sigma_hat/next_sigma/raw_clean; fuse .25 then replay original to_d/Euler order; full8 original VAE decode once; no denoiser/no RNG'),
 budget=dict(total_seconds=5400,per_arm_seconds=2400,rss_bytes=45*1024**3,minimum_free_bytes=10*1024**3,supervisor_poll_seconds=5,termination_grace_seconds=20,
  estimate='Original S70 same settings about1475s per chain. Two new full chains expected about50min plus shared encode/terminal decode;90min cap with40min per-arm allows machine variability; no cap increase after outputs.'),
 recording=dict(Gguide_clean_steps=50,clean_step_tensors=['raw_clean','used_clean'],last_step_tensor_fields=['sigma','next_sigma','x_tilde','sigma_hat','raw_clean','used_clean','output'],
  model_snapshot='Actual params/buffers value,identity,modes before/after; learned weights frozen',failure='Keep partial/error/actual counts; no automatic retry; uncaptured abrupt crash recorded by external supervisor'),
 scoring=dict(reference_path=str(R/'work/S70_fixed_context_generation/scoring_01/transformed_targets_uint8.npy'),reference_bytes=3981440,reference_sha256='e144e842fc36c795baa05841761670555a21bc7b9c36e0a56b8440b6a2324442',reference_read_after='All generation outputs closed and hashed; no reference bytes in generation',
  primary='Each emitted uint8 RGB squared error divided by255^2; all576x576x3 channels each frame; average all4 frames equally',
  primary_signed_contrast='MSE(Gguide)-MSE(Gterminal); negative favors Gguide. Also always report Gguide-G0 and Gguide-Gpaste.',
  frame_channel_denominator=995328,total_channel_denominator=3981312,exact_numerator='int64 SSE; signed total SSE differences exact; no inferential significance threshold',
  secondaries='Same fixed S85 image mask support and hole MSE, full denominators; empty region NA; no border metric',
  no_adjustments=['registration','exposure adjustment','pixel selection','target dropping','scale fitting','post hoc primary choice'],
  incomplete='Any missing frame, nonfinite raw, failed emission consistency => incomplete comparison; no zero filling or reduced frame average',
  independent_review='Different author offline saved fusion/Euler/emission/RNG review and independent scoring arithmetic; no real-model replay required'),
 claim_boundary='One previously exposed scene,4 correlated targets,1noise draw; ordinary baseline manipulation, not blinded confirmation, long-horizon/dynamic consistency, statistical superiority or novel method. Gguide-Gterminal retains cumulative intervention-dose alternative; RGB/latent equal lambda is not equal RGB dose. Prediction support is not physical accuracy or visibility; encoder/decoder nonlocal. VMem+declared ft-mse variant not exact original VAE baseline.',
 new_method_validated=False,novelty_authorization='NONE')
put('CONTRACT.json',contract)
print(json.dumps({n:spec(W/n) for n in ['generate_with_fixed_warp.py','supervise_generation.py','CONTRACT.json']},indent=2))
