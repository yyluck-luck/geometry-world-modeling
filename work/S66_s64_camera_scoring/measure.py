"""Three explicit saved-data modes; no model, image display or automatic chaining."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S64 = ROOT/'work/S64_unit_repaired_generation'
ARCHIVE = ROOT/'results/S64_unit_repaired_generation/archive'
AUTHOR = '/root/c2_v9_recovery_author'
ROW = 'C2_UNIT_REPAIRED_S64'
SOURCE_PINS = {
 'camera': ('work/S45B_c1_numeric_camera_guard_supervised_v12/camera_guard.py', '02114d4a845bd83e3dcd35f663bf64f2a75eb5fb17fc0f3515b84222bd51281f'),
 'score': ('work/S46_c1_blind_scoring_preparation/score_c1_blind_candidate.py', 'ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a'),
 'recompute': ('work/S46_c1_blind_scoring_preparation/recompute_c1_independent_candidate.py', '9373fd035b18ccc81dc848e18612f906a7d32a44cd1c7d2903eb67b7627e9b8f'),
 'compare': ('work/S46_c1_blind_scoring_preparation/C1_independent_recompute/recompute_c1_io.py', '37b5f837b1c2b7645cc4420a9d498a57bf070668936c5c3eb84147094ba4aaeb'),
}
UPSTREAM = {
 'manifest': ('work/S64_unit_repaired_generation/review_attachment_01/manifest.json', '34c2bad90c5627b6e9742fe65f8c8b4a1ff76da730a2c0d87bbcedcc38b28619'),
 'external': ('work/S64_unit_repaired_generation/external_launch_01/receipt.json', '8ebe2376785626c538831201486ea3d9773df94ebab462dfa725f1d2ad948e2c'),
 'commit': ('work/S64_unit_repaired_generation/execution_01/supervisor_terminal_commit.json', 'ebb1f0b3d7c311c5eb8cf9bb6dea37db194c5255477841477a4aec03565e1f55'),
 'postrun_report': ('work/S64_unit_repaired_generation/postrun_readback_01/report.json', 'd8a11b534eeb18e21aa60437e5e7a7840cde74aaa082c38948b444f976b113bd'),
 'postrun_receipt': ('work/S64_unit_repaired_generation/postrun_readback_01/receipt.json', '6add3464246a19b1337781db41d827d860c6d50cef25c6175a53d22ebc46c9cb'),
 'postrun_review': ('work/S64_unit_repaired_generation/INDEPENDENT_POSTRUN_RESULT_REVIEW.json', 'c5a60a522eea8ecf27b75908c72f7f66717a08ed91b6a011ee2bf88383fcf562'),
 'archive': ('results/S64_unit_repaired_generation/archive/manifest.json', 'ccf60d157109fa079f8ea9a0c65533fe861059f97f2a8980495f6c401e256666'),
 'events': ('results/S64_unit_repaired_generation/archive/events.jsonl', 'faa613e20d95af78ac5edcf16bd522aa4068b987c011b4b50dd0798b08ea07d0'),
}
CAMERA_NAMES = {'GuardInvalid','TensorDescriptor','require','require_guard','canonical',
 'stat_identity','file_snapshot','file_record','read_json','decode_scalar','raw_dict_fields',
 'raw_tensor','raw_tensor_list','select_camera_capture','selected_event_captures',
 'flatten','nested_shape','reshape','CameraTensorStore','matrix_max_abs','expected_pose',
 'evaluate_numeric_guard','decode_selected_cameras'}
CAMERA_CONSTANTS = {'EXPECTED_YAW','TOLERANCE','MAX_CAMERA_TENSOR_BYTES','WIDTHS','HEX'}
READS = []
PAYLOAD_ATTEMPTS = []
DEADLINE = float('inf')

def utc(): return datetime.now(timezone.utc).isoformat()
def require(ok, message):
    if not ok: raise ValueError(message)
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def write_new(path, obj):
    with path.open('x') as f: json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def source_bytes(key):
    rel, expected = SOURCE_PINS[key]; path = ROOT/rel
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    require((before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
            == (after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
            and hashlib.sha256(raw).hexdigest() == expected, 'Frozen source changed: '+rel)
    READS.append(dict(path=str(path),sha256=expected,bytes=len(raw),content_kind='source'))
    return path, raw

def load_camera():
    path, raw = source_bytes('camera'); tree = ast.parse(raw,filename=str(path))
    selected = [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in CAMERA_NAMES
                or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in CAMERA_CONSTANTS for t in n.targets)]
    require(len(selected)==len(CAMERA_NAMES)+len(CAMERA_CONSTANTS), 'Camera extraction coverage differs')
    namespace = dict(globals())
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path)+'[S66 pure definitions]','exec'),namespace)
    original_snapshot = namespace['file_snapshot']
    def logged_snapshot(path, expected_sha256=None, deadline=None, max_bytes=None):
        raw, item = original_snapshot(path,expected_sha256,DEADLINE,max_bytes)
        READS.append(dict(item,content_kind='metadata'))
        return raw,item
    namespace['file_snapshot'] = logged_snapshot
    return namespace

def load_kernel(key, ns):
    path, raw = source_bytes(key)
    if key == 'compare':
        tree=ast.parse(raw,filename=str(path))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compare_math')
        code=compile(ast.Module(body=[node],type_ignores=[]),str(path)+'[compare_math]','exec')
    else:
        code=compile(raw,str(path),'exec')
    namespace=dict(globals(),__name__='_s66_'+key,__file__=str(path))
    exec(code,namespace)
    return namespace

def doc(ns,path,sha):
    value,_=ns['read_json'](Path(path),sha,str(path),DEADLINE)
    return value

def upstream(ns):
    docs={key:doc(ns,ROOT/rel,sha) for key,(rel,sha) in UPSTREAM.items() if key!='events'}
    m=docs['manifest']; variant=m['retrieval_variant']
    require(m['row']==ROW and variant['id']=='s64_positive_camera_depth_median_units_v1'
            and variant['eligible_for_original_cohort'] is False
            and m['variant']['repo']=='stabilityai/sd-vae-ft-mse','Wrong S64 scientific identity')
    require(docs['external']['returncode']==0 and docs['external']['external_timeout'] is False
            and docs['commit']['outcome_status']=='RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and docs['commit']['retrieval_unit_binding']['complete'] is True,'Actual S64 terminal incomplete')
    require(docs['postrun_receipt']['status']=='PASS_S64_ENGINEERING_READBACK_ONLY'
            and docs['postrun_receipt']['report_sha256']==UPSTREAM['postrun_report'][1]
            and docs['postrun_review']['status']=='PASS_S64_BOUNDED_ENGINEERING_READBACK_RESULT'
            and not docs['postrun_review']['blockers'],'Actual independently reviewed readback required')
    require(docs['postrun_report']['row']==ROW and docs['postrun_report']['retrieval_variant']==variant
            and docs['commit']['manifest_sha256']==UPSTREAM['manifest'][1]
            and docs['commit']['row']==ROW and docs['commit']['retrieval_variant']==variant
            and docs['archive']['status']=='ARCHIVE_COMPLETE'
            and docs['archive']['caller_manifest_sha256']==UPSTREAM['manifest'][1]
            and docs['archive']['source_identities']==m['source_identities'], 'Archive/variant mismatch')
    return docs

def nine_identities(ns, archive):
    raw,_=ns['file_snapshot'](ARCHIVE/'events.jsonl',UPSTREAM['events'][1],DEADLINE)
    matches=[r for line in raw.splitlines() for r in [json.loads(line)]
             if r['event']=='capture_complete' and r['payload']['name']=='cache_commit'
             and r['payload']['occurrence']==1]
    require(len(matches)==1,'Final authoritative cache occurrence missing')
    top=ns['raw_dict_fields'](matches[0]['payload']['tree'],'final cache')
    cache=ns['raw_dict_fields'](top['cache'],'cache'); frames=cache['pil_frames']
    require(frames['kind'] in ('list','tuple') and len(frames['items'])==9,'Nine authoritative frames required')
    identities=[]
    for i,image in enumerate(frames['items']):
        require(image['kind']=='pil_image','Frame is not archival PIL pixels')
        desc=image['pixels']; validate_pixel_descriptor(desc,archive)
        identities.append(dict(id=i,blob=str(ARCHIVE/desc['blob']),
                               tensor_descriptor_sha256=desc['sha256'],tensor_body_sha256=desc['bytes_sha256']))
    return identities

def validate_pixel_descriptor(desc,archive):
    require(desc['kind']=='tensor' and desc['dtype']=='uint8' and desc['shape']==[576,576,3]
            and desc['order']=='C' and desc['byteorder']=='little' and desc['nbytes']==995328,
            'Wrong authoritative pixel dtype/shape/codec')
    require(desc['blob']=='tensors/'+desc['sha256']+'.bin'
            and archive['tensor_descriptors'][desc['blob']]==desc
            and archive['files'][desc['blob']]==dict(bytes=desc['nbytes'],sha256=desc['bytes_sha256']),
            'Pixel descriptor/manifest identity differs')

def camera(ns,docs,record):
    captures,chain=ns['selected_event_captures'](ARCHIVE/'events.jsonl',docs['archive'],UPSTREAM['events'][1],DEADLINE)
    ids=nine_identities(ns,docs['archive'])
    original_store=ns['CameraTensorStore']
    class TrackedStore(original_store):
        def _snapshot(self,desc,body_item,side_item,side_raw,label):
            PAYLOAD_ATTEMPTS.append(dict(path=str(ARCHIVE/desc['blob']),expected_bytes=desc['nbytes'],
                                         expected_sha256=desc['bytes_sha256'],content_kind='camera_body'))
            return super()._snapshot(desc,body_item,side_item,side_raw,label)
    store=TrackedStore(docs['archive'],ARCHIVE,DEADLINE)
    saved={}; completed=False
    try:
        batches,commits=ns['decode_selected_cameras'](captures,store)
        math_result=ns['evaluate_numeric_guard'](batches,commits)
        saved=store.identities();store.close(True);completed=True
    finally:
        if not saved: saved=store.identities()
        record.update(camera_body_readlist=saved,camera_body_opened_count=store.body_opened_count,
                      camera_initial_body_bytes_read=store.body_bytes_read,
                      camera_close_verified_count=store.close_verified_count,
                      camera_close_verified_body_bytes=sum(v['nbytes'] for v in saved.values()) if completed else None)
        if not completed:store.close(False)
    # Old row/status are kernel compatibility labels only, never S64 conclusions.
    legacy=('row','status','pixel_score','visual_quality','rendered_pixel_camera_obedience','method_gain','novelty')
    math_result={k:v for k,v in math_result.items() if k not in legacy}
    return dict(requested_pose_K_guard_pass=True,camera_numeric=math_result,
                authoritative_pixel_identities=ids,archive_event_chain=chain,
                scope='Saved requested-camera inputs only; not rendered-image camera obedience')

def camera_result(ns,args):
    require(args.camera_review and args.camera_review_sha256,'Score requires actual different-author camera result review')
    review=doc(ns,args.camera_review,args.camera_review_sha256)
    require(review['schema']=='s66-camera-independent-result-review-v1'
            and review['status']=='PASS_S66_CAMERA_INDEPENDENT_RESULT_REVIEW' and review['row']==ROW
            and review['reviewer_role']!=AUTHOR and review['reviewer_role']
            and review['observed_returncode']==0 and review['source_sha256']==args.source_sha256
            and not review['blockers'],'Camera result review is not applicable')
    require(Path(review['camera_receipt']['path'])==HERE/'camera_01/receipt.json'
            and Path(review['camera_report']['path'])==HERE/'camera_01/report.json','Wrong camera result paths')
    receipt=doc(ns,review['camera_receipt']['path'],review['camera_receipt']['sha256'])
    report=doc(ns,review['camera_report']['path'],review['camera_report']['sha256'])
    require(receipt['passed'] and receipt['status']=='PASS_S66_CAMERA_ONLY'
            and receipt['report_sha256']==review['camera_report']['sha256']
            and receipt['source_sha256']==args.source_sha256 and report['row']==ROW
            and report['manifest_sha256']==UPSTREAM['manifest'][1]
            and report['requested_pose_K_guard_pass'] is True
            and report['authoritative_pixel_identities']==review['authoritative_pixel_identities'], 'Camera result binding differs')
    return report['authoritative_pixel_identities'],dict(path=str(Path(args.camera_review)),sha256=args.camera_review_sha256)

def frames(ns,identities,archive,record):
    import numpy as np
    require(np.__version__=='1.26.4','Use the existing NumPy 1.26.4 environment')
    require(type(identities) is list and len(identities)==9,'Nine IDs required')
    result=[]; snapshots=[]
    for i,item in enumerate(identities):
        require(set(item)=={'id','blob','tensor_descriptor_sha256','tensor_body_sha256'}
                and type(item['id']) is int and item['id']==i,'Authoritative IDs differ')
        path=Path(item['blob']);relative='tensors/'+item['tensor_descriptor_sha256']+'.bin'
        require(path==ARCHIVE/relative,'Authoritative pixel path differs')
        desc=archive['tensor_descriptors'][relative];validate_pixel_descriptor(desc,archive)
        require(desc['bytes_sha256']==item['tensor_body_sha256'],'Pixel body declaration differs')
        PAYLOAD_ATTEMPTS.append(dict(path=str(path),expected_bytes=995328,
                                     expected_sha256=item['tensor_body_sha256'],content_kind='RGB_body'))
        raw,read=ns['file_snapshot'](path,item['tensor_body_sha256'],DEADLINE,995328)
        READS[-1]['content_kind']='RGB_body'
        base={k:v for k,v in desc.items() if k not in ('blob','sha256')}
        require(len(raw)==995328 and hashlib.sha256(canonical(base)+b'\0'+raw).hexdigest()==desc['sha256'],
                'Actual pixel descriptor/body SHA differs')
        pixels=np.frombuffer(raw,dtype=np.uint8).reshape(576,576,3)
        require(not pixels.flags.writeable,'Score input must be immutable snapshot')
        result.append(pixels);snapshots.append(read)
    record.update(pixel_body_snapshots=snapshots,pixel_body_snapshot_bytes=sum(x['bytes'] for x in snapshots),
                  pixel_body_count=len(snapshots),numpy_version=np.__version__)
    return result,np

MATH_FIELDS=('primary','per_region_diagnostic','full_frame_diagnostic','generated_only_pair_diagnostic_no_GT',
             'event_MSE_gt_0_01','equality_is_not_event')

def score(ns,docs,args,record):
    ids,review=camera_result(ns,args)
    pixels,np=frames(ns,ids,docs['archive'],record)
    kernel=load_kernel('score',ns);raw=kernel['score_frames'](pixels,np)
    return dict(math={k:raw[k] for k in MATH_FIELDS},primary_pair=[0,8],
                authoritative_pixel_identities=ids,camera_result_review=review,
                scoring_math_sha256=kernel['FROZEN_MATH_SHA256'],scorer_source_sha256=SOURCE_PINS['score'][1])

def recompute(ns,docs,args,record):
    require(args.score_receipt_sha256 and args.score_report_sha256,'Recompute needs sealed primary receipt/report SHA')
    receipt=doc(ns,HERE/'score_01/receipt.json',args.score_receipt_sha256)
    primary=doc(ns,HERE/'score_01/report.json',args.score_report_sha256)
    require(receipt['status']=='PASS_S66_SCORE_ONLY' and receipt['passed']
            and receipt['report_sha256']==args.score_report_sha256 and receipt['source_sha256']==args.source_sha256
            and primary['row']==ROW and primary['scorer_source_sha256']==SOURCE_PINS['score'][1],
            'Primary score is not this sealed successful result')
    ids=primary['authoritative_pixel_identities'];pixels,np=frames(ns,ids,docs['archive'],record)
    kernel=load_kernel('recompute',ns);raw=kernel['recompute_frames'](pixels,np)
    compare=load_kernel('compare',ns)['compare_math']
    # Reconstruct only the old comparator's deterministic compatibility label.
    # It is compared internally and is not emitted as a C1/S64 cohort result.
    expected=dict(primary['math'],row_status=('C1_TECHNICALLY_VALID_SEVERE_DISCREPANCY_EVENT'
                  if primary['math']['event_MSE_gt_0_01'] else 'C1_TECHNICALLY_VALID_NO_SEVERE_DISCREPANCY_EVENT'))
    mismatches=compare(raw,expected)
    return dict(math={k:raw[k] for k in MATH_FIELDS},authoritative_pixel_identities=ids,
                sealed_score_report_sha256=args.score_report_sha256,
                independent_kernel_sha256=SOURCE_PINS['recompute'][1],exact_match=not mismatches,mismatches=mismatches)

def compile_only():
    ns=load_camera()
    for key in ('score','recompute','compare'):load_kernel(key,ns)
    require(not any(x in sys.modules for x in ('numpy','torch','PIL','cv2','diffusers')),'Unexpected scientific import')
    return dict(status='PASS_SOURCE_COMPILE_ONLY',camera_definitions_unchanged=True,
                score_kernel_unchanged=True,independent_kernel_unchanged=True,
                compare_math_unchanged=True,scientific_payload_bytes_read=0)

def main():
    global DEADLINE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile-only',action='store_true')
    parser.add_argument('--mode',choices=('camera','score','recompute'))
    for name in ('source-sha256','camera-review','camera-review-sha256','score-receipt-sha256','score-report-sha256'):
        parser.add_argument('--'+name)
    args=parser.parse_args()
    if args.compile_only:print(json.dumps(compile_only(),indent=2));return 0
    require(args.mode and args.source_sha256,'Explicit mode and reviewed source SHA required')
    actual=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    require(actual==args.source_sha256,'Execution source SHA differs')
    output=HERE/(args.mode+'_01');output.mkdir(exist_ok=False)
    start=time.monotonic();DEADLINE=start+110
    record=dict(schema='s66-mode-receipt-v1',row=ROW,mode=args.mode,source_sha256=actual,
                started_utc=utc(),status='CHECKING',passed=False,model_calls=0,image_display_count=0)
    try:
        ns=load_camera();docs=upstream(ns)
        result={'camera':lambda:camera(ns,docs,record),'score':lambda:score(ns,docs,args,record),
                'recompute':lambda:recompute(ns,docs,args,record)}[args.mode]()
        report=dict(schema='s66-mode-report-v1',row=ROW,mode=args.mode,
                    manifest_sha256=UPSTREAM['manifest'][1],retrieval_variant=docs['manifest']['retrieval_variant'],
                    eligible_for_original_cohort=False,new_method_validated=False,
                    image_display_count=0,visual_quality='NOT_EVALUATED',
                    interpretation='Exploratory engineering variant; old C2 failure/cohort unchanged',**result)
        for item in READS:
            if 'stat' in item:
                require(list(ns['stat_identity'](Path(item['path']).stat()))==item['stat'],'Read input changed before seal')
        require(time.monotonic()<=DEADLINE,'110-second mode budget exceeded')
        write_new(output/'report.json',report)
        passed=args.mode!='recompute' or result['exact_match']
        record.update(passed=passed,status=('PASS_S66_'+args.mode.upper()+'_ONLY') if passed else 'MISMATCH_S66_RECOMPUTE',
                      report_sha256=hashlib.sha256((output/'report.json').read_bytes()).hexdigest())
    except BaseException as error:
        record.update(status='FAILED_S66_'+args.mode.upper(),error_type=type(error).__name__,
                      error=str(error),traceback=traceback.format_exc())
    finally:
        record.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start,readlist=READS,
                      payload_attempts=PAYLOAD_ATTEMPTS,eligible_for_original_cohort=False,new_method_validated=False,
                      read_scope='Readlist includes successful complete snapshots; payload_attempts also marks attempted bodies. Camera initial bytes and successful close verification are separate; failed reads may be partial.',
                      prior_RGB_access='S64 postrun already read RGB for identity/consumption; no assertion of unread pixels or restored cohort blindness')
        write_new(output/'receipt.json',record)
    return 0 if record['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
