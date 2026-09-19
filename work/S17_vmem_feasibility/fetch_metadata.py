from pathlib import Path
import subprocess,json,datetime,hashlib,concurrent.futures
OUT=Path(__file__).resolve().parent
jobs=[
 ('github_main','https://api.github.com/repos/runjiali-rl/vmem/commits/main'),
 ('github_issues','https://api.github.com/repos/runjiali-rl/vmem/issues?state=all&per_page=30'),
 ('vmem_api','https://huggingface.co/api/models/liguang0115/vmem?blobs=true'),
 ('cut3r_api','https://huggingface.co/api/models/liguang0115/cut3r?blobs=true'),
 ('sd21_api','https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base?blobs=true'),
 ('clip_api','https://huggingface.co/api/models/laion/CLIP-ViT-H-14-laion2B-s32B-b79K?blobs=true'),
 ('space_api','https://huggingface.co/api/spaces/liguang0115/vmem'),
 ('pytorch_sdpa','https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.scaled_dot_product_attention.html'),
]
def run(job):
 name,url=job; p=OUT/(name+'.response'); start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 args=['curl','-q','--silent','--show-error','--location','--connect-timeout','10','--max-time','25','--max-filesize','1000000','--header','Accept: application/json','--output',str(p),'--write-out','%{http_code}',url]
 c=subprocess.run(args,text=True,capture_output=True); b=p.read_bytes() if p.exists() else b''
 return {'name':name,'url':url,'started_utc':start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':c.returncode,'http_status':c.stdout,'stderr':c.stderr,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'local_path':str(p),'authenticated':False,'model_weight_bytes_downloaded':0}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: receipts=list(ex.map(run,jobs))
(OUT/'http_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k in ['name','returncode','http_status','bytes','stderr']} for r in receipts],indent=2))
