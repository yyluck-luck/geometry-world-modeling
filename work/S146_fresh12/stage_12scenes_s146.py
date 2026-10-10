#!/usr/bin/env python3
"""S146 staging + window manifests (metadata and resizing only; no image is inspected or scored here).
usage: stage_12scenes_s146.py <s146_data root> <stage12 out> <manifest out dir>
Rooms (protocol): apt1/kitchen, apt2/luke, office2/5a. H = sequence0, C = sequence1 (split.txt). Every frame of both
sequences: color 1296x968 JPEG -> 640x480 PNG (PIL BOX area filter), pose copied; camera-intrinsics.txt from info.txt scaled
per axis with the pixel-centre map x' = (x + 0.5) * s - 0.5. Windows per room: H20 = H[floor(j (N_H - 1) / 19)];
starts s_i = C_first + floor(i (N_C - 106) / 7); bank = H20 + C[s..s+55 step 5]; targets C[s+60, 75, 90, 105];
static C[s, 15, 30, 45]; priming chunks [15, 12] (as S139)."""
import json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
SRC, STAGE, MOUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
ROOMS = [('apt1', 'kitchen'), ('apt2', 'luke'), ('office2', '5a')]
W, H = 640, 480


def info(p):
    d = {}
    for line in p.read_text().splitlines():
        if '=' in line: k, v = line.split('=', 1); d[k.strip()] = v.strip()
    return d


manifests = []
for col, room in ROOMS:
    rdir = SRC / col / col / room; key = f'{col}_{room}'
    inf = info(rdir / 'info.txt'); cw, ch = int(inf['m_colorWidth']), int(inf['m_colorHeight'])
    Kc = np.array([float(x) for x in inf['m_calibrationColorIntrinsic'].split()]).reshape(4, 4)[:3, :3]
    sx, sy = W / cw, H / ch
    K = np.array([[Kc[0, 0] * sx, 0, (Kc[0, 2] + 0.5) * sx - 0.5], [0, Kc[1, 1] * sy, (Kc[1, 2] + 0.5) * sy - 0.5], [0, 0, 1]])
    seqs = [(int(a), int(b)) for a, b in re.findall(r'start=(\d+) ; end=(\d+)', (rdir / 'split.txt').read_text())]
    (h0, h1), (c0, c1) = seqs[0], seqs[1]
    out = STAGE / key; out.mkdir(parents=True, exist_ok=True)
    np.savetxt(out / 'camera-intrinsics.txt', K, fmt='%.6f')
    for sname, (a, b) in (('seq-00', (h0, h1)), ('seq-01', (c0, c1))):
        d = out / sname; d.mkdir(exist_ok=True)
        for f in range(a, b + 1):
            pose = np.loadtxt(rdir / 'data' / f'frame-{f:06d}.pose.txt').reshape(4, 4)
            assert np.isfinite(pose).all() and abs(np.linalg.det(pose[:3, :3]) - 1) < 1e-3, (key, f)
            dst = d / f'frame-{f:06d}.color.png'
            if not dst.exists():
                im = Image.open(rdir / 'data' / f'frame-{f:06d}.color.jpg').convert('RGB'); assert im.size == (cw, ch)
                im.resize((W, H), Image.BOX).save(dst)
            (d / f'frame-{f:06d}.pose.txt').write_text((rdir / 'data' / f'frame-{f:06d}.pose.txt').read_text())
    NH, NC = h1 - h0 + 1, c1 - c0 + 1
    assert NC >= 106 + 7, (key, NC)
    hist = [h0 + (j * (NH - 1)) // 19 for j in range(20)]; assert len(set(hist)) == 20
    starts = [c0 + (i * (NC - 106)) // 7 for i in range(8)]; assert len(set(starts)) == 8 and starts[-1] + 105 <= c1
    ref = lambda s, f: f'{s}/{f:06d}'
    wins = []
    for s in starts:
        wins.append({'window_id': f'{key}_s{s:04d}', 'pair': key, 'room': key, 'history_seq': 'seq-00', 'current_seq': 'seq-01',
                     'start': s, 'bank': [ref('seq-00', f) for f in hist] + [ref('seq-01', s + o) for o in range(0, 60, 5)],
                     'targets': [ref('seq-01', s + o) for o in (60, 75, 90, 105)],
                     'static_recent': [ref('seq-01', s + o) for o in (0, 15, 30, 45)], 'priming_chunks': [15, 12]})
    tg = [t for w in wins for t in w['targets']]; assert len(tg) == len(set(tg)), (key, 'duplicate targets across windows')
    assert all(t not in w['bank'] for w in wins for t in w['targets'])
    m = {'schema': 's146-manifest-v1', 'scene_dir': key, 'intrinsics_640x480': K.tolist(), 'color_size_raw': [cw, ch],
         'H': [h0, h1], 'C': [c0, c1], 'windows': wins}
    (MOUT / f'WINDOW_MANIFEST_{key}.json').write_text(json.dumps(m, indent=1) + '\n'); manifests.append(m)
    print(key, 'K', np.round(K, 2).tolist(), 'H', (h0, h1), 'C', (c0, c1), 'starts', starts, flush=True)
(MOUT / 'WINDOW_MANIFEST_ALL.json').write_text(json.dumps({'schema': 's146-manifest-all-v1', 'rooms': [m['scene_dir'] for m in manifests],
                                                          'windows': [dict(w, scene_dir=m['scene_dir']) for m in manifests for w in m['windows']]}, indent=1) + '\n')
print('windows', sum(len(m['windows']) for m in manifests))
