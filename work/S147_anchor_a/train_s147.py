#!/usr/bin/env python3
"""S147 Anchor-A training (protocol work/S147_anchor_a/PROTOCOL.md).
usage: train_s147.py <F_geo|F_null|J_geo|A_cont> <clips.json> <lat_dir> <warp_dir> <adapter_A.pt> <invalid.json> <out_dir>
env as train_s141.py: STEPS (10000), LR (1e-4), WARMUP (100), P_UNCOND (0.1), RANK (16), CKPT (1), VAL_EVERY (500),
SAVE_EVERY (500), MAX_STEPS_THIS_RUN (pilots).
Recipe = train_s141.py, except: every arm starts from adapter A; trainable set per arm (F_*: branch only, A LoRA frozen;
J_geo: A LoRA + branch; A_cont: A LoRA, no branch); clips on the source-only invalid-geometry list consume exactly the RNG
draws of a normal step (CFG-dropout draw, sigma index, noise) but get no forward/backward/optimizer/scheduler step, in every
arm; F_null feeds a fixed per-channel prototype latent (mean warp latent over valid training clips) with the estimated coverage.
R273 §7 B: isolated training RNG streams (Python random.Random(0) for CFG dropout, a CUDA torch.Generator seeded 0 for sigma
and noise, NumPy default_rng(0) for the clip permutation); warm-up counted in valid updates; a per-step schedule digest
(clip, CFG draw, sigma index, noise SHA-256) in schedule.jsonl for cross-arm alignment checks; a non-finite loss or
gradient stops the run. Engineering env: ENG_CLIPS (comma list replacing the training list), CKPT=0 (ordinary forward)."""
import hashlib, json, math, os, random, sys, time, types
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s141_common as C
import torch
import torch.nn.functional as F

ARM, CLIPS, LAT, WARP, ADA, INV, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), Path(sys.argv[6]), Path(sys.argv[7])
assert ARM in ('F_geo', 'F_null', 'J_geo', 'A_cont')
BRANCH = ARM != 'A_cont'
E = lambda k, d: type(d)(os.environ.get(k, d))
STEPS, LR, WARM, PU, RANK = E('STEPS', 10000), E('LR', 1e-4), E('WARMUP', 100), E('P_UNCOND', 0.1), E('RANK', 16)
CK, VAL_EVERY, SAVE_EVERY, MAXRUN = E('CKPT', 1), E('VAL_EVERY', 500), E('SAVE_EVERY', 500), E('MAX_STEPS_THIS_RUN', 10 ** 9)
OUT.mkdir(parents=True, exist_ok=True); dev = 'cuda'
random.seed(0); np.random.seed(0); torch.manual_seed(0)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ---- data ----
CJ = json.loads(CLIPS.read_text()); train = [c for c in CJ['clips'] if c['split'] == 'train']
if os.environ.get('ENG_CLIPS'):
    _ix = {c['id']: c for c in train}; train = [_ix[k] for k in os.environ['ENG_CLIPS'].split(',')]
INVALID = set(json.loads(INV.read_text())['invalid_clip_ids'])
val = [c for c in CJ['clips'] if c['split'] == 'val'][:32]; val = [c for c in val if c['id'] not in INVALID]   # 31 monitor clips
refs, lats, embs, c2ws = [], [], [], []
for f in sorted(LAT.glob('*.pt')):
    o = torch.load(f); refs += o['refs']; lats.append(o['lat']); embs.append(o['emb']); c2ws.append(o['c2w'])
IX = {r: i for i, r in enumerate(refs)}
LATG = torch.cat(lats).to(dev); EMBG = torch.cat(embs).to(dev); C2WG = torch.cat(c2ws).to(dev)
for c in train + val:
    assert c['scene'] in C.TRAIN_SCENES and all(r in IX for r in c['ctx'] + c['tgt']), c['id']
W5, PROTO = {}, None
if BRANCH:
    for c in train + val:
        if c['id'] in INVALID: continue
        o = torch.load(WARP / f"{c['id']}.pt"); w = torch.cat([o['zw'], o['cov'][:, None]], 1).float()
        assert w.shape == (4, 5, 72, 72) and torch.isfinite(w).all(), c['id']; W5[c['id']] = w
    zsum = torch.zeros(4, dtype=torch.float64); n = 0
    for c in train:
        if c['id'] in INVALID: continue
        zsum += W5[c['id']][:, :4].double().sum(dim=(0, 2, 3)); n += 4 * 72 * 72
    PROTO = (zsum / n).float()                                            # per-channel mean warp latent (valid training clips)
    if ARM == 'F_null':
        for k in W5: W5[k] = torch.cat([PROTO.view(1, 4, 1, 1).expand(4, 4, 72, 72), W5[k][:, 4:]], 1).contiguous()
