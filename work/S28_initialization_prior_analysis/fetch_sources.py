"""Fetch only small public paper HTML and official source text; no code import/execution."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,urllib.request
OUT=Path(__file__).resolve().parent
URLS={
 'dust3r_paper.html':'https://arxiv.org/html/2312.14132',
 'cut3r_paper.html':'https://arxiv.org/html/2501.12387',
 'pow3r_paper.html':'https://arxiv.org/html/2503.17316',
 'mapanything_paper.html':'https://arxiv.org/html/2509.13414',
 'roma_official_docs.html':'https://naver.github.io/roma/',
 'dust3r_official_init.py.txt':'https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/init_im_poses.py',
 'dust3r_official_base.py.txt':'https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/base_opt.py'}
def fetch(item):
 name,url=item; row=dict(url=url,started_utc=datetime.now(timezone.utc).isoformat())
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Research source archival'})
  with urllib.request.urlopen(req,timeout=25) as r:
   b=r.read(5_000_001);assert len(b)<=5_000_000
   row.update(status=r.status,resolved_url=r.url,content_type=r.headers.get('Content-Type'))
  p=OUT/'sources'/name;p.write_bytes(b)
  row.update(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),outcome='SAVED')
 except Exception as e:row.update(outcome='FAILED',error=type(e).__name__+': '+str(e))
 row['completed_utc']=datetime.now(timezone.utc).isoformat();return row
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,URLS.items()))
(OUT/'source_fetch_receipt.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(rows,ensure_ascii=False))
