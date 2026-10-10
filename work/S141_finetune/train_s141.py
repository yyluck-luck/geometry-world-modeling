#!/usr/bin/env python3
"""S141 LoRA fine-tuning of the VMem generator (variant A: LoRA; B: LoRA + zero-init warp input branch).
usage: train_s141.py <A|B> <clips.json> <lat_dir> <warp_dir|NONE> <out_dir>
env: STEPS (3000), LR (1e-4), WARMUP (100), P_UNCOND (0.1), RANK (16), CKPT (1 = activation checkpointing),
     VAL_EVERY (500), SAVE_EVERY (500), MAX_STEPS_THIS_RUN (for smoke tests).
Objective: VMem's DiscreteDenoiser with EpsScaling on all 8 frames noised at one sigma (uniform over the 1000 discrete
levels); contexts substituted clean through cond['replace'] (c) exactly as at sampling; loss = MSE(network output, eps)
on the 4 target frames. With p=P_UNCOND the dict is VMem's uc (zero CLIP, zero replace, zero mask; Pluecker kept).
Variant B appends [warp latent, coverage] for targets / zeros for contexts to concat in both c and uc (like Pluecker)."""
import json, math, os, random, sys, time, types
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s141_common as C
import torch
import torch.nn.functional as F

VAR, CLIPS, LAT, WARP, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
assert VAR in ('A', 'B') and (VAR == 'A' or WARP != 'NONE')
E = lambda k, d: type(d)(os.environ.get(k, d))
STEPS, LR, WARM, PU, RANK = E('STEPS', 3000), E('LR', 1e-4), E('WARMUP', 100), E('P_UNCOND', 0.1), E('RANK', 16)
CK, VAL_EVERY, SAVE_EVERY, MAXRUN = E('CKPT', 1), E('VAL_EVERY', 500), E('SAVE_EVERY', 500), E('MAX_STEPS_THIS_RUN', 10 ** 9)
OUT.mkdir(parents=True, exist_ok=True); dev = 'cuda'
random.seed(0); np.random.seed(0); torch.manual_seed(0)

# ---- data ----
CJ = json.loads(CLIPS.read_text()); train = [c for c in CJ['clips'] if c['split'] == 'train']; val = [c for c in CJ['clips'] if c['split'] == 'val'][:E('VAL_N', 32)]
refs, lats, embs, c2ws = [], [], [], []
for f in sorted(LAT.glob('*.pt')):
    o = torch.load(f); refs += o['refs']; lats.append(o['lat']); embs.append(o['emb']); c2ws.append(o['c2w'])
IX = {r: i for i, r in enumerate(refs)}
LATG = torch.cat(lats).to(dev); EMBG = torch.cat(embs).to(dev); C2WG = torch.cat(c2ws).to(dev)
for c in train + val:
    assert c['scene'] in C.TRAIN_SCENES and all(r in IX for r in c['ctx'] + c['tgt']), c['id']
W5 = {}
if VAR == 'B':
    for c in train + val:
        o = torch.load(Path(WARP) / f"{c['id']}.pt"); W5[c['id']] = torch.cat([o['zw'], o['cov'][:, None]], 1).float()
Kg = C.model_grid_K(C.K7).to(dev)

# ---- model ----
model = C.load_base_model(dev)
torch.manual_seed(0)
n_attn, params = C.add_adapters(model, r=RANK, alpha=float(RANK), warp=(VAR == 'B'))
if CK: model.forward = types.MethodType(C.ckpt_forward, model)
net = C.VMemWrapper(model)
den = C.DiscreteDenoiser(C.DDPMDiscretization(), num_idx=1000, device=dev)
opt = torch.optim.AdamW(params, lr=LR, weight_decay=0.0)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / WARM))
print(f'[train] variant {VAR} attn {n_attn} trainable {sum(p.numel() for p in params) / 1e6:.2f}M clips {len(train)}+{len(val)} '
      f'frames {len(refs)} steps {STEPS} ckpt {CK}', flush=True)


def clip_cond(c):
    ci = [IX[r] for r in c['ctx']]; ti = [IX[r] for r in c['tgt']]
    with torch.no_grad():
        cond = C.build_cond(LATG[ci], EMBG[ci], C.to_gl(C2WG[ci]), Kg.repeat(len(ci), 1, 1), C.to_gl(C2WG[ti]), Kg)
    return cond, torch.cat([LATG[ci], LATG[ti]])


def eps_pred(cc, z, idx, eps):
    sig = den.sigmas[idx]
    x = z + sig * eps
    rep, m = cc['replace'].split((z.shape[1], 1), dim=1)
    inp = x * (1 - m) + rep * m
    with torch.autocast('cuda', dtype=torch.bfloat16):
        out = net(inp / torch.sqrt(sig ** 2 + 1.0), idx.repeat(z.shape[0]), cc, num_frames=z.shape[0])
    return out.float()


