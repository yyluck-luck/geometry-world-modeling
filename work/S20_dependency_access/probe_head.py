from pathlib import Path
import subprocess,json,hashlib,datetime,urllib.parse
W=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_dependency_access')
url='https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_model.safetensors'
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(['/usr/bin/curl','-q','--silent','--show-error','--head','--location','--max-time','30','-H','Authorization:',url],capture_output=True,text=True)
lines=[]
for line in p.stdout.splitlines():
 if line.lower().startswith(('http/','content-type:','content-length:','x-error-code:','x-error-message:','x-repo-commit:','etag:','x-linked-etag:','x-linked-size:','accept-ranges:')):lines.append(line)
 if line.lower().startswith('location:'):
  v=line.split(':',1)[1].strip();u=urllib.parse.urlsplit(v);lines.append('Location without query: '+urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,'','')))
rec=dict(url=url,method='HEAD',started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),curl_returncode=p.returncode,stderr=p.stderr,headers=lines,model_payload_bytes=0,authorization='anonymous; curl config disabled; no token/netrc/cookie access',signed_redirect_query='not stored')
(W/'clip_weight_head.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))

