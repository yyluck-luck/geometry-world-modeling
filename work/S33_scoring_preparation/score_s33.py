#!/usr/bin/env python3
"""S33: import all48 sealed S32 scores, score only one new16-row condition."""
from __future__ import annotations
import argparse,copy,csv,hashlib,importlib.util,io,json,os
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WINDOWS=('fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2')
OLD_ENDS=('initial_0step','corrected_getter_400','global_rescaled_400')
NEW='common_pair_scale_400'
ENDS=OLD_ENDS+(NEW,)
S32=ROOT/'results/S32_consumer_scoring'
S32_HELPER=ROOT/'work/S32_scoring_preparation/score_s32.py'
ORIGINAL=ROOT/'scripts/score_s26b_consumer.py'
SELECTION=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json'
SELSHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
PRODUCERS=ROOT/'results/S33_pair_scale_control'
OUT=ROOT/'results/S33_pair_scale_scoring'
S33_CONTRACT=ROOT/'work/S33_preparation/contract.json'
DISPATCH=ROOT/'work/S33_execution/dispatch_receipt.json'
FIXED={
 str(S32/'receipt.json'):'834627965eaa4198e42a8a00c43951949bf45a15bbdd0e28f871e63d98017b37',
 str(S32/'metrics.json'):'975ad404667a24032ca3c3c5bcfa61fc70dc1f38ef3dd14391df9c4dd2b0bbbf',
 str(S32/'per_frame.csv'):'1743010707fdb9dc1cdd7b6801b51b8f5eb8c8d99fcb10f95b32b5d906ca700d',
 str(ROOT/'work/S32_scoring_preparation/manifest.json'):'091ab3c69fd62c50a57d3ce12f7b404abff370d8fb229381e103a2db4fc2e722',
 str(ROOT/'work/S32_independent_numeric_review_v2/receipt.json'):'2933625352cc2edb2d5581d78418eaffdc0ae108b8bbae41333a5fac8fbb2a97'}
