#!/usr/bin/env python3
"""S32 timestamp-only selection and explicitly exposed oracle-pose metadata.
Never opens an image or prediction archive and never loads window scores.
"""
import ast
import bisect
from collections import defaultdict
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RULE_SHA='2f8339032ea0e0a5c36079e663c14764955e049b5599243667d72db79e186988'
SCENES={'fr2_desk':ROOT/'data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk',
        'fr1_xyz':ROOT/'data/tum/rgbd_dataset_freiburg1_xyz'}

def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(name,x):(HERE/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def require(ok,why):
    if not ok:raise ValueError(why)


def main():
    require(not (HERE/'selected_windows.json').exists() and not (HERE/'selection_receipt.json').exists(),'No repeat selection')
    require(sha(HERE/'selection_rule.md')==RULE_SHA,'Rule fixed before metadata reads')
    frozen=read(HERE/'rule_freeze_receipt.json');require(frozen['sha256']==RULE_SHA,'Fixed rule receipt')
    started=utc();write('selection_attempt.json',dict(started_utc=started,status='STARTED_METADATA_ONLY',rule_sha256=RULE_SHA))
    ids={str(HERE/'selection_rule.md'):RULE_SHA,str(HERE/'rule_freeze_receipt.json'):sha(HERE/'rule_freeze_receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
    metadata_reads=[]
    def metadata_json(rel):
        p=ROOT/rel;require(p.suffix=='.json','JSON metadata only');ids[str(p)]=sha(p);return read(p)
    def function(rel,name):
        p=ROOT/rel;ids[str(p)]=sha(p);nodes=[n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name]
        require(len(nodes)==1,'One source-defined association function');ns={'bisect':bisect}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p)+'::metadata_function','exec'),ns)
        return ns[name]
    def table(path,columns):
        require(path.name in ('rgb.txt','depth.txt','groundtruth.txt'),'Only named timestamp tables')
        raw=path.read_bytes();ids[str(path)]=hashlib.sha256(raw).hexdigest();rows=[]
        for lineno,line in enumerate(raw.decode().splitlines(),1):
            s=line.strip()
            if not s or s.startswith('#'):continue
            fields=s.split();require(len(fields)==columns,'Malformed timestamp table row')
            timestamp=float(fields[0]);require(math.isfinite(timestamp),'Finite timestamp')
            rows.append(dict(line=lineno,time=timestamp,time_string=fields[0],fields=fields[1:]))
        metadata_reads.append(dict(path=str(path),sha256=ids[str(path)],bytes=len(raw),rows=len(rows),role='allowed pose text' if columns==8 else 'timestamp/path text'))
        return rows
    try:
        pose_associate=function('work/S21_baseline_preparation/ttt3r_original/datasets_preprocess/long_prepare_tum.py','associate')
        depth_associate=function('scripts/s23_geometry_diagnostic.py','associate')
        m21=metadata_json('work/S21_baseline_preparation/run_manifest.json')
        m24=metadata_json('work/S24_baseline_expansion/run_manifest.json')
        prior_gt=metadata_json('results/S23_geometry_diagnostic/gt_receipt.json')
        known_depth={x['path']:x for x in prior_gt['files']}
        histories={}
        for scene,manifest,receipts in [
            ('fr2_desk',m21,['results/S21_baseline/cut3r/receipt.json','results/S21_baseline/ttt3r/receipt.json','results/S22_filt_shared_precision/filt3r/receipt.json']),
            ('fr1_xyz',m24,[f'results/S24_baseline_expansion/{m}/receipt.json' for m in ('cut3r','ttt3r','filt3r')])]:
            completed=[]
            for rel in receipts:
                r=metadata_json(rel);require(r['status']=='PASS' and r['frames_completed']==len(manifest['frames']),'Existing model execution must be complete')
                completed.append(dict(path=str(ROOT/rel),sha256=ids[str(ROOT/rel)],status=r['status'],frames_completed=r['frames_completed']))
            histories[scene]=dict(frames={x['path']:x for x in manifest['frames']},receipts=completed)
        windows=[];scene_records=[];selected_pose_rows_parsed=0
        for scene,base in SCENES.items():
            rgb=table(base/'rgb.txt',2);poses=table(base/'groundtruth.txt',8);depths=table(base/'depth.txt',2)
            rgb.sort(key=lambda r:(Decimal(r['time_string']),r['line']))
            n=len(rgb);require(n>=4,'N<4; cannot substitute a different scene')
            groups={}
            for key,data in [('rgb',rgb),('pose',poses),('depth',depths)]:
                bytime=defaultdict(list)
                for x in data:bytime[x['time']].append(x)
                groups[key]=bytime
            pm=dict(pose_associate(dict.fromkeys(groups['rgb']),dict.fromkeys(groups['pose']),0.,.02))
            dm=depth_associate(dict.fromkeys(groups['rgb']),dict.fromkeys(groups['depth']))
            old=m21 if scene=='fr2_desk' else m24
            require(ids[str(base/'groundtruth.txt')]==old['gt_sha256'],'Original historical groundtruth text identity')
            require(all(pm.get(f['rgb_time'])==f['gt_time'] for f in old['frames']),'Current global pose matching must reproduce checked historical mapping')
            if scene=='fr2_desk':
                for rec in prior_gt['files']:
                    f=m21['frames'][rec['index']]
                    require(dm.get(f['rgb_time'])==float(Path(rec['path']).stem),'Original sensor matching agrees with actual prior S23 read identities')
            scene_records.append(dict(scene=scene,source_directory=str(base),raw_rgb_count=n,groundtruth_row_count=len(poses),depth_row_count=len(depths),
                full_rgb_pose_pairs=len(pm),full_rgb_depth_pairs=len(dm),duplicate_timestamp_keys={k:sum(len(v)>1 for v in g.values()) for k,g in groups.items()},
                source_sha256={name:ids[str(base/name)] for name in ('rgb.txt','groundtruth.txt','depth.txt')},
                prior_model_input_count=len(histories[scene]['frames']),historical_execution_receipts=histories[scene]['receipts'],
                prior_sensor_depth_evidence='S23 actual depth-read receipt covers 278 fr2 paired images; individual matches shown per frame' if scene=='fr2_desk' else 'S24 scored full associated camera trajectory; this does NOT establish sensor depth PNG exposure',
                unreviewed_earlier_RGB_or_sensor_depth_exposure='UNKNOWN',human_RGB_viewing='UNKNOWN',
                groundtruth_pose_text_bytes_exposed_before_this_selection=True,scene_previously_used=True,blind_or_unseen_scene=False))
            used=set()
            for j in (1,2):
                start=j*(n-4)//3;indices=list(range(start,start+4));overlap=bool(used & set(indices));used.update(indices)
                frames=[];problems=['rule_windows_overlap'] if overlap else []
                for index,source_index in enumerate(indices):
                    rr=rgb[source_index];path=base/rr['fields'][0]
                    require(path.resolve().is_relative_to(base.resolve()),'RGB indexed path stays inside original scene')
                    ft=rr['time'];gt_time=pm.get(ft);dt_time=dm.get(ft);pose_rows=groups['pose'].get(gt_time,[]);dep_rows=groups['depth'].get(dt_time,[])
                    camera=dict(status='MISSING_ASSOCIATION' if gt_time is None else 'AMBIGUOUS_DUPLICATE_POSE' if len(pose_rows)!=1 else 'MATCHED',
                        source=str(base/'groundtruth.txt'),time=gt_time,time_string=pose_rows[0]['time_string'] if len(pose_rows)==1 else None,
                        source_line=pose_rows[0]['line'] if len(pose_rows)==1 else None,allowed_oracle_control=True,
                        coordinate_convention='TUM optical c2w in absolute metric world; no additional Y/Z flip',c2w_tensor_generated=False)
                    if len(pose_rows)==1:
                        pp=pose_rows[0];values=[float(x) for x in pp['fields']];selected_pose_rows_parsed+=1
                        norm=math.sqrt(math.fsum(v*v for v in values[3:]));valid=all(math.isfinite(v) for v in values) and abs(norm-1)<1e-3
                        camera.update(translation_m=values[:3],quaternion_xyzw=values[3:],quaternion_norm=norm,coordinates_parsed_now=True,
                            signed_dt_seconds_float=gt_time-ft,absolute_dt_seconds_decimal=str(abs(Decimal(pp['time_string'])-Decimal(rr['time_string']))),valid_pose_metadata=valid)
                        if not valid:camera['status']='INVALID_POSE_METADATA'
                    else:camera.update(coordinates_parsed_now=False,valid_pose_metadata=False)
                    depth_path=str(base/dep_rows[0]['fields'][0]) if len(dep_rows)==1 else None
                    sensor=dict(status='MISSING_ASSOCIATION' if dt_time is None else 'AMBIGUOUS_DUPLICATE_DEPTH' if len(dep_rows)!=1 else 'MATCHED',
                        source_index_file=str(base/'depth.txt'),time=dt_time,time_string=dep_rows[0]['time_string'] if len(dep_rows)==1 else None,
                        source_line=dep_rows[0]['line'] if len(dep_rows)==1 else None,path=depth_path,sha256=None,
                        byte_identity_status='PENDING_LATER_BYTE_SEAL',file_exists=Path(depth_path).is_file() if depth_path else False,
                        absolute_dt_seconds_decimal=str(abs(Decimal(dep_rows[0]['time_string'])-Decimal(rr['time_string']))) if len(dep_rows)==1 else None,
                        role='scoring-only sensor depth; no current PNG bytes read or coverage inspection')
                    historical=histories[scene]['frames'].get(str(path));known=known_depth.get(depth_path)
                    exposure=dict(scene_previously_used=True,RGB_bytes_read_by_this_selection=False,RGB_pixels_decoded_by_this_selection=False,
                        prior_RGB_model_inference_in_checked_stage=bool(historical),prior_model_frame_index=historical['index'] if historical else None,
                        checked_stage='S21/S22 associated first300' if scene=='fr2_desk' else 'S24 full796 pose-associated sequence',
                        prior_RGB_human_display='UNKNOWN',other_prior_RGB_inference_or_read='UNKNOWN',
                        prior_sensor_depth_PNG_read_proven_in_S23=bool(known),prior_S23_sensor_row_index=known['index'] if known else None,
                        overall_sensor_depth_PNG_exposure='KNOWN_PRIOR_READ' if known else 'UNKNOWN_OUTSIDE_CHECKED_S23_RECEIPT',
                        prior_camera_trajectory_scoring_in_checked_stage=bool(historical),
                        prior_window_specific_depth_scores_viewed='UNKNOWN_FOR_OTHER_PROTOCOLS; S32 not run',
                        S32_scores_used_for_selection=False,prior_optical_pose_text_byte_exposure=True,
                        this_selection_pose_text_bytes_read=True,this_selection_selected_pose_coordinates_parsed=camera['coordinates_parsed_now'],
                        sensor_depth_bytes_read_by_this_selection=False,prediction_NPZ_bytes_read_by_this_selection=False,blind_test_claim=False)
                    reasons=[]
                    if not path.is_file():reasons.append('RGB_FILE_MISSING')
                    if len(groups['rgb'][ft])!=1:reasons.append('DUPLICATE_RGB_TIMESTAMP')
                    if not camera['valid_pose_metadata']:reasons.append(camera['status'])
                    problems.extend(f'frame{index}:{x}' for x in reasons)
                    frames.append(dict(index=index,source_rgb_index=source_index,path=str(path),sha256=None,
                        RGB_byte_identity_status='PENDING_LATER_BYTE_SEAL',rgb_time=ft,rgb_time_string=rr['time_string'],rgb_index_source_line=rr['line'],
                        gt_time=gt_time,pose_association=camera,sensor_depth_association=sensor,exposure=exposure,required_input_issues=reasons))
                windows.append(dict(id=f'{scene}_j{j}',scene=scene,j=j,total_original_RGB=n,start_index=start,source_RGB_indices=indices,
                    formula='floor(j*(N-4)/3)',status='METADATA_ELIGIBLE_CONTENT_NOT_FROZEN' if not problems else 'FIXED_WINDOW_BLOCKED_NO_REPLACEMENT',
                    required_input_issues=problems,frames=frames,sensor_depth_matched_frames=sum(f['sensor_depth_association']['status']=='MATCHED' for f in frames),
                    elapsed_scene_start_seconds=str(Decimal(frames[0]['rgb_time_string'])-Decimal(rgb[0]['time_string'])),
                    RGB_span_seconds=str(Decimal(frames[-1]['rgb_time_string'])-Decimal(frames[0]['rgb_time_string'])),
                    given_pose_condition=dict(source=str(base/'groundtruth.txt'),expected_sha256=ids[str(base/'groundtruth.txt')],role='Shared optical GT-c2w oracle control; not pure RGB or blind camera estimation',coordinates='TUM optical c2w, no flip',selected_pose_coordinates_parsed_now=True),
                    future_execution=dict(consumer_stage='initial four-frame consumer only; no old4-to-new4 chain',fresh_independent_CUT3R_reset=True,reuse_full_sequence_other_heads=False,
                        reset_semantics='Fresh state at each window entry/i=0; keep original per-frame recurrence, not reset=True on every frame',
                        predictor=dict(model='existing CUT3R512DPT',cpu_threads=8,outer_dtype='float32',max_seconds=180,max_rss_bytes=16*1024**3),
                        GA=dict(max_seconds=120,max_rss_bytes=4*1024**3),execution_started=False)))
        for path,value in ids.items():require(sha(path)==value,'Metadata or selection source changed')
        payload=dict(schema='s32-four-predetermined-consumer-windows-metadata-v1',status='SELECTED_METADATA_ONLY_NOT_EXPERIMENT_FROZEN',
            selection_started_utc=started,completed_utc=utc(),rule_fixed_utc=frozen['fixed_utc'],selection_rule_sha256=RULE_SHA,
            windows=windows,scene_historiography=scene_records,metadata_files=metadata_reads,source_and_metadata_sha256=ids,
            actual_access=dict(RGB_image_bytes=0,RGB_pixel_decodes=0,sensor_depth_PNG_bytes=0,prediction_NPZ_bytes=0,new_window_scores=0,
                full_groundtruth_text_files_read=2,selected_GT_pose_numeric_rows_parsed=selected_pose_rows_parsed,model_runs=0,GA_runs=0),
            limitations=['Selection is new, scenes and some exact RGB are historically exposed','Unknown exposure remains unknown, not unseen','RGB/depth content SHA is pending actual later byte sealing','Sensor pairing/absence does not cause window replacement','Source/weight/compute protocol requires a later explicit freeze'])
        write('selected_windows.json',payload)
        write('selection_receipt.json',dict(status='PASS_METADATA_SELECTION_ONLY',started_utc=started,completed_utc=utc(),rule_sha256=RULE_SHA,
            script_sha256=sha(__file__),selected_windows_sha256=sha(HERE/'selected_windows.json'),window_count=len(windows),frame_count=sum(len(w['frames']) for w in windows),
            blocked_windows=[w['id'] for w in windows if w['required_input_issues']],actual_access=payload['actual_access'],metadata_unchanged=True))
        print(json.dumps(dict(status='SELECTED_METADATA_ONLY',windows=[dict(id=w['id'],N=w['total_original_RGB'],start=w['start_index'],status=w['status'],sensor_pairs=w['sensor_depth_matched_frames']) for w in windows],sha256=sha(HERE/'selected_windows.json')),ensure_ascii=False))
    except BaseException as exc:
        write('selection_receipt.json',dict(status='FAILED_METADATA_SELECTION',started_utc=started,failed_utc=utc(),error=repr(exc),policy='Preserve fixed rule and attempt; no automatic replacement/reselection'));raise

if __name__=='__main__':main()
