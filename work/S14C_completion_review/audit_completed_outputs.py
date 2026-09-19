#!/usr/bin/env python3
"""Completion audit of saved outputs and file identities; no geometry/rank recomputation."""
from pathlib import Path
import json,csv,hashlib,math,datetime,collections,traceback
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
O=R/'work/S14C_completion_review'
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
checks=0; errors=[]; reads={}
def load(p):
 p=R/p; b=p.read_bytes();reads[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return json.loads(b)
def hashfile(p):
 p=R/p; h=hashlib.sha256(p.read_bytes()).hexdigest();reads[str(p.relative_to(R))]=h;return h
def check(ok,name):
 global checks
 checks+=1
 if not ok: errors.append(name);raise AssertionError(name)
def same(a,b,name):check(a==b,name)
def close(a,b,name):check(abs(a-b)<=1e-12+1e-10*abs(b),name)
def dt(x):return datetime.datetime.fromisoformat(x)
def compare(a,b,name,allow_close=False):
 if type(b) is dict:
  same(set(a),set(b),name+'/keys')
  for k in b:compare(a[k],b[k],name+'/'+str(k),allow_close)
 elif type(b) is list:
  same(len(a),len(b),name+'/length')
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,name+'/'+str(i),allow_close)
 elif type(b) is float and allow_close:close(a,b,name)
 else:same(a,b,name)
def csvcheck(path,columns,rows):
 p=R/path; hashfile(path)
 with p.open() as f:
  rd=csv.DictReader(f);same(rd.fieldnames,columns,path+'/columns');actual=list(rd)
 same(len(actual),len(rows),path+'/row count')
 for i,(a,b) in enumerate(zip(actual,rows)):
  for k in columns:
   v=b[k]
   if type(v) is float:same(float(a[k]),v,f'{path}/{i}/{k}')
   else:same(a[k],'' if v is None else str(v),f'{path}/{i}/{k}')
