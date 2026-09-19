from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures, hashlib, json, subprocess
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent / 'S12_literature_sources'
ROOT.mkdir(exist_ok=True)
SOURCES = [
 ('vmem_arxiv_v3.html', 'https://arxiv.org/html/2506.18903v3'),
 ('covrag_arxiv_v1.html', 'https://arxiv.org/html/2606.02479v1'),
 ('boostmvsnerfs_arxiv_v1.html', 'https://arxiv.org/html/2407.15848v1'),
 ('boostmvsnerfs_author_project.html', 'https://su-terry.github.io/BoostMVSNeRFs/'),
 ('aalto_ji_item.html', 'https://aaltodoc.aalto.fi/items/eb4782f5-85c1-42ea-9774-0e100894887a'),
 ('nam_sejong_bibliography.html', 'https://sejong.elsevierpure.com/en/publications/an-efficient-algorithm-to-select-reference-views-for-virtual-view/'),
]
def now(): return datetime.now(timezone.utc).isoformat()
class Text(HTMLParser):
 def __init__(self): super().__init__(); self.parts=[]
 def handle_data(self,s):
  if s.strip(): self.parts.append(s.strip())
def one(item):
 name,url=item; p=ROOT/name
 if p.exists(): raise FileExistsError(p)
 start=now()
 r=subprocess.run(['curl','--location','--fail','--retry','1','--connect-timeout','15','--max-time','45','--user-agent','Mozilla/5.0','--output',str(p),'--write-out','%{http_code} %{url_effective}',url],capture_output=True,text=True)
 out={'path':str(p.relative_to(ROOT.parent.parent)),'url':url,'started_utc':start,'finished_utc':now(),'returncode':r.returncode,'http_final':r.stdout,'stderr':r.stderr}
 if p.exists():
  b=p.read_bytes();out.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  if r.returncode==0:
   t=Text();t.feed(b.decode('utf-8'));tp=p.with_suffix('.txt');tp.write_text('\n'.join(t.parts)+'\n');out.update(derived_text=str(tp.relative_to(ROOT.parent.parent)),derived_text_sha256=hashlib.sha256(tp.read_bytes()).hexdigest(),conversion='stdlib HTMLParser.handle_data, retains script text; source HTML authoritative')
 return out
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(one,SOURCES))
 (ROOT/'download_manifest.json').write_text(json.dumps({'recorded_utc':now(),'sources':rows},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(rows,ensure_ascii=False,indent=2))
