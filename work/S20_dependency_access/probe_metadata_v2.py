from pathlib import Path
import subprocess,json,hashlib,datetime,concurrent.futures,urllib.parse
W=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_dependency_access')
reqs=[('clip_tag', 'https://api.github.com/repos/mlfoundations/open_clip/git/ref/tags/v2.30.0'), ('clip_pretrained', 'https://api.github.com/repos/mlfoundations/open_clip/contents/src/open_clip/pretrained.py?ref=v2.30.0'), ('clip_factory', 'https://api.github.com/repos/mlfoundations/open_clip/contents/src/open_clip/factory.py?ref=v2.30.0'), ('clip_constants', 'https://api.github.com/repos/mlfoundations/open_clip/contents/src/open_clip/constants.py?ref=v2.30.0'), ('clip_architecture', 'https://api.github.com/repos/mlfoundations/open_clip/contents/src/open_clip/model_configs/ViT-H-14.json?ref=v2.30.0'), ('clip_hub_config', 'https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_config.json'), ('stability_readme_api', 'https://api.github.com/repos/Stability-AI/stablediffusion/readme'), ('clip_pypi', 'https://pypi.org/pypi/open-clip-torch/2.30.0/json')]
def run(pair):
 name,url=pair; out=W/(name+'.body');head=W/(name+'.headers.tmp');start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=subprocess.run(['/usr/bin/curl','-q','--silent','--show-error','--location','--max-time','30','--max-filesize','1048576','-H','Authorization:','--output',str(out),'--dump-header',str(head),'--write-out','%{http_code}',url],capture_output=True,text=True)
 raw=head.read_text() if head.exists() else ''; selected=[]
 for line in raw.splitlines():
  if line.lower().startswith(('http/','content-type:','content-length:','x-error-code:','x-error-message:','x-repo-commit:','etag:','x-linked-etag:','x-linked-size:','accept-ranges:')):selected.append(line)
  if line.lower().startswith('location:'):
   v=line.split(':',1)[1].strip();u=urllib.parse.urlsplit(v);selected.append('Location without query: '+urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,'','')))
 if head.exists():head.unlink()
 rec=dict(name=name,url=url,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),curl_returncode=p.returncode,http_status=p.stdout,stderr=p.stderr,headers=selected,body_bytes=out.stat().st_size if out.exists() else 0,sha256=hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,authorization='anonymous; curl config disabled; no token/netrc/cookie access',max_response_bytes=1048576)
 (W/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2)+'\n');return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:
 for r in ex.map(run,reqs):print(json.dumps(r))

