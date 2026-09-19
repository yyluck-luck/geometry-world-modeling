from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request, hashlib, json, datetime, re, subprocess

BASE=Path(__file__).resolve().parent
SOURCES=BASE/'sources'
SOURCES.mkdir(exist_ok=True)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def fetch(item):
    name,url=item
    r={'name':name,'url':url,'started_utc':now()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'S15-literature-review/1.0'})
        with urllib.request.urlopen(req,timeout=45) as f:
            b=f.read(12_000_001); r['final_url']=f.url; r['status']=f.status
        if len(b)>12_000_000: raise RuntimeError('source exceeds bounded 12 MB')
        p=SOURCES/name
        if p.exists(): raise FileExistsError(p)
        p.write_bytes(b)
        r.update(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
        if name.endswith('.pdf'):
            txt=p.with_suffix('.txt')
            q=subprocess.run(['pdftotext','-layout',str(p),str(txt)],capture_output=True,text=True)
            r['text_conversion']={'returncode':q.returncode,'stderr':q.stderr,'path':str(txt)}
    except Exception as e: r['error']=repr(e)
    r['completed_utc']=now(); return r

items=[
('mostegel2016.pdf','https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/Mostegel_Using_Self-Contradiction_to_CVPR_2016_paper.pdf'),
('self_adapting_readme.md','https://raw.githubusercontent.com/mattpoggi/self-adapting-confidence/master/README.md'),
('confidentsplat_v1.html','https://arxiv.org/html/2509.16863v1'),
('cut3r_project.html','https://cut3r.github.io/'),
('covrag_v1.html','https://arxiv.org/html/2606.02479v1')]
with ThreadPoolExecutor(max_workers=5) as pool: receipt=list(pool.map(fetch,items))
readme=SOURCES/'self_adapting_readme.md'
if readme.exists():
    m=re.search(r'\[\[Paper\]\]\((https?://[^)]+)\)',readme.read_text())
    if not m: m=re.search(r'(https?://\S+\.pdf)',readme.read_text())
    if m: receipt.append(fetch(('self_adapting2020.pdf',m.group(1))))
(BASE/'source_download_receipt.json').write_text(json.dumps({'recorded_utc':now(),'downloads':receipt},indent=2)+'\n')
print(json.dumps(receipt,indent=2))
