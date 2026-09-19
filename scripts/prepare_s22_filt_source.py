"""Pinned FILT3R source preparation while the frozen S21 experiment runs."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/S22_filt_preparation';W.mkdir(parents=True,exist_ok=False)
OUT=W/'filt3r_original';S=ROOT/'work/S21_novelty_search'
REV=json.loads((S/'filt_head.body').read_text())['sha']
TREE=json.loads((S/'filt_tree.body').read_text())['tree']
def blob(d):return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
cache={}
for base in [ROOT/'work/S21_baseline_preparation/ttt3r_original']:
    for p in base.rglob('*'):
        if p.is_file()and p.suffix!='.pyc':d=p.read_bytes();cache[blob(d)]=d
for p in S.glob('*.source'):d=p.read_bytes();cache[blob(d)]=d
def fetch(e):
    r=dict(path=e['path'],git_blob=e['sha'],started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    d=cache.get(e['sha']);r['method']='reuse identical Git blob'
    if d is None:
        r.update(method='anonymous official source',url=f'https://raw.githubusercontent.com/jinotter3/FILT3R/{REV}/{e["path"]}')
        try:
            with urllib.request.urlopen(r['url'],timeout=25)as f:d=f.read(2097153)
        except Exception as ex:r['error']=repr(ex);d=b''
    r.update(passed=blob(d)==e['sha'],bytes=len(d),sha256=hashlib.sha256(d).hexdigest(),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if r['passed']:
        p=OUT/e['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
    (W/'receipts').mkdir(exist_ok=True);(W/'receipts'/(e['path'].replace('/','__')+'.json')).write_text(json.dumps(r,indent=2)+'\n')
    return r
entries=[e for e in TREE if e['type']=='blob'and(e['path'].startswith(('src/','eval/relpose/','eval/public_','datasets_preprocess/'))or e['path']in {'README.md','requirements.txt','eval/eval.md'})]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(fetch,entries))
report=dict(commit=REV,files=results,passed=all(r['passed']for r in results),real_data_decoded=0,model_runs=0)
(W/'source_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(commit=REV,files=len(results),passed=report['passed'],failed=[r['path']for r in results if not r['passed']])))
