#!/usr/bin/env python3
"""S141 precompute: VMem VAE latents + CLIP image embeddings (fp32, the exact gen_s140 encode path) and poses for
every 5th frame of the 7-Scenes training scenes. usage: prep_latents_s141.py <data7_root> <out_dir> <scene>[,<scene>...]
Writes <out_dir>/<scene>__<seq>.pt = {refs, lat [N,4,72,72], emb [N,1024], c2w [N,4,4] (raw OpenCV poses)}."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s141_common as C
import torch

D7, OUT, SCENES = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].split(',')
assert not set(SCENES) - set(C.TRAIN_SCENES), 'only training scenes may be encoded'
OUT.mkdir(parents=True, exist_ok=True)
dev = 'cuda'
ae = C.AutoEncoder(chunk_size=1).to(dev, torch.float32).eval()
clip = C.CLIPConditioner().to(dev, torch.float32).eval()
t0 = time.time()
for sc in SCENES:
    for seq in sorted(p for p in (D7 / sc).glob('seq-*') if p.is_dir()):
        f = OUT / f'{sc}__{seq.name}.pt'
        if f.exists(): continue
        n = len(list(seq.glob('frame-*.color.png')))
        fids = list(range(0, n, 5))
        lats, embs, poses = [], [], []
        for i in range(0, len(fids), 8):
            ch = fids[i:i + 8]
            imgs = torch.stack([C.load_rgb_path(seq / f'frame-{k:06d}.color.png') for k in ch]).to(dev)
            with torch.inference_mode():
                lats.append(ae.encode(imgs, 1).cpu()); embs.append(clip(imgs).cpu())
            poses += [torch.from_numpy(C.load_pose_path(seq / f'frame-{k:06d}.pose.txt')) for k in ch]
        obj = {'refs': [f'{sc}/{seq.name}/{k:06d}' for k in fids], 'lat': torch.cat(lats), 'emb': torch.cat(embs),
               'c2w': torch.stack(poses), 'n_frames': n}
        torch.save(obj, f.with_suffix('.tmp')); f.with_suffix('.tmp').rename(f)
        print(f'[prep] {sc}/{seq.name} {len(fids)} frames lat {tuple(obj["lat"].shape)} {time.time() - t0:.0f}s', flush=True)
print('[prep] done', round(time.time() - t0, 1))
