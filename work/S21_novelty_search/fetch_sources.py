from pathlib import Path
import json,subprocess,hashlib,datetime,concurrent.futures,sys,base64
W=Path(__file__).resolve().parent
repos={'ttt':'Inception3D/TTT3R','filt':'jinotter3/FILT3R','ray':'Brack-Wang/raymap3r'}
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def get(entry):
 name,url=entry;body=W/(name+'.body');receipt=W/(name+'.receipt.json');assert not receipt.exists()
 start=utc();q=subprocess.run(['/usr/bin/curl','-q','-L','-sS','--max-time','30','--max-filesize','2097152','-H','Authorization:','-o',str(body),'-w','%{http_code}',url],capture_output=True,text=True)
 r={'name':name,'url':url,'started_utc':start,'ended_utc':utc(),'curl_returncode':q.returncode,'http_status':q.stdout,'stderr':q.stderr,'body_bytes':body.stat().st_size if body.exists() else 0,'body_sha256':hashlib.sha256(body.read_bytes()).hexdigest() if body.exists() else None,'anonymous':True,'type':'metadata_or_source_only'}
 if q.returncode==0 and q.stdout=='200' and '/contents/' in url:
  j=json.loads(body.read_text());data=base64.b64decode(j['content']);p=W/(name+'.source');p.write_bytes(data);r.update(git_blob_sha=j['sha'],source_path=str(p),source_bytes=len(data),source_sha256=hashlib.sha256(data).hexdigest())
 receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return r
mode=sys.argv[1]
if mode=='heads':requests=[(k+'_head','https://api.github.com/repos/'+v+'/commits/main')for k,v in repos.items()]
elif mode=='trees':requests=[(k+'_tree','https://api.github.com/repos/'+v+'/git/trees/'+json.loads((W/(k+'_head.body')).read_text())['sha']+'?recursive=1')for k,v in repos.items()]
else:
 plans=json.loads((W/(mode+'.json')).read_text());requests=[]
 for k,paths in plans.items():
  rev=json.loads((W/(k+'_head.body')).read_text())['sha']
  for path in paths:requests.append((k+'_'+path.replace('/','__').replace('.','_'),'https://api.github.com/repos/'+repos[k]+'/contents/'+path+'?ref='+rev))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(get,requests))
