from pathlib import Path
import subprocess,json,datetime,hashlib
out=Path(__file__).resolve().parent
url='https://huggingface.co/liguang0115/cut3r/resolve/b14faf986da0df405cff1b41e60e2975c4da2745/cut3r_512_dpt_4_64.pth'
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
c=subprocess.run(['curl','-q','--silent','--show-error','--head','--location','--connect-timeout','10','--max-time','25','--header','Range: bytes=0-0','--write-out','\nFINAL_STATUS:%{http_code}',url],capture_output=True,text=True)
safe=[x for x in c.stdout.splitlines() if x.lower().startswith(('http/','content-length:','content-type:','accept-ranges:','content-range:','x-linked-size:','x-linked-etag:','etag:','final_status:'))]
p=out/'cut3r_cdn_range_head.txt';p.write_text('\n'.join(safe)+'\n')
r={'started_utc':start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'HEAD','url':url,'request_header':'Range: bytes=0-0','redirects_followed':True,'authenticated':False,'returncode':c.returncode,'stderr':c.stderr,'response_headers':safe,'weight_payload_bytes':0,'note':'Metadata-only HEAD; no actual resumable payload transfer was attempted.'}
(out/'cut3r_cdn_range_head_receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
