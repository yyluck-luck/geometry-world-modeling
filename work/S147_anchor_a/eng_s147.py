#!/usr/bin/env python3
"""S147 engineering gate (R273 §7 C), one GPU, no development data.
usage: eng_s147.py <clips.json> <lat_dir> <warp_dir> <adapter_A.pt> <invalid.json> <out.json>
On one valid training clip with F_geo's construction (A + zero-init branch, branch-only allowlist):
 (a) conditional and unconditional losses give finite, nonzero branch-weight gradients; one AdamW step changes the branch;
     every other tensor (base and A LoRA) is byte-identical afterwards; optimizer membership equals the allowlist;
 (b) checkpointed vs ordinary forward loss without grad (relative difference <= 1e-3), and the checkpointed branch gradient
     against a central finite difference along its direction (relative error <= 0.2 at h = 1e-2 or 3e-3); a full
     ordinary-forward backward does not fit 24 GB. Tolerances frozen here, before any development output."""
import json, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s141_common as C
import torch
import torch.nn.functional as F
CL, LAT, WARP, ADA, INV, OUT = [Path(a) for a in sys.argv[1:7]]
dev = 'cuda'; torch.manual_seed(0)
INVALID = set(json.loads(INV.read_text())['invalid_clip_ids'])
clip = next(c for c in json.loads(CL.read_text())['clips'] if c['split'] == 'train' and c['id'] not in INVALID and c['kind'] == 'memory')
refs, lats, embs, c2ws = [], [], [], []
for f in sorted(LAT.glob('*.pt')):
    o = torch.load(f); refs += o['refs']; lats.append(o['lat']); embs.append(o['emb']); c2ws.append(o['c2w'])
IX = {r: i for i, r in enumerate(refs)}; LATG = torch.cat(lats).to(dev); EMBG = torch.cat(embs).to(dev); C2WG = torch.cat(c2ws).to(dev)
o = torch.load(WARP / f"{clip['id']}.pt"); W5 = torch.cat([o['zw'], o['cov'][:, None]], 1).float().to(dev)
Kg = C.model_grid_K(C.K7).to(dev)


def build():
    model = C.load_base_model(dev); torch.manual_seed(0)
    C.add_adapters(model, r=16, alpha=16.0, warp=True)
    st = torch.load(ADA, map_location='cpu', weights_only=False); model.load_state_dict(st['adapter'], strict=False)
    for n, p in model.named_parameters(): p.requires_grad = '.warp.' in n
    return model


ci = [IX[r] for r in clip['ctx']]; ti = [IX[r] for r in clip['tgt']]
with torch.no_grad():
    cond = C.build_cond(LATG[ci], EMBG[ci], C.to_gl(C2WG[ci]), Kg.repeat(4, 1, 1), C.to_gl(C2WG[ti]), Kg)
z = torch.cat([LATG[ci], LATG[ti]]); den = C.DiscreteDenoiser(C.DDPMDiscretization(), num_idx=1000, device=dev)
g = torch.Generator(device=dev); g.manual_seed(123)
idx = torch.tensor([600], device=dev); eps = torch.randn(z.shape, device=dev, generator=g)


def loss_of(net, cc):
    sig = den.sigmas[idx]; x = z + sig * eps
    rep, m = cc['replace'].split((z.shape[1], 1), dim=1); inp = x * (1 - m) + rep * m
    with torch.autocast('cuda', dtype=torch.bfloat16):
        out = net(inp / torch.sqrt(sig ** 2 + 1.0), idx.repeat(8), cc, num_frames=8)
    return F.mse_loss(out.float()[4:], eps[4:])


