#!/usr/bin/env python3
"""S145 teacher-forced monitor probe (R263 §4.3; diagnostic only, cannot prune generation arms).
All 32 S141 monitor clips, B's final adapter, the GPU monitor warps used in B's training diagnostics, sigma indices
[50,200,400,600,800,950], fixed noise seed 1000*clip_index + sigma_position (as train_s141.validate), bf16 autocast (as
training). Conditions on the 5 extra channels: correct | zero5 | zero_latent (coverage kept) | stratum_mean (per target,
per exact coverage stratum k=round(64*cov)) | permuted (S145 permutation). Branches: c, uc, and the configured guided
prediction eps_u + s*(eps_c - eps_u) at target frames with s from VMem's MultiviewScaleRule.
Reports per condition and sigma: target eps-MSE, clean-latent MSE = sigma^2 * eps-MSE, sensitivity vs the correct input.
usage: probe_s145.py <clips_s141.json> <lat_dir> <warp_dir (S141 .pt)> <adapter_B.pt> <out.json>"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s141_common as C
import torch
from modeling.sampling import MultiviewScaleRule

CL, LAT, WARP, ADP, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5])
dev = 'cuda'; val = [c for c in json.loads(CL.read_text())['clips'] if c['split'] == 'val']; assert len(val) == 32
refs, lats, embs, c2ws = [], [], [], []
for f in sorted(LAT.glob('*.pt')):
    o = torch.load(f); refs += o['refs']; lats.append(o['lat']); embs.append(o['emb']); c2ws.append(o['c2w'])
IX = {r: i for i, r in enumerate(refs)}
LATG = torch.cat(lats).to(dev); EMBG = torch.cat(embs).to(dev); C2WG = torch.cat(c2ws).to(dev); Kg = C.model_grid_K(C.K7).to(dev)
model = C.load_base_model(dev); torch.manual_seed(0); C.add_adapters(model, r=16, alpha=16.0, warp=True)
st = torch.load(ADP, map_location='cpu', weights_only=False); assert st['variant'] == 'B' and st['step'] == 10000
res_ = model.load_state_dict(st['adapter'], strict=False); assert not res_.unexpected_keys
model.eval(); net = C.VMemWrapper(model)
den = C.DiscreteDenoiser(C.DDPMDiscretization(), num_idx=1000, device=dev); rule = MultiviewScaleRule(min_scale=float(C.CFG.model.cfg_min))
IDX = [50, 200, 400, 600, 800, 950]; CFGS = float(C.CFG.model.cfg)


def perm(zw, cov, cid, tgt):
    zp = zw.clone()
    for j in range(4):
        kk = torch.round(cov[j, 0] * 64).long().flatten().cpu().numpy()
        seed = int.from_bytes(hashlib.sha256(f'S145|145|{cid}|{tgt[j]}'.encode()).digest()[:8], 'little')
        rng = np.random.Generator(np.random.PCG64(seed)); src = np.arange(kk.size)
        for v in np.unique(kk):
            ii = np.where(kk == v)[0]; src[ii] = ii[rng.permutation(len(ii))]
        zp[j] = zw[j].reshape(4, -1)[:, torch.from_numpy(src).to(zw.device)].reshape(4, 72, 72)
    return zp


def strat_mean(zw, cov):
    zm = zw.clone()
    for j in range(4):
        kk = torch.round(cov[j, 0] * 64).long()
        for v in torch.unique(kk):
            m = (kk == v); zm[j][:, m] = zw[j][:, m].mean(1, keepdim=True)
    return zm


rows = []
with torch.no_grad():
    for k, c in enumerate(val):
        ci = [IX[r] for r in c['ctx']]; ti = [IX[r] for r in c['tgt']]
        cond = C.build_cond(LATG[ci], EMBG[ci], C.to_gl(C2WG[ci]), Kg.repeat(4, 1, 1), C.to_gl(C2WG[ti]), Kg)
        z = torch.cat([LATG[ci], LATG[ti]])
        o = torch.load(WARP / f"{c['id']}.pt"); zw, cov = o['zw'].to(dev).float(), o['cov'][:, None].to(dev).float()
        conds = {'correct': torch.cat([zw, cov], 1), 'zero5': torch.zeros(4, 5, 72, 72, device=dev),
                 'zero_latent': torch.cat([torch.zeros_like(zw), cov], 1), 'stratum_mean': torch.cat([strat_mean(zw, cov), cov], 1),
                 'permuted': torch.cat([perm(zw, cov, c['id'], c['tgt']), cov], 1)}
        scale = rule(CFGS, cond['all_c2ws'], cond['all_Ks'], cond['input_masks'])
        s_t = (scale[4:] if torch.is_tensor(scale) else torch.full((4,), float(scale))).to(dev).view(4, 1, 1, 1)
        for j, ix in enumerate(IDX):
            g = torch.Generator(device=dev); g.manual_seed(1000 * k + j); eps = torch.randn(z.shape, generator=g, device=dev)
            sig = den.sigmas[torch.tensor([ix], device=dev)]; x = z + sig * eps
            pred = {}
            for name, w5 in conds.items():
                for br in ('c', 'uc'):
                    cc = C.extend_concat(cond[br], w5)
                    rep, m = cc['replace'].split((4, 1), dim=1); inp = x * (1 - m) + rep * m
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        out = net(inp / torch.sqrt(sig ** 2 + 1.0), torch.tensor([ix], device=dev).repeat(8), cc, num_frames=8).float()
                    pred[(name, br)] = out[4:]
                pred[(name, 'guided')] = pred[(name, 'uc')] + s_t * (pred[(name, 'c')] - pred[(name, 'uc')])
            for (name, br), p in pred.items():
                e = float(((p - eps[4:]) ** 2).mean()); sens = float(((p - pred[('correct', br)]) ** 2).mean())
                rows.append({'clip': c['id'], 'seq': c['C'], 'sigma_index': ix, 'sigma': float(sig), 'condition': name, 'branch': br,
                             'eps_mse': e, 'clean_latent_mse': float(sig) ** 2 * e, 'sensitivity_vs_correct': sens})
        print(c['id'], 'done', flush=True)
summ = {}
for r in rows:
    summ.setdefault(f"{r['branch']}|{r['condition']}|{r['sigma_index']}", []).append((r['eps_mse'], r['clean_latent_mse'], r['sensitivity_vs_correct']))
summ = {k: {'eps_mse': float(np.mean([a for a, _, _ in v])), 'clean_latent_mse': float(np.mean([b for _, b, _ in v])),
            'sensitivity': float(np.mean([s for _, _, s in v]))} for k, v in summ.items()}
OUT.write_text(json.dumps({'schema': 's145-probe-v1', 'precision': 'bf16 autocast (as training)', 'cfg_scale_targets': 'MultiviewScaleRule',
                           'summary': summ, 'rows': rows}, indent=1) + '\n')
print(json.dumps({k: v for k, v in summ.items() if k.startswith('guided')}, indent=1))
