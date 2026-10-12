"""Read-only remote input hashing. No image decoding or experiment here."""
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


if __name__ == '__main__':
    root = Path('/mnt/gluster_dcpu/yiyangliu/gwm_s134')
    gen = root / 'out/s140_confirm_tacc/gen'
    plan_path = root / 'src/s140/plan_confirm.json'
    plan = json.loads(plan_path.read_text())
    receipts = [json.loads(s) for p in sorted(gen.glob('RUNS*.jsonl'))
                for s in p.read_text().splitlines() if s.strip()]
    # Print receipt schema first; parent binds the historical field names explicitly.
    paths = {plan_path, root / 'src/s140/gen_s140.py',
             root / 'src/s140/score_s140.py', gen / 'S140_SCORES.json'}
    paths.update(gen.glob('RUNS*.jsonl'))
    for c in plan['contexts']:
        for seed in (3, 4, 5, 6):
            paths.add(gen / f"{c['ctx_key']}__s{seed}.npy")
        paths.update(root / 'data/S140_warps_chess' / x for x in c['warp_files'])
        for ref in c['target_refs']:
            sq, fr = ref.split('/')
            paths.add(root / 'data/s139_datasets' / c['scene_dir'] / sq / f'frame-{fr}.color.png')
    files = {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths)}
    print(json.dumps({'schema': 'p1-input-manifest-v1', 'files': files,
                      'plan': plan, 'run_receipts': receipts}, sort_keys=True))