HELPER_SHA='adb646284110b38741c311e893064558ca4d409ecc3b5e7e75c4540f1203c319'
ORIGINAL_SHA='02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def require(ok,why):
    if not ok:raise ValueError(why)
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def run(path,expected_sha):
    require(sha(path)==expected_sha,'Explicit frozen scoring manifest SHA')
    c=read(path);require(c['status']=='FROZEN' and c['schema']=='s33-import48-score16-v1','Unbound candidate cannot run')
    require(c['output_root']==str(OUT) and c['endpoints']==list(ENDS),'Fixed4condition output scope')
    require(c['resource']==dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),'Fixed caller120s2GiBCPU1 budget')
    require(c['old_scoring_sha256']==FIXED,'Unchanged frozen old48 source identities')
    require(c['selection_path']==str(SELECTION) and c['selection_sha256']==SELSHA,'Fixed original window selection')
    require([w['id'] for w in c['windows']]==list(WINDOWS),'Full ordered4window domain')
    controls=c['control_sha256'];required={str(Path(__file__).resolve()),str(HERE/'protocol.md'),str(S32_HELPER),str(ORIGINAL)}
    require(required<=set(controls) and controls[str(S32_HELPER)]==HELPER_SHA and controls[str(ORIGINAL)]==ORIGINAL_SHA,'Original metric and missing-value functions fixed')
    require(not OUT.exists(),'Existing score output never overwritten');OUT.mkdir()
    receipt=dict(status='RUNNING',started_utc=utc(),scoring_manifest_sha256=expected_sha,new_model=0,new_GA=0,new_MST=0,new_backward=0,
        sensor_GT_bytes_started=False,old_endpoint_array_reads=0,new_k_computations=0)
    write(OUT/'receipt.json',receipt)
    try:
        ids={str(path):expected_sha,str(SELECTION):SELSHA,**FIXED,**controls}
        for p,h in ids.items():require(sha(p)==h,'Changed scoring/source identity: '+p)
        # Import only S32 JSON/CSV; do not recursively reopen old input arrays or GT.
        oldraw=(S32/'metrics.json').read_bytes();csvraw=(S32/'per_frame.csv').read_bytes()
        old=json.loads(oldraw);prior=read(S32/'receipt.json');oldmanifest=read(ROOT/'work/S32_scoring_preparation/manifest.json')
        review=read(ROOT/'work/S32_independent_numeric_review_v2/receipt.json')
        require(prior['status']=='PASS' and review['status']=='PASS_INDEPENDENT_SAVED_NUMERIC_REVIEW','Old table has both actual main and independent PASS')
        require(prior['output_sha256']['metrics.json']==FIXED[str(S32/'metrics.json')] and prior['output_sha256']['per_frame.csv']==FIXED[str(S32/'per_frame.csv')],'Old source receipt binds exact table bytes')
        require(old['scoring_manifest_sha256']==FIXED[str(ROOT/'work/S32_scoring_preparation/manifest.json')],'Old table/frozen policy identity')
        oldrows=old['per_frame'];domain={(w,e,i) for w in WINDOWS for e in OLD_ENDS for i in range(4)}
        require(len(oldrows)==48 and {(r['window_id'],r['endpoint'],r['index']) for r in oldrows}==domain,'All original48 rows, including12NA')
        source_windows={w['id']:w for w in oldmanifest['windows']};selection=read(SELECTION)
        require([w['id'] for w in selection['windows']]==list(WINDOWS),'Original selection unchanged')
        eligible=list(WINDOWS[1:]);require([w['id'] for w in oldmanifest['windows'] if w['availability']=='AVAILABLE']==eligible,'Keep original3pose-eligible domain')
        (OUT/'imported_s32_metrics.json').write_bytes(oldraw);(OUT/'imported_s32_per_frame.csv').write_bytes(csvraw)
        require(sha(OUT/'imported_s32_metrics.json')==FIXED[str(S32/'metrics.json')] and sha(OUT/'imported_s32_per_frame.csv')==FIXED[str(S32/'per_frame.csv')],'Original tables copied byte-for-byte')
        pref=c['producer_contract'];require(pref['path']==str(S33_CONTRACT) and sha(pref['path'])==pref['sha256'],'New formal producer contract')
        ids[pref['path']]=pref['sha256'];pc=read(pref['path'])
        require(pc['status']=='FROZEN' and pc['schema']=='s33-initial-pair-scale-mean-control-v1','Exact new producer experiment')
        require(pc['selection_sha256']==SELSHA and pc['steps']==400 and pc['endpoints']==[NEW] and pc['output_root']==str(PRODUCERS),'No new endpoint substitution')
        # Policy B JSON is declared and hashed by caller controls before reading.
        policy_path=ROOT/'work/S32_preparation/B_contract.json'
        require(str(policy_path) in controls and controls[str(policy_path)]=='340c1b7b9e246fb088db8a50194d3003e1e384ecb05a24dc901bda2ff7bdca60','Policy source explicitly sealed')
        require(pc['scoring_policy']==read(policy_path)['scoring_policy'],'Same frozen metric policy')
        bref=c['terminal_barrier'];require(bref['path']==str(DISPATCH) and sha(bref['path'])==bref['sha256'],'All4new terminal barrier identity')
        ids[bref['path']]=bref['sha256'];barrier=read(bref['path'])
        require(barrier['status']=='COMPLETE_FIXED_WINDOW_MATRIX_SEALED' and barrier['contract_sha256']==pref['sha256'] and barrier['selection_sha256']==SELSHA,'Actual4window completion barrier')
        require(set(barrier['windows'])==set(WINDOWS),'No missing terminal window')
        producers={};arrays_to_read={};gt_needed=[]
        for w in c['windows']:
            wid=w['id'];require(w['frames']==source_windows[wid]['frames'],'Re-use exact frozen GT associations/SHA; no new match or GT hash in preparation')
            rp=Path(w['producer_receipt']['path']);require(rp==PRODUCERS/wid/'receipt.json' and sha(rp)==w['producer_receipt']['sha256'],'Exact new producer receipt')
            ids[str(rp)]=w['producer_receipt']['sha256'];r=read(rp)
            require(r['window_id']==wid and r['selection_sha256']==SELSHA and r['contract_sha256']==pref['sha256'],'Producer identity and shared selection')
            require(barrier['windows'][wid]==dict(status=r['status'],receipt_sha256=sha(rp)),'Dispatcher binds actual whole-window terminal record')
            status=w['availability'];expected='UNAVAILABLE' if wid==WINDOWS[0] else 'PASS' if status=='AVAILABLE' else 'FAILED'
            require(status==('UNAVAILABLE_MISSING_POSE' if wid==WINDOWS[0] else status) and (wid==WINDOWS[0] or status in ('AVAILABLE','UNAVAILABLE_PRODUCER_FAILED')),'No pending windows silently becomeNA')
            require(r['status']==expected,'Actual PASS/FAILED or fixed missingpose status')
            if wid==WINDOWS[0]:require(r['reason']=='MISSING_GIVEN_CAMERA_ASSOCIATION','Original missing-pose cause preserved')
            require(isinstance(w['reason'],str) and (status=='AVAILABLE' or bool(w['reason'])),'Explain missing new candidate')
            item=w['endpoint'];require(item['name']==NEW and item['depth_key']=='depth' and item['dtype']=='float32','One new FP32depth-only endpoint')
            if status=='AVAILABLE':
                ap=PRODUCERS/wid/(NEW+'.npz');require(item['status']=='AVAILABLE' and item['path']==str(ap) and r['outputs'][ap.name]==item['sha256'],'Candidate is exact PASS output')
                require(r['candidate_available'] is True,'Complete candidate, no partial initialization scoring')
                arrays_to_read[wid]=item
                for f in w['frames']:
                    require(isinstance(f['depth_sha256'],str) and len(f['depth_sha256'])==64,'Existing S32 sensor SHA')
                    gt_needed.append(dict(window_id=wid,index=f['index'],rgb_time=f['rgb_time'],depth_time=f['depth_time'],path=f['depth_path'],sha256=f['depth_sha256']))
            else:require(item['status']=='UNAVAILABLE' and item['path'] is None and item['sha256'] is None,'Failed candidate4NA; do not affect old48')
            producers[wid]=(rp.parent,r)
        # Every successful new product is byte-sealed before any prediction decoding or GT byte.
        for directory,r in producers.values():
            if r['status']!='PASS':continue
            for name,h in r['outputs'].items():
                p=directory/name;require(not Path(name).is_absolute() and p.resolve().is_relative_to(directory.resolve()),'No product path escape')
                require(sha(p)==h,'Complete new producer output identity: '+name);ids[str(p)]=h
        require(all(ids[x['path']]==x['sha256'] for x in arrays_to_read.values()),'All candidate arrays sealed')
        write(OUT/'prediction_input_seal.json',dict(status='PASS_ALL4_TERMINAL_AND_ALL_NEW_PASS_OUTPUTS_BEFORE_GT',utc=utc(),input_sha256=ids,new_available_windows=list(arrays_to_read),
            old_arrays_read=False,GT_bytes_read_by_this_scorer=False,prior_GT_exposure='These sensor images were already scored in S32; this is not a new blind test'))
        for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
        import numpy as np
        require(np.__version__=='1.26.4','Existing scientific NumPy identity')
        helper=module(S32_HELPER,'s33_frozen_s32_missing_math');original=module(ORIGINAL,'s33_frozen_original_depth_math')
        arrays={};schemas={}
        for wid,item in arrays_to_read.items():
            raw=Path(item['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==item['sha256'],'Changed new array after seal')
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                require(z.files==['depth'],'Only the declared depth member');a=z['depth'].copy()
            require(a.shape==(4,384,512) and a.dtype==np.float32,'Complete4frameFP32 candidate')
            arrays[wid]=a;schemas[wid]=dict(shape=list(a.shape),dtype=str(a.dtype))
        write(OUT/'prediction_schema.json',schemas)
        require(len({f['path'] for f in gt_needed})==len(gt_needed),'Decode each prescribed available sensor once')
        receipt.update(sensor_GT_bytes_started=bool(gt_needed),sensor_GT_byte_start_utc=utc());write(OUT/'receipt.json',receipt)
        for f in gt_needed:require(sha(f['path'])==f['sha256'],'Same S32 sensor bytes');ids[f['path']]=f['sha256']
        write(OUT/'GT_byte_seal.json',dict(status='PASS',utc=utc(),GT_sha256={f['path']:f['sha256'] for f in gt_needed},GT_images_decoded=0))
        depths,records,gtids=original.load_sensor_depths(gt_needed)
        require(all(ids[p]==h for p,h in gtids.items()),'Loader decoded same presealed sensor files')
        gt={(f['window_id'],f['index']):d for f,d in zip(gt_needed,depths)}
        write(OUT/'GT_receipt.json',dict(utc=utc(),files=records,GT_images_decoded=len(depths),role='New candidate only; old48 never rescored; historical GT exposure acknowledged'))
        newrows=[];groups=copy.deepcopy(old['window_groups']);summaries=copy.deepcopy(old['endpoint_summaries'])
        for w in c['windows']:
            wid=w['id'];subset=[]
            for i in range(4):
                if w['availability']!='AVAILABLE':row=helper.empty_row(wid,NEW,i,w['reason'],'UNAVAILABLE_WINDOW')
                else:row=dict(window_id=wid,endpoint=NEW,index=i,row_status='SCORED',missing_reason=None,**original.depth_metrics(arrays[wid][i],gt[wid,i]))
                subset.append(row);newrows.append(row)
            groups[wid][NEW]=helper.aggregate_group(subset,original)
        summaries[NEW]=dict(all_four_prespecified=helper.window_summary([groups[w][NEW] for w in WINDOWS],WINDOWS),
            three_preselected_pose_eligible=helper.window_summary([groups[w][NEW] for w in eligible],eligible))
        rows=copy.deepcopy(oldrows)+newrows
        require(len(rows)==64 and {(r['window_id'],r['endpoint'],r['index']) for r in rows}=={(w,e,i) for w in WINDOWS for e in ENDS for i in range(4)},'Complete64 unique rows')
        require(rows[:48]==oldrows and all(groups[w][e]==old['window_groups'][w][e] for w in WINDOWS for e in OLD_ENDS) and all(summaries[e]==old['endpoint_summaries'][e] for e in OLD_ENDS),'Old row/group/summary values unchanged')
        csvreader=csv.DictReader(io.StringIO(csvraw.decode()));fields=csvreader.fieldnames
        require(len(list(csvreader))==48 and csvraw.endswith(b'\n'),'Original completeCSV line boundary')
        text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=fields,lineterminator='\r\n' if b'\r\n' in csvraw else '\n');writer.writerows(newrows)
        extra=text.getvalue().encode();(OUT/'new_candidate_per_frame.csv').write_bytes(csvraw.splitlines(keepends=True)[0]+extra)
        (OUT/'per_frame.csv').write_bytes(csvraw+extra)
        require((OUT/'per_frame.csv').read_bytes()[:len(csvraw)]==csvraw,'Old48CSV remains literal byte prefix')
        write(OUT/'new_candidate_metrics.json',dict(endpoint=NEW,per_frame=newrows,window_groups={w:groups[w][NEW] for w in WINDOWS},endpoint_summary=summaries[NEW]))
        write(OUT/'metrics.json',dict(scoring_manifest_sha256=expected_sha,selection_sha256=SELSHA,per_frame=rows,window_groups=groups,endpoint_summaries=summaries,
            prespecified_windows=4,pose_eligible_windows=3,prespecified_groups=16,prespecified_rows=64,imported_rows=48,new_rows=16,
            scored_rows=sum(r['row_status']=='SCORED' for r in rows),unavailable_rows=sum(r['row_status']!='SCORED' for r in rows),
            imported_source_sha256=FIXED,GT_scale_fit=False,confidence_mask=False,far_depth_cut=False,new_global_rescaling=False,
            evidence_scope='One ordinary constrained pair-scale control in previously scored short windows; no innovation/long-memory/video or independent-frame claim'))
        for p,h in ids.items():require(sha(p)==h,'Input changed during scoring')
        receipt.update(status='PASS',completed_utc=utc(),per_frame_rows=64,endpoint_groups=16,imported_S32_rows=48,new_candidate_rows=16,
            new_scored_rows=sum(r['row_status']=='SCORED' for r in newrows),new_NA_rows=sum(r['row_status']!='SCORED' for r in newrows),
            GT_images_decoded=len(depths),old_rows_groups_summaries_unchanged=True,old_CSV_literal_prefix=True,inputs_unchanged=True,input_sha256=ids,
            output_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='receipt.json'},
            status_meaning='Complete table constructed; producer failures stay NA and old48 are retained; not an improvement or novelty verdict')
        write(OUT/'receipt.json',receipt);print(json.dumps(dict(status='PASS_TABLE',rows=64,imported=48,new=16)))
    except BaseException as exc:
        receipt.update(status='FAILED',failed_utc=utc(),error=repr(exc),failure_policy='Keep output/attempt; identity or schema violations are not silently converted to scientificNA')
        write(OUT/'receipt.json',receipt);raise
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();run(Path(a.manifest).resolve(),a.sha256)
