#!/usr/bin/env python3
"""R254 F2: verify a final adapter before evaluation. usage: check_adapter_s141.py <adapter.pt> <A|B> [steps=10000]
Exit 1 unless step == steps, variant/rank match, B has the warp branch, every tensor is finite. Prints the SHA-256."""
import hashlib, sys
import torch
p, v = sys.argv[1], sys.argv[2]; steps = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
st = torch.load(p, map_location='cpu', weights_only=False); ad = st['adapter']
n_lora = sum(1 for k in ad if '.down.' in k or '.up.' in k); n_warp = sum(1 for k in ad if '.warp.' in k)
ok = (st['step'] == steps and st['variant'] == v and st['rank'] == 16 and n_lora == 64 * 4 * 2
      and (n_warp == 2) == (v == 'B') and all(torch.isfinite(t).all() for t in ad.values()))
up_norm = float(sum(t.float().norm() ** 2 for k, t in ad.items() if '.up.' in k) ** 0.5)
sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
print(f'adapter {p} variant {st["variant"]} step {st["step"]} lora_tensors {n_lora} warp_tensors {n_warp} up_norm {up_norm:.4f} sha256 {sha} -> {"OK" if ok else "FAIL"}')
sys.exit(0 if ok else 1)
