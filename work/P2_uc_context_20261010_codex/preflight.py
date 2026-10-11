"""Read-only manifest: no image decode, reconstruction or model execution."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path('/mnt/gluster_dcpu/yiyangliu/gwm_s134')
A = Path('/mnt/gluster_dcpu/yiyangliu/gwm_s141')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def manifest(plan):
    files=set(); baseline={}; receipts={}
    for p in sorted((A/'eval/chess_A').glob('RUNS*.jsonl')):
        for line in p.read_text().splitlines():
            r=json.loads(line);key=(r['ctx_key'],r['seed'])
            if key in receipts: assert receipts[key]['output']['sha256']==r['output']['sha256']
            receipts[key]=r
    for c in plan['contexts']:
        for ref in c['ctx_refs']:
            sq,f=ref.split('/')
            files.update(ROOT/'data/s139_stage'/c['scene_dir']/sq/f'frame-{f}.{kind}' for kind in ['color.png','pose.txt'])
        for ref in c['target_refs']:
            sq,f=ref.split('/')
            files.add(ROOT/'data/s139_stage'/c['scene_dir']/sq/f'frame-{f}.pose.txt')
            files.add(ROOT/'data/s139_datasets'/c['scene_dir']/sq/f'frame-{f}.color.png')
        files.add(ROOT/'data/s139_stage'/c['scene_dir']/'camera-intrinsics.txt')
        files.update(ROOT/'data/S140_warps_chess'/x for x in c['warp_files'])
        for seed in [3,4]:
            p=A/'eval/chess_A'/f"{c['ctx_key']}__s{seed}.npy"
            record=receipts[(c['ctx_key'],seed)];h=sha(p)
            assert h==record['output']['sha256'],p
            baseline[p.name]={'path':str(p),'sha256':h,'receipt':record}
    files.add(A/'runs/A/adapter_final.pt')
    files.update((ROOT/'src/vmem').rglob('*.py'))
    files.update((ROOT/'src/vmem/configs').rglob('*.yaml'))
    files.update(ROOT/'src/s141'/x for x in ['gen_s141.py','s141_common.py'])
    files.update(p for p in (ROOT/'weights').rglob('*') if p.is_file() and p.suffix in {'.pth','.pt','.safetensors','.json','.yaml','.txt'})
    info={str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)}
    assert info[str(A/'runs/A/adapter_final.pt')]['sha256']=='635e6e319d4dbf40d5db58d42498303c5f15fb32107f976e8c315d173de87818'
    return {'schema':'p2-inputs-v1','files':info,'baseline':baseline,'plan':plan,
            'boundary':'File hashes include query RGB bytes; no pixel arrays or outcome scores decoded.'}


if __name__=='__main__': print(json.dumps(manifest(json.loads(sys.argv[1]))))
