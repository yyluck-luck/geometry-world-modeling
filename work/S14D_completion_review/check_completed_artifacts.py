"""Completion identity/receipt audit only; no arrays, images or model decoding."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT=ROOT/'work/S14D_completion_review'
checks=[]
read_paths=set()

def read(name):
    p=ROOT/name
    read_paths.add(str(p))
    return json.loads(p.read_text())

def digest(p):
    p=Path(p);read_paths.add(str(p))
    with p.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def check(label,ok):
    checks.append({'label':label,'ok':bool(ok)})

started=datetime.now(timezone.utc).isoformat()
mf='docs/S14D_RAY_ONLY_EXECUTION_MANIFEST_V2.json'
m=read(mf);m1=read('docs/S14D_RAY_ONLY_EXECUTION_MANIFEST.json')
r=read('results/S14D_ray_only_probe/run_metadata.json')
c=read('work/S14D_execution/caller_receipt.json')
v=read('results/S14D_ray_only_independent/verification.json')
f=read('work/S14D_pre_run_review/final_freeze_check_v2.json')
f1=read('work/S14D_pre_run_review/final_freeze_check.json')
cor=read('work/S14D_preparation/freeze_race_correction.json')
sha=digest(ROOT/mf)
for name,obj in [('production',r),('caller',c),('independent',v),('final_review',f)]:
    check(name+' manifest binding',obj['manifest_sha256']==sha)
check('frozen copied manifest exact',digest(ROOT/'results/S14D_ray_only_probe/frozen_manifest.json')==sha)
check('138 frozen files',len(m['identities'])==138)
current={}
for path,expected in m['identities'].items():
    actual=digest(path);current[path]=actual
    check('current frozen byte identity/'+path,actual==expected)
check('independent before/after exact frozen identity',v['frozen_identity_before']==v['frozen_identity_after']==m['identities'])
check('pre-run 138 identity records exactly frozen',len(f['identity_checks'])==138 and
      {x['path']:x['actual'] for x in f['identity_checks']}==m['identities'] and all(x['ok'] and x['expected']==x['actual'] for x in f['identity_checks']))
check('pre-run 43 groups all passed',f['check_groups']==len(f['checks'])==43 and all(x['ok'] for x in f['checks']) and not f['failed_checks'] and not f['identity_mismatches'])
check('pre-run final before caller start',m['frozen_utc']<f['started_utc']<f['completed_utc']<c['started_utc']<r['started_utc'])
check('completion time sequence',r['completed_utc']<c['completed_utc']<v['started_utc']<v['completed_utc'])
check('production successful',r['status']=='SUCCESS' and r['phase']=='complete' and r['before_after_identity_pass'])
check('caller successful exit and monitor',c['status']=='PASS' and c['returncode']==0 and c['monitor_ok'] and c['before_after_identity_pass'] and not c['timed_out'] and not c['rss_limit_exceeded'])
check('CPU device and 8 threads',r['device']==m['contract']['device']=='cpu' and r['cpu_threads']==m['contract']['cpu_threads']==8)
check('resource budgets monitored',c['limits']=={'seconds':600,'rss_bytes':32*1024**3} and c['elapsed_seconds']<600 and c['maxrss']<32*1024**3)
check('all runtime scope flags false',not any(r[k] for k in ['video_generated','new_model_trained','accuracy_evaluated']))
hist=[x['path'] for x in m['history_images']]
check('20 unique historical images',len(hist)==len(set(hist))==20)
for name in ['image_open_attempt_paths','image_opened_paths','decoded_image_paths']:
    check(name+' matches exact history order',r[name]==hist)
check('all history SHA included',all(m['identities'][x['path']]==x['sha256'] for x in m['history_images']))
expected_counters={'history_rgb_decoded':20,'query_rgb_decoded':0,'gt_files_decoded':0,'query_calls':5,
                   'history_image_open_attempts':20,'history_images_opened':20,'query_call_attempts':5,
                   'query_image_encoder_batches':0,'query_ray_encoder_calls':5}
for key,number in expected_counters.items():check('runtime counter/'+key,r['counters'][key]==number)
check('contract 4 targets and 5 calls',m['contract']['unique_target_count']==4 and m['contract']['call_target_indices']==[0,0,1,2,3])
check('five query records',len(r['query_runs'])==5)
fields=['state_feat','state_pos','init_state_feat','mem','init_mem']
keys=['pts3d_in_self_view','conf_self','rgb','camera_pose','pts3d_in_other_view','conf']
check('five state field domain',set(r['state_before'])==set(fields))
for i,q in enumerate(r['query_runs']):
    check(f'call{i} exact call/target/dummy',q['call']==i and q['target_index']==[0,0,1,2,3][i] and q['dummy']==['nan','zero','nan','nan','nan'][i])
    check(f'call{i} flags',q['flags']=={k:[x] for k,x in m['contract']['query_flags'].items()})
    check(f'call{i} output six keys',q['output_keys']==keys)
    check(f'call{i} tensor input shapes',q['input_shapes']=={'img':[1,3,224,224],'ray_map':[1,224,224,6],'true_shape':[1,2],'camera_pose':[1,4,4]})
    check(f'call{i} clock within production',r['started_utc']<q['started_utc']<q['completed_utc']<r['completed_utc'])
    for field in fields:check(f'call{i} unchanged state hash/{field}',q['state_hashes'][field]==r['state_before'][field]['sha256'])
check('dummy all output exact declared and independently verified',r['dummy_all_outputs_exact'] and v['numerical']['dummy_invariance_all_tensor_keys']==keys)
check('state hash independent references exact',v['numerical']['state_reference_hashes']=={k:r['state_before'][k]['sha256'] for k in fields})
check('three response diagnostics',len(r['response_diagnostics'])==3)
for i,(a,b) in enumerate(zip(r['response_diagnostics'],v['numerical']['response_diagnostics'])):
    check(f'response{i} exact reported diagnostics',a['call']==b['call']==i+2 and a['target_index']==b['target_index']==i+1 and a['threshold']==1e-6 and not a['quality_evidence'] and
          a['max_abs_geometry_difference']==max(b['geometry_max_abs_differences'].values()) and a['response_detected']==b['any_geometry_response_over_1e_6']==(a['max_abs_geometry_difference']>1e-6))
check('response not technical gate',m['contract']['response_is_technical_gate'] is False and v['response_is_technical_pass_gate'] is False and v['numerical']['response_is_not_a_technical_pass_gate'])
check('independent check list all PASS',v['status']=='PASS' and v['check_count']==len(v['checks'])==652 and all(x['status']=='PASS' for x in v['checks']))
check('independent tolerance unchanged',v['atol']==m['contract']['independent_atol']==1e-6 and v['rtol']==m['contract']['independent_rtol']==1e-5)
check('independent saved array scope',v['checked_npz_files']==9 and v['checked_npz_arrays']==75 and v['rays_checked']==4*224*224 and v['query_calls_checked']==5 and v['model_calls']==0 and v['target_images_decoded']==v['gt_or_quality_scores_decoded']==0)
check('production 13 output files',len(r['output_sha256'])==13)
for name,expected in r['output_sha256'].items():check('current output SHA/'+name,digest(ROOT/'results/S14D_ray_only_probe'/name)==expected)
check('independent 14 results same before/after',len(v['result_hashes_before'])==14 and v['result_hashes_before']==v['result_hashes_after'])
check('independent results bind production outputs',v['result_hashes_after']=={**r['output_sha256'],'run_metadata.json':digest(ROOT/'results/S14D_ray_only_probe/run_metadata.json')})
check('independent source unchanged and frozen',v['source_sha256']==v['source_sha256_after']==m['identities'][str(ROOT/'scripts/verify_s14d_ray_only_independent.py')]==digest(ROOT/'results/S14D_ray_only_independent/independent_source_snapshot.py'))
check('production source snapshot is frozen runner',digest(ROOT/'results/S14D_ray_only_probe/source_snapshot.py')==m['identities'][m['runner']])
check('independent caller receipt same now',v['caller_sha256']==digest(ROOT/'work/S14D_execution/caller_receipt.json'))
for name,item in r['loaded_upstream_modules'].items():check('loaded upstream source bound/'+name,item['sha256']==m['identities'][item['path']])
changed=[p for p in m['identities'] if m1['identities'][p]!=m['identities'][p]]
expected_changed=[str(ROOT/'docs/S14D_INDEPENDENT_PREPARATION.md'),str(ROOT/'work/S14D_independent_preparation/receipt.json')]
check('V1 V2 same input domain',set(m1['identities'])==set(m['identities']))
check('V1 only two preparation control hashes changed',set(changed)==set(expected_changed)=={x['path'] for x in cor['changed']}=={x['path'] for x in f1['identity_mismatches']})
for k in ['history_images','checkpoint','runner','repo','commit','python','contract','history_provenance']:
    check('V1 V2 unchanged/'+k,m1[k]==m[k])
check('V1 blocked before model',f1['actual_model_runs']==f1['checkpoint_deserializations']==f1['image_npz_gt_decodes']==0 and cor['model_executions_before_correction']==0)
check('V1 manifest original identity retained',digest(ROOT/'docs/S14D_RAY_ONLY_EXECUTION_MANIFEST.json')==cor['old_manifest_sha256'] and sha==cor['new_manifest_sha256'])
figure=read('work/S14D_reporting/figure_receipt.json')
check('figure input identity bound to production',figure['source_sha256']==r['output_sha256']['query_outputs.npz'])
check('figure plot source SHA',digest(ROOT/'scripts/plot_s14d_ray_only.py')==figure['plot_source_sha256'])
check('figure all five entire maps scope',figure['calls_shown']==list(range(5)) and figure['pixels_per_call']==224*224 and not figure['crop'] and not figure['clipping'] and not figure['smoothing'])
for name,h in figure['outputs'].items():check('figure output SHA/'+name,digest(ROOT/'work/S14D_reporting'/name)==h)
result={'schema':'s14d-completion-machine-audit-v1','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS' if all(c['ok'] for c in checks) else 'BLOCKED','check_count':len(checks),'checks':checks,
        'failed_checks':[c for c in checks if not c['ok']],'scope':'Current byte identity and JSON/source fact consistency; no array numeric recomputation, no model execution, no image/checkpoint decode.',
        'hash_read_files':sorted(read_paths),'actual_array_decodes':0,'actual_model_calls':0,
        'reported_old_independent_checks':652,'reported_old_independent_max_abs_difference':v['max_abs_difference'],
        'identity_count':len(current),'production_output_count':13,'state_metadata_hash_comparisons':25,
        'report_review_pending':True,'figure_visual_review':'PNG actually viewed; five panels, full axes and model-unit colorbar legible; no visible clipping.'}
path=OUT/'machine_receipt.json'
assert not path.exists()
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','check_count','failed_checks','completed_utc']},ensure_ascii=False))
