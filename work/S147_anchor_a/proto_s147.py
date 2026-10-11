#!/usr/bin/env python3
"""S147 F_null prototype (R273 §7 B): per-channel float64 mean of the warp latents over all four targets and all latent
positions of every valid training clip, in manifest order, cast once to float32. Shared by train_s147.py (via prototype())
and by the pre-training freeze: usage: proto_s147.py <clips.json> <warp_dir> <invalid.json> <out PROTOTYPE.json>"""
import json, sys
from pathlib import Path
import torch


def prototype(zws):
    zsum = torch.zeros(4, dtype=torch.float64); n = 0
    for z in zws:
        assert z.shape == (4, 4, 72, 72) and torch.isfinite(z).all()
        zsum += z.double().sum(dim=(0, 2, 3)); n += 4 * 72 * 72
    return (zsum / n).float()


def encode(p):
    return {'prototype': p.tolist(), 'prototype_hex': [float(x).hex() for x in p.tolist()]}


if __name__ == '__main__':
    CL, WD, INV, OUT = [Path(a) for a in sys.argv[1:5]]
    bad = set(json.loads(INV.read_text())['invalid_clip_ids'])
    ids = [c['id'] for c in json.loads(CL.read_text())['clips'] if c['split'] == 'train' and c['id'] not in bad]
    p = prototype(torch.load(WD / f'{i}.pt')['zw'].float() for i in ids)
    OUT.write_text(json.dumps({**encode(p), 'n_clips': len(ids), 'rule': __doc__.split('\n')[0]}, indent=1) + '\n'); print(encode(p))