res = {'clip': clip['id']}
model = build(); model.forward = types.MethodType(C.ckpt_forward, model); net = C.VMemWrapper(model)
names = sorted(n for n, p in model.named_parameters() if p.requires_grad)
params = [p for p in model.parameters() if p.requires_grad]
res['allowlist'] = names; ok = names == ['input_blocks.0.0.warp.bias', 'input_blocks.0.0.warp.weight']
snap = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.0)
res['optimizer_membership_ok'] = len(opt.param_groups[0]['params']) == 2 and all(any(p is q for q in params) for p in opt.param_groups[0]['params'])
for tag in ('c', 'uc'):
    before = [p_.detach().clone() for p_ in params]
    cc = C.extend_concat(cond[tag], W5)
    opt.zero_grad(set_to_none=True); L = loss_of(net, cc); L.backward()
    gw = model.input_blocks[0][0].warp.weight.grad; gb = model.input_blocks[0][0].warp.bias.grad
    res[f'{tag}_loss'] = float(L); res[f'{tag}_grad_norm_w'] = float(gw.norm()); res[f'{tag}_grad_norm_b'] = float(gb.norm())
    ok &= bool(torch.isfinite(L) and torch.isfinite(gw).all() and torch.isfinite(gb).all() and gw.norm() > 0)
    opt.step()                                                           # one update per conditioning case (R274 #9)
    res[f'{tag}_parameter_update'] = any(not torch.equal(p_, b_) for p_, b_ in zip(params, before)); ok &= res[f'{tag}_parameter_update']
after = {k: v.detach().cpu() for k, v in model.state_dict().items()}
changed = [k for k in snap if not torch.equal(snap[k], after[k])]
res['changed_tensors'] = changed; ok &= sorted(changed) == names
del model, net, opt, snap, after; torch.cuda.empty_cache()
# (b) a full ordinary-forward backward does not fit a 24 GB RTX 3090 (measured OOM), so: (b1) no-grad loss of the
#     checkpointed vs ordinary forward (relative difference <= 1e-3); (b2) the checkpointed branch gradient g against a
#     central finite difference of the loss along d = g/|g| (no-grad, same precision): relative error <= 0.2 at h = 1e-2 or 3e-3.
print('[eng] part a done', {k: res[k] for k in ('c_loss', 'uc_loss', 'c_grad_norm_w', 'uc_grad_norm_w')}, flush=True)
m2 = build(); m2.forward = types.MethodType(C.ckpt_forward, m2); n2 = C.VMemWrapper(m2); cc = C.extend_concat(cond['c'], W5)
L = loss_of(n2, cc); L.backward()
wp = [m2.input_blocks[0][0].warp.weight, m2.input_blocks[0][0].warp.bias]
gv = torch.cat([p.grad.detach().flatten().float() for p in wp]); gnorm = float(gv.norm()); d = gv / gv.norm()
with torch.no_grad():
    l_ck = float(loss_of(n2, cc)); del m2.forward; l_pl = float(loss_of(n2, cc)); m2.forward = types.MethodType(C.ckpt_forward, m2)
    rel = abs(l_ck - l_pl) / abs(l_pl); fd = {}
    base_p = [p.detach().clone() for p in wp]
    for h in (1e-2, 3e-3):
        vals = []
        for sgn in (1, -1):
            off = 0
            for p, b0 in zip(wp, base_p):
                n = p.numel(); p.copy_(b0 + sgn * h * d[off:off + n].view_as(p).to(p.dtype)); off += n
            vals.append(float(loss_of(n2, cc)))
        for p, b0 in zip(wp, base_p): p.copy_(b0)
        fd[str(h)] = {'central_difference': (vals[0] - vals[1]) / (2 * h), 'analytic': gnorm, 'rel_err': abs((vals[0] - vals[1]) / (2 * h) - gnorm) / gnorm}
res.update({'ckpt_vs_plain_loss_rel_nograd': rel, 'finite_difference': fd, 'tolerances': {'loss_rel': 1e-3, 'fd_rel_err': 0.2}})
ok &= rel <= 1e-3 and min(v['rel_err'] for v in fd.values()) <= 0.2
res['PASS'] = bool(ok and res['optimizer_membership_ok'])
OUT.write_text(json.dumps(res, indent=1) + '\n'); print(json.dumps({k: v for k, v in res.items() if k != 'allowlist'}))
sys.exit(0 if res['PASS'] else 3)
