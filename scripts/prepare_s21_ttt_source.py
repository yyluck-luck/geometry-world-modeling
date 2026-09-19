"""Assemble exact pinned public TTT3R source using Git blob identity checks."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess
ROOT = Path(__file__).resolve().parents[1]
W = ROOT / 'work/S21_baseline_preparation'
OUT = W / 'ttt3r_original'
S = ROOT / 'work/S21_novelty_search'
REV = json.loads((S/'ttt_head.body').read_text())['sha']
TREE = json.loads((S/'ttt_tree.body').read_text())['tree']
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
cache = {}
for base in [WS/'work/cut3r-local', WS/'work/vmem/extern/CUT3R']:
    for p in base.rglob('*'):
        if p.is_file() and p.suffix in {'.py','.md','.txt','.sh','.cpp','.cu','.h'}:
            data=p.read_bytes(); cache[blob(data)]=data
for p in S.glob('*.source'):
    data=p.read_bytes();cache[blob(data)]=data
def fetch(e):
    dest=OUT/e['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    r=dict(path=e['path'],git_blob=e['sha'],started=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if e['sha'] in cache:
        data=cache[e['sha']];r['method']='existing identical Git blob'
    else:
        url=f'https://raw.githubusercontent.com/Inception3D/TTT3R/{REV}/{e["path"]}'
        r.update(method='anonymous raw source',url=url)
        q=subprocess.run(['/usr/bin/curl','-q','-fL','-sS','--max-time','30','--max-filesize','2097152',url],capture_output=True)
        r.update(returncode=q.returncode,error=q.stderr.decode(errors='replace'))
        data=q.stdout
    r.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),passed=blob(data)==e['sha'],ended=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if r['passed']: dest.write_bytes(data)
    (W/'source_receipts').mkdir(exist_ok=True)
    (W/'source_receipts'/ (e['path'].replace('/','__')+'.json')).write_text(json.dumps(r,indent=2)+'\n')
    return r
entries=[e for e in TREE if e['type']=='blob' and (e['path'].startswith(('src/','eval/relpose/','datasets_preprocess/')) or e['path'] in {'README.md','requirements.txt','eval/eval.md'})]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(fetch,entries))
report=dict(commit=REV,files=results,passed=all(x['passed'] for x in results))
(W/'source_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(commit=REV,count=len(results),passed=report['passed'],failed=[x['path'] for x in results if not x['passed']])))
