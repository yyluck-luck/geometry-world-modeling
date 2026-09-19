import sys,json,subprocess,hashlib,datetime,pathlib
D=pathlib.Path(__file__).parent
name,url,method=sys.argv[1:]
assert method in ('GET','HEAD')
assert not (D/(name+'.receipt.json')).exists()
old=list(D.glob('*.receipt.json')); used=sum(json.loads(p.read_text()).get('body_bytes',0) for p in old)
assert used<20*1024*1024
cap=min(1024*1024,20*1024*1024-used)
body=D/(name+'.body'); headers=D/(name+'.headers'); start=datetime.datetime.now(datetime.timezone.utc).isoformat()
cmd=['curl','--disable','--silent','--show-error','--connect-timeout','8','--max-time','20','--max-filesize',str(cap),'--dump-header',str(headers),'--output',str(body),'--write-out','%{http_code}','--location','--max-redirs','2']
if method=='HEAD':cmd+=['--head']
cmd+=[url]
r=subprocess.run(cmd,capture_output=True,text=True)
b=body.read_bytes() if body.exists() else b''
rec=dict(name=name,url=url,method=method,started_utc=start,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),returncode=r.returncode,http=r.stdout,stderr=r.stderr,body_bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),cap_bytes=cap,total_local_body_bytes_after=used+len(b),scope='text metadata or headers only; zero RGB/depth/model payload requests')
(D/(name+'.receipt.json')).write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec))
