import importlib.util
from pathlib import Path
import subprocess, datetime, hashlib, json
from concurrent.futures import ThreadPoolExecutor
BASE=Path(__file__).resolve().parent
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def fetch(v):
    name,url=v; p=BASE/'sources'/name
    r={'started_utc':now(),'url':url,'path':str(p),'fallback':'curl; cap increased for actual paper size, not research budget'}
    try:
        if p.exists():raise FileExistsError(p)
        x=subprocess.run(['curl','--fail','--location','--max-time','45','--max-filesize','40000000','--output',str(p),url],capture_output=True,text=True,timeout=50)
        r.update(returncode=x.returncode,stderr=x.stderr)
        if x.returncode==0:
            b=p.read_bytes();r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
            if name.endswith('.pdf'):
                t=p.with_suffix('.txt');z=subprocess.run(['pdftotext','-layout',str(p),str(t)],capture_output=True,text=True)
                r['text_conversion']={'returncode':z.returncode,'stderr':z.stderr,'path':str(t)}
    except Exception as e:r['error']=repr(e)
    r['completed_utc']=now();return r
items=[('mostegel2016_arxiv.pdf','https://arxiv.org/pdf/1604.05132v1'),('self_adapting2020.pdf','https://mattpoggi.github.io/assets/papers/poggi2020eccv.pdf'),('confidentsplat_v1.html','https://arxiv.org/html/2509.16863v1')]
with ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(fetch,items))
(BASE/'source_retry_receipt.json').write_text(json.dumps({'recorded_utc':now(),'downloads':r},indent=2)+'\n')
print(json.dumps(r,indent=2))
