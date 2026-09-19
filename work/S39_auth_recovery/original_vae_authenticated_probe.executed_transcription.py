# Transcribed after execution from the visible tool-call heredoc on 2026-09-07.
# This is not a byte-preserved runtime source artifact. The body below reproduces
# the executed Python source as transcribed; it has NOT been executed again.
# Original invocation environment is retained in the adjacent source_record.json.
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, time, signal, logging
import httpx
import huggingface_hub as h
from huggingface_hub.utils import build_hf_headers
logging.disable(logging.CRITICAL)
root=Path.cwd();out=root/'work/S39_auth_recovery'
receipt_path=out/'original_vae_authenticated_probe.json'
report_path=out/'original_vae_authenticated_probe.md'
assert not receipt_path.exists() and not report_path.exists(), 'Refuse to overwrite prior probe'
revision='5ede9e4bf3e3fd1cb0ef2f7a3fff13ee514fdf06'
repo='stabilityai/stable-diffusion-2-1-base'
expected='a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815'
started=datetime.now(timezone.utc).isoformat();transactions=[];sent=[]
class DeadlineExceeded(Exception):pass
class RequestBudgetExceeded(Exception):pass
class BodyLimitExceeded(Exception):pass
def deadline(signum,frame):raise DeadlineExceeded()
signal.signal(signal.SIGALRM,deadline)
def request_hook(request):
 if len(sent)>=2:raise RequestBudgetExceeded()
 sent.append({'ordinal':len(sent)+1,'host':request.url.host,'path':request.url.path,'method':request.method,'authorization_header_present':bool(request.headers.get('authorization')),'dispatch_utc':datetime.now(timezone.utc).isoformat()})
client=httpx.Client(proxy='http://127.0.0.1:7897',timeout=httpx.Timeout(18.0),follow_redirects=False,trust_env=False,event_hooks={'request':[request_hook]})
h.set_client_factory(lambda:client)
# The official SDK normally consumes the authorized saved credential. Its value is never inspected or recorded.
headers=build_hf_headers(token=True)
auth_present=bool(headers.get('authorization'))
requests=[
 ('config',f'https://huggingface.co/{repo}/raw/{revision}/vae/config.json',None),
 ('weight_metadata',f'https://huggingface.co/api/models/{repo}/revision/{revision}',{'blobs':'true'})]
for name,url,params in requests:
 rec={'name':name,'url_without_query':url,'params':params or {},'started_utc':datetime.now(timezone.utc).isoformat(),'method':'GET','authentication_requested_via_official_SDK':True,'authorization_header_present':auth_present,'hard_deadline_seconds':20,'body_limit_bytes':262144,'retry_count':0,'follow_redirects':False}
 begin=time.monotonic();body=bytearray()
 try:
  signal.setitimer(signal.ITIMER_REAL,20.0)
  with h.get_session().stream('GET',url,params=params,headers=headers) as response:
   rec['http_status']=response.status_code
   rec['content_type']=response.headers.get('content-type','')
   for chunk in response.iter_bytes():
    if len(body)+len(chunk)>262144:raise BodyLimitExceeded()
    body.extend(chunk)
   rec['body_bytes']=len(body);rec['body_sha256']=hashlib.sha256(body).hexdigest()
   if response.status_code==200:
    data=json.loads(body)
    if name=='config':
     if not isinstance(data,dict):raise ValueError('config object expected')
     rec['config']=data
     rec['config_git_blob_sha1']=hashlib.sha1(f'blob {len(body)}\0'.encode()+body).hexdigest()
    else:
     rec['repository_fields']={k:data.get(k) for k in ['id','sha','private','gated']}
     rec['revision_matches_requested']=data.get('sha')==revision
     wanted={'vae/config.json','vae/diffusion_pytorch_model.safetensors','vae/diffusion_pytorch_model.bin'}
     rec['selected_file_metadata']=[{k:item.get(k) for k in ['rfilename','size','blobId','lfs'] if k in item} for item in data.get('siblings',[]) if item.get('rfilename') in wanted]
   else:
    rec['error_summary']=f'HTTP {response.status_code}; received {len(body)} bytes of response body. Body text and response URLs are not retained.'
 except BaseException as e:
  rec['exception_type']=type(e).__name__
  rec.setdefault('http_status',None)
  rec['partial_body_bytes']=len(body)
  rec['error_summary']='Request did not complete successfully; exception class only retained, without credential values or URL-bearing exception text.'
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  rec['completed_utc']=datetime.now(timezone.utc).isoformat();rec['elapsed_seconds']=time.monotonic()-begin
 transactions.append(rec)
headers.clear();client.close()
config=transactions[0];meta=transactions[1]
rows=meta.get('selected_file_metadata',[])
weight=next((x for x in rows if x['rfilename']=='vae/diffusion_pytorch_model.safetensors'),None)
configrow=next((x for x in rows if x['rfilename']=='vae/config.json'),None)
identity={
 'original_config_obtained':config.get('http_status')==200 and 'config' in config,
 'original_metadata_obtained':meta.get('http_status')==200 and meta.get('revision_matches_requested') is True,
 'original_safetensors_LFS_sha256':(weight or {}).get('lfs',{}).get('sha256'),
 'matches_prior_ft_mse_published_LFS':(weight or {}).get('lfs',{}).get('sha256')==expected if weight else None,
 'config_git_blob_matches_metadata':config.get('config_git_blob_sha1')==configrow.get('blobId') if configrow and config.get('config_git_blob_sha1') else None,
 'original_weight_payload_downloaded':False,'original_weight_payload_hash_verified':False}
identity['original_publication_edge']= 'ORIGINAL_CONFIG_AND_FIXED_REVISION_METADATA_OBTAINED' if identity['original_config_obtained'] and identity['original_metadata_obtained'] and weight else 'UNKNOWN'
result={'schema':'s39-original-vae-authenticated-probe-v1','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'sdk_version':h.__version__,'auth_mode':'Official HF SDK consuming the user-authorized saved credential; no direct credential-file reads or credential logging','HF_HOME_configured':'/Users/rocket/.cache/huggingface-research-s39','proxy_scope':'process-local existing proxy http://127.0.0.1:7897; no system network changes','requested_revision':revision,'repo':repo,'actual_outgoing_requests':sent,'request_count':len(sent),'max_requests':2,'transactions':transactions,'identity':identity,'model_weight_bytes_downloaded':0,'model_or_scientific_runs':0,'browser_operations':0,'old_unauthenticated_401_reused_as_current_evidence':False,'pre_network_preparation_issue':{'error':'ImportError: configure_http_backend not exported by SDK 1.30.0','resolution':'Inspected public set_client_factory/get_session API and used supported SDK client factory','network_attempts_during_error':0},'status':'COMPLETED_TWO_AUTHENTICATED_SMALL_REQUESTS'}
assert len(sent)<=2
assert all(x['elapsed_seconds']<20.5 for x in transactions)
receipt_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'receipt':str(receipt_path),'request_count':len(sent),'statuses':[{k:x.get(k) for k in ['name','http_status','body_bytes','exception_type','elapsed_seconds']} for x in transactions],'identity':identity,'completed_utc':result['completed_utc']},ensure_ascii=False,indent=2))
