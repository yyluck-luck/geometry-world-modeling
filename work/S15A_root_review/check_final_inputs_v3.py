"""Independent S15A final JSON/source binding review. Does not read PNG/NPZ/PTH."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
checks=[]
def ck(ok,name):
 checks.append(dict(name=name,passed=bool(ok)))
 if not ok:raise ValueError(name)
def sha(p):
 p=Path(p);assert p.suffix in {'.json','.py','.md'},'This review only reads text/source bytes'
 return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_text())
report=dict(schema='s15a-final-input-independent-review-v1',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='RUNNING',checks=checks,real_png_reads=0,npz_reads=0,checkpoint_reads=0,model_calls=0)
try:
 mp=ROOT/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json';m=js(mp);old=js(ROOT/'docs/S14E_MODEL_EXECUTION_MANIFEST.json')
 samples_path=ROOT/'work/S15A_samples_v2/samples.json';samples=js(samples_path)['samples'];combined_path=ROOT/'data/bonn_s15a_history_combined/receipt.json';combined=js(combined_path)
 cps=[ROOT/p for p in ['work/S15A_access/history_contract.json','work/S15A_access/history_resume_contract.json','work/S15A_access/history_resume2_contract.json','work/S15A_access/history_curl_contract_v2.json','work/S15A_access/history_persistent_contract.json']]
 rps=[ROOT/p for p in ['data/bonn_s15a_history/receipt.json','data/bonn_s15a_history_resume1/receipt.json','data/bonn_s15a_history_resume2/receipt.json','data/bonn_s15a_history_curl/receipt.json','data/bonn_s15a_history_persistent/receipt.json']]
 cs=[js(p) for p in cps];rs=[js(p) for p in rps];c0=cs[0]
 ck(cs[1]['members']==c0['members'][11:] and cs[2]['members']==c0['members'][15:] and cs[3]['members']==c0['members'][18:] and cs[4]['members']==c0['members'][18:],'Recovery allowlists are exact uncompleted original tails')
 for i,(c,r,cp,rp) in enumerate(zip(cs,rs,cps,rps)):
  ck(Path(r['contract_path']).resolve()==cp and r['contract_sha256']==sha(cp),'Exact designated contract receipt link '+str(i))
  for key in ('url','archive_total_bytes','central_directory_offset','etag','last_modified','inventory_sha256','samples_sha256','protocol_v2_sha256'):
   ck(c[key]==c0[key],'Same-source frozen '+key+' recovery '+str(i))
  ck((c['fetcher_sha256'] if i<3 else c['zip_parser_sha256'])==c0['fetcher_sha256'],'Same reviewed ZIP parser recovery '+str(i))
  ck(c['samples_sha256']==sha(samples_path),'Samples identity recovery '+str(i))
  ck(r['image_array_decodes']==0 and r['model_calls']==0,'No decodes during acquisition '+str(i))
  ck([x['name'] for x in r['members']]==c['members'][:len(r['members'])],'Completed request prefix '+str(i))
  for j,q in enumerate(r['requests']):
   if 'status' not in q:ck(i<4 and j==len(r['requests'])-1,'Only terminal handshake attempt lacks response');continue
   hdr=q['headers'];rng=q['requested_range'][6:]
   ck(q['status']==206 and q['final_url']==c0['url'] and hdr['ETag']==c0['etag'] and hdr['Last-Modified']==c0['last_modified'],'Exact response identity '+str(i)+'/'+str(j))
   ck(hdr['Content-Range']=='bytes '+rng+'/'+str(c0['archive_total_bytes']),'Exact response range '+str(i)+'/'+str(j))
   lo,hi=map(int,rng.split('-'));ck(q['bytes']==hi-lo+1 and hdr['Content-Encoding'] in (None,'identity') and hdr['Content-Length'] in (None,str(q['bytes'])),'Response byte and encoding '+str(i)+'/'+str(j))
  ck(combined['source_receipt_sha256'][str(rp)]==sha(rp),'Combined source receipt '+str(i))
 ck(rs[0]['status']=='FAIL' and rs[1]['status']=='FAIL' and rs[2]['status']=='FAIL' and rs[3]['status']=='FAIL' and rs[4]['status']=='PASS','Failures preserved, final recovery successful')
 ck([len(r['members']) for r in rs]==[11,4,3,0,2],'Eleven plus four plus three plus zero plus two completion')
 joined=sum((r['members'] for r in rs),[])
 ck(combined['status']=='PASS' and combined['members']==joined,'Combined ordered members exact')
 ck(combined['body_bytes']==sum(r['body_bytes'] for r in rs)<=20*1024**2 and combined['requests']==sum((r['requests'] for r in rs),[]) and len(combined['requests'])<=46,'Aggregate bytes/requests bounded')
 ck(combined['source_sha256']==sha(ROOT/'scripts/assemble_s15a_acquisition.py'),'Actual assembly source frozen')
 ck(len(samples)==24 and [x['index'] for x in samples]==list(range(24)) and [x['role'] for x in samples]==['history']*20+['future_target']*4,'Twenty history and four future metadata roles')
 ck(c0['members']==[x['rgb_member'] for x in samples[:20]]==[x['name'] for x in joined],'No sample replacement across recovery')
 expected_history=[dict(index=i,path=str(Path(x['path']).resolve()),sha256=x['sha256']) for i,x in enumerate(joined)]
 ck(m['history_images']==expected_history and len({x['path'] for x in expected_history})==20,'Final manifest exact twenty paths and acquisition digests')
 ck(m['schema']=='s15-history-manifest-v1' and m['commit']==old['commit']=='8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf','Final schema/commit')
 for role in ('repo','python','checkpoint','rope_check'):ck(m[role]==old[role],'Inherited role '+role)
 mids=m['identities'];repo=Path(m['repo']);up={p:h for p,h in mids.items() if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'};old_up={p:h for p,h in old['identities'].items() if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'}
 ck(len(up)==99 and up==old_up,'Exact inherited ninety-nine source digests')
 for role in ('checkpoint','rope_check'):ck(mids[m[role]]==old['identities'][old[role]],'Inherited byte identity '+role)
 ck(mids[m['checkpoint']]=='7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d','Pinned checkpoint metadata identity')
 adapter=str(ROOT/'scripts/cut3r_rope_compat.py');ck(mids[adapter]==old['identities'][adapter],'Inherited signed adapter digest')
 ck(m['runner']==str(ROOT/'scripts/run_s15_history.py') and mids[m['runner']]=='2a31ca2ee6a9084669ea2ca75fdcb5d40ee727fa7c1a5d64af82f3088c884369','Reviewed new history runner')
 fixed=dict(history_count=20,query_count=0,history_flags=dict(img_mask=True,ray_mask=False,update=True,reset=False),device='cpu',cpu_threads=8,seed=0,size=[224,224],dtype='float32',wall_seconds=600,monitored_rss_bytes=34359738368,external_monitor_required=True,history_rgb_allowed=True,target_rgb_allowed=False,target_depth_allowed=False)
 ck(all(m['contract'].get(k)==v for k,v in fixed.items()),'CPU fixed twenty-history/no-query contract')
 controls=m['control_files'];hpaths={x['path'] for x in expected_history};expected=set(up)|set(controls)|hpaths|{m['runner'],m['checkpoint'],m['rope_check'],adapter}
 ck(set(mids)==expected and len(set(controls))==len(controls),'Exact role union, no hidden array or target identity')
 ck(all(Path(p).suffix in {'.json','.py','.md'} for p in controls) and all(Path(p).name not in {'rgb.txt','depth.txt','groundtruth.txt'} for p in mids),'Controls are text/source, raw index and GT omitted')
 required_controls={str(p) for p in cps+rps+[combined_path,samples_path,ROOT/'scripts/freeze_s15a_history.py',ROOT/'scripts/assemble_s15a_acquisition.py',ROOT/'scripts/run_s14d_controlled.py']}
 ck(required_controls<=set(controls),'Original and recovery provenance frozen as controls')
 for p,h in mids.items():
  if p in hpaths or p==m['checkpoint']:continue
  ck(sha(p)==h,'Current text/source bytes '+p)
 ck(datetime.datetime.fromisoformat(m['frozen_utc'])>=datetime.datetime.fromisoformat(combined['assembled_utc']),'Manifest sealed after actual acquisition assembly')
 report.update(status='PASS',manifest_sha256=sha(mp),manifest=str(mp),identities=len(mids),history_images=expected_history,checkpoint_verification_scope='Inherited SHA checked against prior frozen manifest only; no weight bytes read by this pre-review',image_verification_scope='Paths/digests checked against successful member receipts; PNG bytes not read by this pre-review',source_sha256={str(ROOT/'scripts/freeze_s15a_history.py'):sha(ROOT/'scripts/freeze_s15a_history.py'),str(ROOT/'scripts/assemble_s15a_acquisition.py'):sha(ROOT/'scripts/assemble_s15a_acquisition.py')})
except Exception as e:report.update(status='FAIL',error=repr(e))
report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();out=ROOT/'work/S15A_root_review/final_input_review.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in {'checks','history_images'}},indent=2));print('checks',len(checks));raise SystemExit(0 if report['status']=='PASS' else 1)