report={'schema':'s14c-completed-output-audit-v1','status':'RUNNING','started_utc':started}
try:
 mf='docs/S14C_EXECUTION_MANIFEST.json';m=load(mf);mh=reads[mf]
 expected={x['path']:x['sha256'] for x in m['inputs']+[m['score_input']]+m['controls']}
 expected[mf]=mh
 same(len(m['inputs']),32,'prediction input count');same(len(m['controls']),31,'control count');same(len(expected),65,'bound identity count')
 for p,h in expected.items():same(hashfile(p),h,'live bound/'+p)
 base='results/S14C_selection_disagreement'
 assoc='results/S14C_exploratory_association'
 independent='results/S14C_independent_verification'
 mm=load(base+'/run_metadata.json');am=load(assoc+'/run_metadata.json');v=load(independent+'/verification.json')
 same(mm['status'],'SUCCESS','measurement status');same(am['status'],'SUCCESS','association status');same(v['status'],'PASS','verification status');same(v['errors'],[],'independent errors')
 for metadata in [mm,am,v]:
  same(metadata['manifest_sha256'],mh,'manifest bound to stage')
 same(mm['source_sha256'],m['source_sha256'],'measurement source');same(am['source_sha256'],m['source_sha256'],'association source');same(v['source_sha256'],m['independent_verifier_sha256'],'verifier source')
 same(v['atol'],1e-12,'unchanged atol');same(v['rtol'],1e-10,'unchanged rtol')
 seal=load(base+'/measure_seal.json');same(len(seal['files']),8,'eight sealed payloads')
 meas_hash={p:hashfile(base+'/'+p) for p in list(seal['files'])+['measure_seal.json']}
 for p,h in seal['files'].items():same(meas_hash[p],h,'seal/'+p)
 assoc_hash={p.name:hashfile(assoc+'/'+p.name) for p in (R/assoc).iterdir() if p.is_file()}
 same(len(assoc_hash),8,'eight association payloads')
 for stage,metadata,outdir in [('measure',mm,base),('associate',am,assoc)]:
  for p,h in metadata['output_sha256'].items():same(hashfile(outdir+'/'+p),h,'metadata output/'+p)
  same(metadata['source_sha256_after'],m['source_sha256'],'source after')
  same(metadata['manifest_sha256_after'],mh,'manifest after')
  ident=load(outdir+'/input_identity.json');compare(ident['before'],ident['after'],'producer input identity');compare(ident['before'],{x['path']:x['sha256'] for x in m['inputs']},'producer expected input identity')
 compare(v['input_hashes_before'],v['input_hashes_after'],'independent input identity')
 same(v['score_hash_before'],m['score_input']['sha256'],'independent score before');same(v['score_hash_after'],m['score_input']['sha256'],'independent score after')
 compare(v['measurement_hashes_before'],meas_hash,'independent measured artifacts')
 compare(v['association_hashes_before'],assoc_hash,'independent association artifacts')
 callers={}
 for stage,metadata in [('measure',mm),('associate',am),('verify',v)]:
  c=load(f'work/S14C_execution/{stage}/caller_receipt.json');callers[stage]=c
  same(c['status'],'PASS',stage+'/caller status');same(c['exit_code'],0,stage+'/exit')
  same(c['timeout_seconds'],600,stage+'/timeout');same(c['bound_file_count'],65,stage+'/bound count')
  compare(c['identity_before'],expected,stage+'/caller before');compare(c['identity_after'],expected,stage+'/caller after')
  compare(c['measure_files_after'],meas_hash,stage+'/measure outputs after')
  if 'measure_files_before'in c:compare(c['measure_files_before'],meas_hash,stage+'/measure outputs before')
  if 'associate_files_before'in c:compare(c['associate_files_before'],assoc_hash,stage+'/associate outputs before');compare(c['associate_files_after'],assoc_hash,stage+'/associate outputs after')
  rp=independent+'/verification.json' if stage=='verify' else (base if stage=='measure' else assoc)+'/run_metadata.json'
  same(c['result_receipt_sha256'],hashfile(rp),stage+'/bound run receipt')
  check(dt(c['spawned_utc'])<=dt(metadata['started_utc'])<=dt(metadata['completed_utc'])<=dt(c['child_finished_utc']),stage+'/actual time bounds')
 check(dt(m['frozen_utc'])<dt(mm['started_utc'])<dt(mm['completed_utc'])<=dt(seal['sealed_utc'])<dt(callers['associate']['measure_seal_verified_utc'])<dt(am['started_utc'])<dt(am['measurement_seal_verified_utc'])<dt(am['score_first_read_utc'])<dt(am['completed_utc'])<dt(v['started_utc']),'production freeze seal label chronology')
 check(dt(v['all_32_inputs_verified_utc'])<dt(v['prediction_reconstruction_completed_utc'])<dt(v['score_first_read_utc'])<dt(v['completed_utc']),'independent prediction before label')
 same(mm['counters']['score_hash_reads'],0,'measure no score byte reads');same(mm['counters']['score_json_decoded'],0,'measure no score decode');same(mm['counters']['measurement_csv_decoded'],2,'2CSV');same(mm['counters']['measurement_json_decoded'],30,'30JSON')
 same(am['counters']['score_json_decoded'],1,'associate one score JSON')
 rowsdoc=load(base+'/rows.json');rows=rowsdoc['rows']; joined_doc=load(assoc+'/joined_rows.json');joined=joined_doc['rows']
 details=load(base+'/point_details.json')['rows'];provenance=load(base+'/selection_provenance.json')['rows']
 keys=[(s,b,q) for s in ['S7','S8'] for b in range(3) for q in range(20,24)]
 key=lambda r:(r['stage'],r['block'],r['query'])
 same([key(x) for x in rows],keys,'24 measurement keys');same([key(x) for x in joined],keys,'24 joined keys');same([key(x) for x in details],keys,'24 detail keys')
 csvcheck(base+'/rows.csv',rowsdoc['columns'],rows);csvcheck(assoc+'/joined_rows.csv',joined_doc['columns'],joined)
 for r,j,d,p in zip(rows,joined,details,provenance):
  for col in rowsdoc['columns']:same(j[col],r[col],'sealed scalar preserved/'+col)
  same(r['status'],'OK','row OK');same(len(d['source_count_grid']),25,'25 grid cells')
  same({(x['k_g'],x['k_p']) for x in d['source_count_grid']},{(a,b) for a in range(5) for b in range(5)},'grid domain')
  same(sum(x['n_points'] for x in d['source_count_grid']),r['n_points'],'grid total')
  same(sum(x['n_points'] for x in d['source_count_grid'] if x['k_g']>=2 and x['k_p']>=2),r['common_points'],'grid common')
  same(len(d['points']),r['common_points'],'all common components retained')
  same(len({x['point_id'] for x in d['points']}),r['common_points'],'unique common point IDs')
  same(r['common_fraction'],r['common_points']/r['n_points'],'common fraction')
  same(r['common_fraction_of_g'],r['common_points']/r['eligible_g'],'G fraction')
  same(r['common_fraction_of_p'],r['common_points']/r['eligible_p'],'P fraction')
  same(d['g_selected'],p['g']['selected'],'G selection provenance');same(d['p_selected'],p['p']['selected'],'P selection provenance')
  same(r['same_selected_set'],set(d['g_selected'])==set(d['p_selected']),'G=P flag')
 same(sum(r['n_points'] for r in rows),mm['counters']['point_visits'],'point visit counters')
 same(sum(r['common_points'] for r in rows),mm['counters']['common_point_visits'],'common visit counters')
 same(sum(d['pair_visits'] for d in details),mm['counters']['pair_visits'],'pair visit counters')
 actual_assoc=load(assoc+'/associations.json')['rows']; independent_assoc=load(independent+'/independent_associations.json')['rows']
 same(len(actual_assoc),32,'32 correlations');compare(actual_assoc,independent_assoc,'all32 independently recorded results',True)
 metrics=m['group_contract']['metrics'];same({(r['stage'],r['block'],r['metric']) for r in actual_assoc},{(s,b,z) for s in ['S7','S8'] for b in [None,0,1,2] for z in metrics},'eight group full metric domain')
 for a in actual_assoc:
  rr=[r for r in joined if r['stage']==a['stage'] and (a['block'] is None or r['block']==a['block'])]
  same(a['n_total'],len(rr),'group n');same(a['n_usable'],len(rr),'group usable');same(a['n_missing'],0,'no missing');same(a['excluded_keys'],[],'excluded none');same(a['usable_keys'],[list(key(x)) for x in rr],'same query domain')
  constant=len({r[a['metric']] for r in rr})==1 or len({r['y_pose_minus_geometry_pp'] for r in rr})==1
  same(a['rho'] is None,constant,'null iff constant');same(a['reason'],'constant_x_or_y' if constant else None,'null reason')
 blockcounts=[]
 for s in ['S7','S8']:
  for b in range(3):
   rr=[r for r in joined if r['stage']==s and r['block']==b];dd=[d for d in details if d['stage']==s and d['block']==b]
   sc=collections.Counter((tuple(sorted(d['g_selected'])),tuple(sorted(d['p_selected']))) for d in dd);xc=collections.Counter(r['disagreement_g_minus_p'] for r in rr)
   blockcounts.append(dict(stage=s,block=b,rows=len(rr),selection_groups=len(sc),selection_duplicate_extra_rows=sum(n-1 for n in sc.values()),selection_equal_query_pairs=sum(n*(n-1)//2 for n in sc.values()),x_values=len(xc),x_duplicate_extra_rows=sum(n-1 for n in xc.values()),x_equal_query_pairs=sum(n*(n-1)//2 for n in xc.values()),y_values=len({r['y_pose_minus_geometry_pp'] for r in rr})))
 primary=[a for a in actual_assoc if a['metric']=='disagreement_g_minus_p']
 overs=[dict(stage=a['stage'],block=a['block'],metric=a['metric'],rho=a['rho'],overshoot=abs(a['rho'])-1) for a in actual_assoc if a['rho'] is not None and abs(a['rho'])>1]
 same(len(overs),4,'four preserved floating overshoots');check(all(v['overshoot']==2.220446049250313e-16 for v in overs),'tiny overshoot matches report')
 report.update(status='PASS',live_bound_files=65,group_count=8,correlation_rows=32,null_correlations=sum(a['rho'] is None for a in actual_assoc),all_query_status_ok=True,missing_queries=[],same_g_p_rows=sum(r['same_selected_set'] for r in rows),common_points_range=[min(r['common_points'] for r in rows),max(r['common_points'] for r in rows)],common_fraction_range=[min(r['common_fraction'] for r in rows),max(r['common_fraction'] for r in rows)],block_duplicate_counts=blockcounts,primary_correlations=primary,floating_overshoots=overs,calculation_counters=mm['counters'],independent_verification_counts={k:v[k] for k in ['exact_checks','float_checks','max_abs_difference']},caller_peak_rss={s:c['child_peak_rss_bytes'] for s,c in callers.items()},actual_stage_times={s:{'started_utc':x['started_utc'],'completed_utc':x['completed_utc']} for s,x in [('measure',mm),('associate',am),('verify',v)]})
except BaseException as e:
 report.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
 raise
finally:
 report.update(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),check_count=checks,errors=errors,read_sha256=reads,scope='Saved-output values/counts/transcription and SHA only; no original array decoding, no geometry/rank algorithm rerun, no production imports.')
 with (O/'machine_receipt.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:report[k] for k in ['status','completed_utc','check_count','errors']}))