Kg = C.model_grid_K(C.K7).to(dev)

# ---- model: base + A (+ zero-init branch) ----
model = C.load_base_model(dev)
torch.manual_seed(0)
n_attn, _ = C.add_adapters(model, r=RANK, alpha=float(RANK), warp=BRANCH)
stA = torch.load(ADA, map_location='cpu', weights_only=False)
assert stA['variant'] == 'A' and stA['rank'] == RANK
res = model.load_state_dict(stA['adapter'], strict=False)
lora_keys = [k for k in model.state_dict() if '.down.' in k or '.up.' in k]
assert not res.unexpected_keys and not [k for k in res.missing_keys if k in lora_keys] and set(stA['adapter']) == set(lora_keys), res
for name, p in model.named_parameters():
    is_lora, is_warp = ('.down.' in name or '.up.' in name), '.warp.' in name
    p.requires_grad = (is_warp and ARM in ('F_geo', 'F_null', 'J_geo')) or (is_lora and ARM in ('J_geo', 'A_cont'))
params = [p for p in model.parameters() if p.requires_grad]
n_warp = sum(p.numel() for n_, p in model.named_parameters() if p.requires_grad and '.warp.' in n_)
n_lora = sum(p.numel() for n_, p in model.named_parameters() if p.requires_grad and ('.down.' in n_ or '.up.' in n_))
assert (n_warp > 0) == BRANCH and (n_lora > 0) == (ARM in ('J_geo', 'A_cont'))
if CK: model.forward = types.MethodType(C.ckpt_forward, model)
net = C.VMemWrapper(model)
den = C.DiscreteDenoiser(C.DDPMDiscretization(), num_idx=1000, device=dev)
opt = torch.optim.AdamW(params, lr=LR, weight_decay=0.0)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / WARM))
META = {'arm': ARM, 'variant': 'B' if BRANCH else 'A', 'rank': RANK, 'base_adapter': str(ADA), 'base_adapter_sha256': sha(ADA),
        'invalid_list_sha256': sha(INV), 'prototype': PROTO}
print(f'[train] arm {ARM} attn {n_attn} trainable lora {n_lora / 1e6:.3f}M warp {n_warp} clips {len(train)} (invalid '
      f'{sum(c["id"] in INVALID for c in train)}) val {len(val)} steps {STEPS} ckpt {CK} proto {None if PROTO is None else PROTO.tolist()}', flush=True)


def clip_cond(c):
    ci = [IX[r] for r in c['ctx']]; ti = [IX[r] for r in c['tgt']]
    with torch.no_grad():
        cond = C.build_cond(LATG[ci], EMBG[ci], C.to_gl(C2WG[ci]), Kg.repeat(len(ci), 1, 1), C.to_gl(C2WG[ti]), Kg)
    return cond, torch.cat([LATG[ci], LATG[ti]])


def eps_pred(cc, z, idx, eps):   # train_s141.eps_pred
    sig = den.sigmas[idx]
    x = z + sig * eps
    rep, m = cc['replace'].split((z.shape[1], 1), dim=1)
    inp = x * (1 - m) + rep * m
    with torch.autocast('cuda', dtype=torch.bfloat16):
        out = net(inp / torch.sqrt(sig ** 2 + 1.0), idx.repeat(z.shape[0]), cc, num_frames=z.shape[0])
    return out.float()


def with_warp(cc, c):
    return C.extend_concat(cc, W5[c['id']].to(dev)) if BRANCH else cc


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


def adapter_blob(step):
    return {'adapter': C.adapter_state(model), 'step': step, **META}


# ---- resume ----
step = 0; valid_updates = 0; last = OUT / 'ckpt_last.pt'; logf = OUT / 'train_log.jsonl'; schf = OUT / 'schedule.jsonl'
PYR = random.Random(0); GEN = torch.Generator(device=dev); GEN.manual_seed(0)      # isolated training streams
if last.exists():
    s = torch.load(last, weights_only=False)
    assert s['arm'] == ARM
    model.load_state_dict(s['adapter'], strict=False); opt.load_state_dict(s['opt']); sched.load_state_dict(s['sched'])
    step, valid_updates = s['step'], s['valid_updates']
    random.setstate(s['py']); np.random.set_state(s['np']); torch.set_rng_state(s['torch']); torch.cuda.set_rng_state(s['cuda'])
    PYR.setstate(s['pyr']); GEN.set_state(s['gen'].cpu() if hasattr(s['gen'], 'cpu') else s['gen'])
    print(f'[train] resumed at step {step} (valid updates {valid_updates})', flush=True)


