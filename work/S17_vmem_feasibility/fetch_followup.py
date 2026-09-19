from pathlib import Path
import subprocess,json,datetime,hashlib,concurrent.futures
OUT=Path(__file__).resolve().parent
jobs=[('sd21_api_retry','GET','https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base?blobs=true'),('clip_api_retry','GET','https://huggingface.co/api/models/laion/CLIP-ViT-H-14-laion2B-s32B-b79K?blobs=true'),('issue2_comments','GET','https://api.github.com/repos/runjiali-rl/vmem/issues/2/comments'),('issue11_comments','GET','https://api.github.com/repos/runjiali-rl/vmem/issues/11/comments'),('vmem_weight_head','HEAD','https://huggingface.co/liguang0115/vmem/resolve/ac5921080a57f5a634f4b9acbbc8f3db67c9d113/vmem_weights.pth'),('cut3r_weight_head','HEAD','https://huggingface.co/liguang0115/cut3r/resolve/b14faf986da0df405cff1b41e60e2975c4da2745/cut3r_512_dpt_4_64.pth')]
def run(job):
 name,method,url=job;p=OUT/(name+'.response');start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 a=['curl','-q','--silent','--show-error','--connect-timeout','10','--max-time','25','--max-filesize','1000000']
 if method=='HEAD':a+=['--head']
 else:a+=['--location']
 c=subprocess.run(a+['--output',str(p),'--write-out','%{http_code}',url],capture_output=True,text=True)
 b=p.read_bytes() if p.exists() else b''
 if method=='HEAD' and b:
  # Do not preserve CDN signed redirects or cookies; sizes/identity/status suffice.
  safe=[line for line in b.decode(errors='replace').splitlines() if line.lower().startswith(('http/','content-length:','content-type:','x-linked-size:','x-linked-etag:','etag:','x-error-code:','x-error-message:'))]
  b=('\n'.join(safe)+'\n').encode();p.write_bytes(b)
 return {'name':name,'method':method,'url':url,'started_utc':start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':c.returncode,'http_status':c.stdout,'stderr':c.stderr,'preserved_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'authenticated':False,'weight_payload_bytes':0,'head_redirects_followed':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(run,jobs))
(OUT/'http_followup_receipts.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
