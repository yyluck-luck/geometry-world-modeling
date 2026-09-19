#!/usr/bin/env python3
"""Audit S8 sampling before RGB QA, using timestamp-only independent math."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import traceback
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_s8_results import sampling_from_timestamps,safe_under,valid_sha

AUDIT_SHA='6ae1ee6fa5373a378cacb53babb1475a12b669419d8ebe96529aab079ba72878'


def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def timestamp_rows(path,columns):
    values=[]
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        parts=line.split()
        if len(parts)!=columns:raise ValueError('Unexpected timestamp row width')
        t=float(parts[0])
        if not math.isfinite(t):raise ValueError('Nonfinite timestamp')
        # GT pose tokens deliberately remain unparsed.
        values.append((t,parts[1]) if columns==2 else (t,))
    values.sort()
    if not values or any(b[0]<=a[0] for a,b in zip(values,values[1:])):
        raise ValueError('Empty or duplicate timestamp table')
    return values


def run(args):
    if args.output.exists() or args.output.is_symlink():raise ValueError('Use a fresh audit directory')
    args.output.mkdir(parents=True)
    meta=dict(status='running',started_utc=now(),image_pixels_read=False,gt_pose_values_parsed=False,checks=[])
    def check(name,condition):
        meta['checks'].append(dict(name=name,passed=bool(condition)))
        if not condition:raise AssertionError(name)
    try:
        tracked_paths=[args.design_freeze,args.manifest,args.protocol,args.sampling,
            args.data/'rgb.txt',args.data/'depth.txt',args.data/'groundtruth.txt',
            Path(__file__),ROOT/'scripts/verify_s8_results.py',ROOT/'scripts/verify_s6_scores.py',ROOT/'scripts/verify_s7_replay.py']
        tracked={str(p.resolve()):sha(p) for p in tracked_paths}
        design=read(args.design_freeze);manifest=read(args.manifest);sampling=read(args.sampling)
        check('fixed_independent_sampling_math',sha(ROOT/'scripts/verify_s8_results.py')==AUDIT_SHA)
        check('protocol_matches_design',sha(args.protocol)==design['protocol_sha256']==manifest['protocol_sha256'])
        for name,digest in design['source_sha256'].items():
            check('design_source/'+name,sha(ROOT/name)==digest)
            tracked[str((ROOT/name).resolve())]=digest
        check('sampling_completed',sampling['status']=='completed')
        check('sampling_scope_metadata',sampling['images_decoded'] is False and sampling['gt_pose_values_parsed'] is False)
        check('sampling_protocol_sha',sampling['protocol_sha256']==design['protocol_sha256'])
        check('sampling_source_sha',sampling['preparation_source_sha256']==design['source_sha256']['scripts/prepare_s8_inputs.py'])
        check('sampling_manifest_sha',sha(args.manifest)==sampling['manifest_sha256'])
        check('manifest_schema_runner',manifest['schema']=='s8-inputs-v1' and manifest['runner_sha256']=='cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292')
        check('archive_hash_cross_record_consistency',valid_sha(manifest['archive_sha256']) and manifest['archive_sha256']==sampling['archive_sha256'])
        check('manifest_dataset',manifest['dataset']=='rgbd_dataset_freiburg2_desk')
        check('block_integer_ids',all(type(b['block']) is int and type(b['accepted_window_index']) is int for b in manifest['blocks']))
        check('block_ids_splits',[(b['block'],b['split']) for b in manifest['blocks']]==[(0,'test'),(1,'test'),(2,'test')])
        for name in ('rgb.txt','depth.txt','groundtruth.txt'):
            actual=sha(safe_under(args.data,name))
            check('text_hash/'+name,actual==manifest['text_file_sha256'][name]==sampling['text_file_sha256'][name])
        rgb=timestamp_rows(args.data/'rgb.txt',2);depth=timestamp_rows(args.data/'depth.txt',2)
        gt_timestamps=np.asarray(timestamp_rows(args.data/'groundtruth.txt',8),dtype=np.float64)
        check('metadata_table_counts',sampling['rgb_count']==len(rgb) and sampling['depth_count']==len(depth) and sampling['gt_timestamp_count']==len(gt_timestamps))
        check('metadata_selected_counts',type(sampling['selected_rgb_frames']) is int and sampling['selected_rgb_frames']==72 and type(sampling['selected_depth_files']) is int and sampling['selected_depth_files']==72)
        accepted,chosen,pair_count=sampling_from_timestamps(rgb,depth,gt_timestamps)
        check('complete_pair_count',pair_count==sampling['paired_count'])
        check('all_accepted_windows_count',len(accepted)==len(sampling['plan']['accepted_windows']))
        check('first_middle_last_indices',chosen==sampling['plan']['selected_window_indices'])
        for i,(a,b) in enumerate(zip(accepted,sampling['plan']['accepted_windows'])):
            check(f'window{i}/index',type(b['index']) is int and b['index']==i)
            check(f'window{i}/time',a['nominal_start']==b['nominal_start'] and a['nominal_end']==b['nominal_end'])
            check(f'window{i}/matches',all(type(v) is int for v in b['match_indices']) and [r[0] for r in a['rows']]==b['match_indices'])
            check(f'window{i}/rgb_timestamps',[r[1][0] for r in a['rows']]==b['rgb_timestamps'])
            check(f'window{i}/targets',a['target_timestamps']==b['target_timestamps'])
            check(f'window{i}/snap_errors',a['snap_errors']==b['snap_errors_seconds'])
        seen={k:{'paths':set(),'inodes':set(),'hashes':set(),'timestamps':set()} for k in ('rgb','depth')}
        for b,wi in zip(manifest['blocks'],chosen):
            check(f'block{b["block"]}/window',b['accepted_window_index']==wi)
            check(f'block{b["block"]}/count',len(b['frames'])==24)
            window=accepted[wi];stamps=[r[1][0] for r in window['rows']]
            check(f'block{b["block"]}/nominal_times',b['nominal_start']==window['nominal_start'] and b['nominal_end']==window['nominal_end'])
            check(f'block{b["block"]}/actual_duration',b['actual_duration_seconds']==stamps[-1]-stamps[0])
            check(f'block{b["block"]}/rgb_intervals',b['rgb_intervals_seconds']==[y-x for x,y in zip(stamps,stamps[1:])])
            check(f'block{b["block"]}/sensor_offsets',b['rgb_minus_depth_seconds']==[r[1][0]-r[2][0] for r in window['rows']])
            for fi,(f,row) in enumerate(zip(b['frames'],accepted[wi]['rows'])):
                check(f'B{b["block"]}F{fi}/integer_fields',type(f['frame']) is int and type(f['match_index']) is int)
                check(f'B{b["block"]}F{fi}/index',f['frame']==fi and f['match_index']==row[0])
                check(f'B{b["block"]}F{fi}/target',f['target_timestamp']==window['target_timestamps'][fi])
                check(f'B{b["block"]}F{fi}/snap_error',f['snap_error_seconds']==window['snap_errors'][fi])
                for kind,expected in zip(('rgb','depth'),row[1:]):
                    label=f'B{b["block"]}F{fi}/{kind}'
                    check(label+'/timestamp_type',type(f[kind]['timestamp']) in (int,float))
                    check(label+'/timestamp_path',f[kind]==dict(timestamp=expected[0],path=expected[1]))
                    path=safe_under(args.data,f[kind]['path']);digest=sha(path);stat=path.stat()
                    tracked[str(path)]=digest
                    check(label+'/sha',digest==f[kind+'_sha256'])
                    identities=dict(paths=str(path),inodes=(stat.st_dev,stat.st_ino),hashes=digest,timestamps=expected[0])
                    for key,v in identities.items():
                        check(label+'/unique_'+key,v not in seen[kind][key]);seen[kind][key].add(v)
        check('rgb_depth_distinct_files',not seen['rgb']['paths']&seen['depth']['paths'] and not seen['rgb']['inodes']&seen['depth']['inodes'])
        for path,digest in tracked.items():check('source_unchanged/'+path,sha(path)==digest)
        meta.update(status='passed',manifest_sha256=sha(args.manifest),protocol_sha256=sha(args.protocol),
            independent_window_count=len(accepted),selected_window_indices=chosen,
            selected_rgb_images=72,selected_depth_files=72,independent_pair_count=pair_count,
            source_sha256={n:sha(ROOT/n) for n in ('scripts/verify_s8_sampling.py','scripts/verify_s8_results.py',
                'scripts/verify_s6_scores.py','scripts/verify_s7_replay.py')})
        shutil.copy2(__file__,args.output/'auditor_snapshot.py')
    except BaseException:
        meta.update(status='failed',traceback=traceback.format_exc())
        raise
    finally:
        meta.update(completed_utc=now(),checks_passed=sum(c['passed'] for c in meta['checks']))
        write(args.output/'verification.json',meta)
    print(json.dumps({k:meta[k] for k in ('status','checks_passed','independent_window_count','selected_window_indices')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','protocol','design-freeze','data','sampling','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