def save(path):
    torch.save({**adapter_blob(step), 'opt': opt.state_dict(), 'sched': sched.state_dict(), 'valid_updates': valid_updates,
                'py': random.getstate(), 'np': np.random.get_state(), 'torch': torch.get_rng_state(), 'cuda': torch.cuda.get_rng_state(),
                'pyr': PYR.getstate(), 'gen': GEN.get_state()},
               str(path) + '.tmp')
    os.replace(str(path) + '.tmp', path)


def log(rec):
    with logf.open('a') as fh: fh.write(json.dumps(rec) + '\n')


if step == 0:
    torch.save(adapter_blob(0), OUT / 'adapter_000000.pt')
    tv = time.time(); v, vs = validate(); log({'step': 0, 'val': v, 'val_by_sigma': vs, 'val_seconds': time.time() - tv}); print(f'[val] step 0 {v:.5f} {vs}', flush=True)
perm_rng = np.random.default_rng(0); order = []
for _ in range(max(1, (step - 1) // len(train) + 1) if step > 0 else 1): order = list(perm_rng.permutation(len(train)))  # as train_s141
t_last = time.time(); run_steps = 0; acc = []; skipped = 0; gn = torch.tensor(0.0)
while step < STEPS and run_steps < MAXRUN:
    if step % len(train) == 0 and step > 0: order = list(perm_rng.permutation(len(train)))
    c = train[order[step % len(train)]]
    u = PYR.random(); use_uc = u < PU                                      # same three draws on every scheduled step
    idx = torch.randint(0, 1000, (1,), device=dev, generator=GEN); eps = torch.randn((8, 4, 72, 72), device=dev, generator=GEN)
    with schf.open('a') as fh:
        fh.write(json.dumps({'step': step, 'clip': c['id'], 'u': u, 'idx': int(idx.item()), 'eps_sha': hashlib.sha256(eps.cpu().numpy().tobytes()).hexdigest()[:16],
                             'skip': c['id'] in INVALID}) + '\n')
    if c['id'] in INVALID:
        skipped += 1
    else:
        cond, z = clip_cond(c); assert z.shape == eps.shape
        cc = with_warp(cond['uc'] if use_uc else cond['c'], c)
        loss = F.mse_loss(eps_pred(cc, z, idx, eps)[4:], eps[4:])
        if not torch.isfinite(loss): raise RuntimeError(f'non-finite loss at step {step} clip {c["id"]}')
        opt.zero_grad(set_to_none=True); loss.backward()
        gn = torch.nn.utils.clip_grad_norm_(params, 1.0)
        if not torch.isfinite(gn): raise RuntimeError(f'non-finite gradient at step {step} clip {c["id"]}')
        opt.step(); sched.step()
        valid_updates += 1; acc.append(loss.item())
    step += 1; run_steps += 1
    if step % 20 == 0:
        dt = (time.time() - t_last) / 20; t_last = time.time()
        rec = {'step': step, 'valid_updates': valid_updates, 'skipped_in_window': skipped, 'loss': float(np.mean(acc)) if acc else None,
               'lr': sched.get_last_lr()[0], 'grad_norm': float(gn), 'sec_per_step': dt, 'max_mem_gb': torch.cuda.max_memory_allocated() / 2 ** 30}
        log(rec); acc = []; skipped = 0
        print(f"[train] {step} valid {valid_updates} loss {rec['loss']} gn {rec['grad_norm']:.3f} {dt:.2f}s/step mem {rec['max_mem_gb']:.1f}G", flush=True)
    if step % SAVE_EVERY == 0 or step == STEPS:
        save(last)
    if step % 1000 == 0 or step == STEPS:
        torch.save(adapter_blob(step), OUT / f'adapter_{step:06d}.pt')
    if step % VAL_EVERY == 0 or step == STEPS:
        v, vs = validate(); log({'step': step, 'val': v, 'val_by_sigma': vs}); print(f'[val] step {step} {v:.5f} {vs}', flush=True)
if step < STEPS and os.environ.get('SAVE_AT_EXIT') == '1':
    save(last)
if step >= STEPS:
    blob = adapter_blob(step)
    if ARM in ('F_geo', 'F_null'):   # engineering gate 2: A LoRA untouched
        assert all(torch.equal(blob['adapter'][k], stA['adapter'][k]) for k in stA['adapter']), 'A LoRA changed in a frozen arm'
    torch.save(blob, OUT / 'adapter_final.pt')
    print('[train] DONE', step, 'valid_updates', valid_updates, flush=True)
