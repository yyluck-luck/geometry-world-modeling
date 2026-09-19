#!/usr/bin/env python3
"""Read saved scalar JSON only; no tensor, image, model, optimizer or GT access."""
import datetime, hashlib, json
from pathlib import Path
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT=ROOT/'work/S32_next_decision'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={}
def read(p):
 p=ROOT/p; raw=p.read_bytes(); inputs[str(p)]=hashlib.sha256(raw).hexdigest(); return json.loads(raw)
def trace(p):
 p=ROOT/p; raw=p.read_bytes(); inputs[str(p)]=hashlib.sha256(raw).hexdigest(); return [json.loads(x) for x in raw.splitlines()]
m=read(Path('results/S32_consumer_scoring/metrics.json'))
s=read(Path('results/S32_consumer_scoring/receipt.json'))
assert m['scoring_manifest_sha256']=='091ab3c69fd62c50a57d3ce12f7b404abff370d8fb229381e103a2db4fc2e722'
assert s['status']=='PASS' and s['output_sha256']['metrics.json']==inputs[str(ROOT/'results/S32_consumer_scoring/metrics.json')]
selection=read(Path('work/S32_input_freeze/selected_windows_rgb_sealed.json'))
r={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operation':'saved scalar JSON extraction; not independent numerical rescoring', 'denominator':{k:m[k] for k in ['prespecified_windows','prespecified_groups','prespecified_rows','scored_rows','unavailable_rows']},'windows':{}}
for w in selection['windows']:
 wid=w['id'];item={'rgb_span_seconds':w['frames'][-1]['rgb_time']-w['frames'][0]['rgb_time'],'metrics':{e:{k:g[k] for k in ['absrel','rmse_m','delta1','scored_frames']} for e,g in m['window_groups'][wid].items()}}
 p=Path('results/S32_consumer_windows')/wid
 if wid!='fr2_desk_j1':
  d=read(p/'decomposition.json'); t=trace(p/'GA/C2a/gradient_depth_trace.jsonl'); receipt=read(p/'GA/C2a/receipt.json')
  assert len(t)==400 and [x['actual_adam_steps'] for x in t]==list(range(1,401))
  a,b=t[0]['statistics_before_step'],t[-1]['statistics_after_step']
  item.update(k=d['k'],mu=d['mu'],components=d['components'],nonuniform_rms_log=d['nonuniform_rms_log'],initial_focal=a['focal'],final_focal=b['focal'],initial_pw_scale=a['pw_scale'],final_pw_scale=b['pw_scale'],final_frame_depth_ratio=[f['depth_initial_ratio_mean'] for f in b['frames']],initial_loss=t[0]['loss_before_step'],postfinal_loss=receipt['observer']['postfinal_objective'],trace_rows=len(t),ga_seconds=receipt['ga_with_observation_seconds'])
 r['windows'][wid]=item
assert all(sha(Path(p))==h for p,h in inputs.items())
r['input_sha256']=inputs
(OUT/'evidence_excerpt.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'SAVED_JSON_EXTRACTED','input_json_files':len(inputs),'new_NPZ_GT_model_GA':0,'output_sha256':sha(OUT/'evidence_excerpt.json')},ensure_ascii=False))