def with_warp(cc, c):
    return C.extend_concat(cc, W5[c['id']].to(dev)) if VAR == 'B' else cc


VAL_IDX = [50, 200, 400, 600, 800, 950]
def validate():
    g = torch.Generator(device=dev); tot = []
    with torch.no_grad():
        for k, c in enumerate(val):
            cond, z = clip_cond(c); cc = with_warp(cond['c'], c)
            for j, ix in enumerate(VAL_IDX):
                g.manual_seed(1000 * k + j); eps = torch.randn(z.shape, generator=g, device=dev)
                tot.append(F.mse_loss(eps_pred(cc, z, torch.tensor([ix], device=dev), eps)[4:], eps[4:]).item())
    a = np.array(tot).reshape(len(val), len(VAL_IDX))
    return float(a.mean()), [float(x) for x in a.mean(0)]


# ---- resume ----
step = 0; last = OUT / 'ckpt_last.pt'; logf = OUT / 'train_log.jsonl'
if last.exists():
    s = torch.load(last, weights_only=False)
    model.load_state_dict(s['adapter'], strict=False); opt.load_state_dict(s['opt']); sched.load_state_dict(s['sched'])
    step = s['step']; random.setstate(s['py']); np.random.set_state(s['np']); torch.set_rng_state(s['torch']); torch.cuda.set_rng_state(s['cuda'])
    print(f'[train] resumed at step {step}', flush=True)


def save(path):
    torch.save({'adapter': C.adapter_state(model), 'opt': opt.state_dict(), 'sched': sched.state_dict(), 'step': step,
                'py': random.getstate(), 'np': np.random.get_state(), 'torch': torch.get_rng_state(), 'cuda': torch.cuda.get_rng_state(),
                'variant': VAR, 'rank': RANK}, str(path) + '.tmp')
    os.replace(str(path) + '.tmp', path)


def log(rec):
    with logf.open('a') as fh: fh.write(json.dumps(rec) + '\n')


if step == 0:
    v, vs = validate(); log({'step': 0, 'val': v, 'val_by_sigma': vs}); print(f'[val] step 0 {v:.5f} {vs}', flush=True)
perm_rng = np.random.default_rng(0); order = []
for _ in range(max(1, (step - 1) // len(train) + 1) if step > 0 else 1): order = list(perm_rng.permutation(len(train)))  # same epoch order on resume
t_last = time.time(); run_steps = 0; acc = []
while step < STEPS and run_steps < MAXRUN:
    if step % len(train) == 0 and step > 0: order = list(perm_rng.permutation(len(train)))
    c = train[order[step % len(train)]]
    cond, z = clip_cond(c)
    cc = with_warp(cond['uc'] if random.random() < PU else cond['c'], c)
    idx = torch.randint(0, 1000, (1,), device=dev); eps = torch.randn_like(z)
    loss = F.mse_loss(eps_pred(cc, z, idx, eps)[4:], eps[4:])
    opt.zero_grad(set_to_none=True); loss.backward()
    gn = torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); sched.step()
    step += 1; run_steps += 1; acc.append(loss.item())
    if step % 20 == 0:
        dt = (time.time() - t_last) / 20; t_last = time.time()
        rec = {'step': step, 'loss': float(np.mean(acc)), 'lr': sched.get_last_lr()[0], 'grad_norm': float(gn), 'sec_per_step': dt,
               'max_mem_gb': torch.cuda.max_memory_allocated() / 2 ** 30}
        log(rec); acc = []
        print(f"[train] {step} loss {rec['loss']:.5f} gn {rec['grad_norm']:.3f} {dt:.2f}s/step mem {rec['max_mem_gb']:.1f}G", flush=True)
    if step % SAVE_EVERY == 0 or step == STEPS:
        save(last)
    if step % 1000 == 0 or step == STEPS:
        torch.save({'adapter': C.adapter_state(model), 'step': step, 'variant': VAR, 'rank': RANK}, OUT / f'adapter_{step:06d}.pt')
    if step % VAL_EVERY == 0 or step == STEPS:
        v, vs = validate(); log({'step': step, 'val': v, 'val_by_sigma': vs}); print(f'[val] step {step} {v:.5f} {vs}', flush=True)
if step >= STEPS:
    torch.save({'adapter': C.adapter_state(model), 'step': step, 'variant': VAR, 'rank': RANK}, OUT / 'adapter_final.pt')
    print('[train] DONE', step, flush=True)
