#!/usr/bin/env python3
"""S146 metadata receipt (R265 §1-2): archive hashes, info.txt/split.txt contents + SHA-256, explicit sequence0/sequence1
parsing (inclusive, disjoint, gap-free), strict pose validation for every frame of both traversals (finite 4x4, last row
[0,0,0,1], ||R^T R - I||_max < 1e-4, |det R - 1| < 1e-4), colour extrinsic identity, raw and staged intrinsics, staged-file
consistency (pose bytes equal, PNG size 640x480), plus the candidate-room audit for the apt2 replacement rule.
usage: metadata_receipt_s146.py <s146_data> <stage12> <zips.sha256> <out.json>"""
import hashlib, json, re, sys
from pathlib import Path
import numpy as np
from PIL import Image
SRC, STAGE, ZH, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_split(txt):
    seqs = {}
    for m in re.finditer(r'(sequence\d+)\s*\[frames=(\d+)\]\s*\[start=(\d+) ; end=(\d+)\]', txt):
        seqs[m.group(1)] = (int(m.group(3)), int(m.group(4)), int(m.group(2)))
    return seqs


def pose_ok(p):
    try:
        P = np.loadtxt(p).reshape(4, 4)
    except Exception:
        return False, 'unparseable'
    if not np.isfinite(P).all(): return False, 'non-finite'
    if not np.allclose(P[3], [0, 0, 0, 1], atol=1e-6): return False, 'last-row'
    R = P[:3, :3]
    if np.abs(R.T @ R - np.eye(3)).max() > 1e-4: return False, 'non-orthonormal'
    if abs(np.linalg.det(R) - 1) > 1e-4: return False, 'det'
    return True, ''


rec = {'archives': ZH.read_text().split('\n'), 'rooms': {}, 'apt2_candidate_audit': {}}
for col, room in (('apt1', 'kitchen'), ('apt2', 'luke'), ('office2', '5a')):
    r = SRC / col / col / room; key = f'{col}_{room}'
    info, split = (r / 'info.txt').read_text(), (r / 'split.txt').read_text()
    seqs = parse_split(split)
    assert 'sequence0' in seqs and 'sequence1' in seqs
    (a0, b0, n0), (a1, b1, n1) = seqs['sequence0'], seqs['sequence1']
    assert n0 == b0 - a0 + 1 and n1 == b1 - a1 + 1 and a0 == 0 and a1 == b0 + 1, (key, seqs)
    bad = {}
    for f in range(a0, b1 + 1):
        ok, why = pose_ok(r / 'data' / f'frame-{f:06d}.pose.txt')
        if not ok: bad[f] = why
    ext = re.search(r'm_calibrationColorExtrinsic = ([^\n]+)', info).group(1).split()
    st = STAGE / key; mism = 0; sizes = set()
    for sname, (a, b) in (('seq-00', (a0, b0)), ('seq-01', (a1, b1))):
        for f in range(a, b + 1):
            if (st / sname / f'frame-{f:06d}.pose.txt').read_bytes() != (r / 'data' / f'frame-{f:06d}.pose.txt').read_bytes(): mism += 1
            if f in (a, b): sizes.add(Image.open(st / sname / f'frame-{f:06d}.color.png').size)
    rec['rooms'][key] = {'info_txt': info, 'info_sha256': sha(r / 'info.txt'), 'split_txt': split, 'split_sha256': sha(r / 'split.txt'),
                         'sequence0': [a0, b0], 'sequence1': [a1, b1], 'invalid_poses': bad,
                         'color_extrinsic_identity': bool(np.allclose(np.array(ext, float).reshape(4, 4), np.eye(4))),
                         'staged_K': np.loadtxt(st / 'camera-intrinsics.txt').tolist(), 'staged_pose_mismatches': mism,
                         'staged_png_sizes_sampled': sorted(sizes)}
    print(key, 'seq0', (a0, b0), 'seq1', (a1, b1), 'invalid', len(bad), 'ext_identity', rec['rooms'][key]['color_extrinsic_identity'], 'pose mism', mism, sizes, flush=True)
for room in ('bed', 'kitchen', 'living', 'luke'):
    r = SRC / 'apt2' / 'apt2' / room; seqs = parse_split((r / 'split.txt').read_text())
    (a0, b0, _), (a1, b1, _) = seqs['sequence0'], seqs['sequence1']
    inv = [f for f in range(a0, b1 + 1) if not pose_ok(r / 'data' / f'frame-{f:06d}.pose.txt')[0]]
    rec['apt2_candidate_audit'][room] = {'sequence0': [a0, b0], 'sequence1': [a1, b1], 'invalid_frames': inv,
                                         'n_invalid_seq0': sum(a0 <= f <= b0 for f in inv), 'n_invalid_seq1': sum(a1 <= f <= b1 for f in inv)}
OUT.write_text(json.dumps(rec, indent=1) + '\n')
print('apt2 audit', {k: (v['n_invalid_seq0'], v['n_invalid_seq1']) for k, v in rec['apt2_candidate_audit'].items()})
