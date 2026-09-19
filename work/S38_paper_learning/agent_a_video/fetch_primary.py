from pathlib import Path
import urllib.request,hashlib,json,concurrent.futures
from datetime import datetime,timezone
D=Path(__file__).parent/'materials'
urls={
 'streamingt2v.pdf':'https://openaccess.thecvf.com/content/CVPR2025/papers/Henschel_StreamingT2V_Consistent_Dynamic_and_Extendable_Long_Video_Generation_from_Text_CVPR_2025_paper.pdf',
 'vmem.pdf':'https://openaccess.thecvf.com/content/ICCV2025/papers/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.pdf',
 'worldmem.pdf':'https://proceedings.neurips.cc/paper_files/paper/2025/file/470629a47e2d65ce0606c40055df5d26-Paper-Conference.pdf',
 'longlive.pdf':'https://proceedings.iclr.cc/paper_files/paper/2026/file/91a1610c6ed9e02d33f826b46f472b92-Paper-Conference.pdf',
 'streamingt2v_venue.html':'https://openaccess.thecvf.com/content/CVPR2025/html/Henschel_StreamingT2V_Consistent_Dynamic_and_Extendable_Long_Video_Generation_from_Text_CVPR_2025_paper.html',
 'vmem_venue.html':'https://openaccess.thecvf.com/content/ICCV2025/html/Li_VMem_Consistent_Interactive_Video_Scene_Generation_with_Surfel-Indexed_View_Memory_ICCV_2025_paper.html',
 'worldmem_venue.html':'https://proceedings.neurips.cc/paper_files/paper/2025/hash/470629a47e2d65ce0606c40055df5d26-Abstract-Conference.html',
 'longlive_venue.html':'https://proceedings.iclr.cc/paper_files/paper/2026/hash/91a1610c6ed9e02d33f826b46f472b92-Abstract-Conference.html'
}
def get(item):
 name,url=item;r={'name':name,'url':url,'started_utc':datetime.now(timezone.utc).isoformat(),'timeout_seconds':45,'maximum_bytes':40*1024*1024}
 try:
  q=urllib.request.Request(url,headers={'User-Agent':'Research literature reader'})
  with urllib.request.urlopen(q,timeout=45) as f:
   raw=f.read(40*1024*1024+1);r.update(status=f.status,content_type=f.headers.get('Content-Type'),final_url=f.url)
  if len(raw)>40*1024*1024: raise RuntimeError('paper size exceeded bound')
  if name.endswith('.pdf') and not raw.startswith(b'%PDF'): raise RuntimeError('not a PDF')
  (D/name).write_bytes(raw);r.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),saved=str(D/name))
 except Exception as e:r.update(error_type=type(e).__name__,error=str(e))
 r['completed_utc']=datetime.now(timezone.utc).isoformat();return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e: records=list(e.map(get,urls.items()))
(D.parent/'fetch_receipt.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
for r in records:print(json.dumps(r,ensure_ascii=False))
