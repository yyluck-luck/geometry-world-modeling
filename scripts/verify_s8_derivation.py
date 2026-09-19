#!/usr/bin/env python3
"""Independent timestamp/byte audit of a completed S8 V2 derivative.

No production derivation function is imported. Only the first GT token is
parsed numerically; image pixels and seven pose tokens remain opaque bytes.
The completed-status gate precedes all source/derived data-tree inspection.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
DATASET='rgbd_dataset_freiburg2_desk'
PRODUCTION_SHA='05eb236982b6eaca47156fc09066e996e9d894dd702be52310f3af4e36609583'
V2_PROTOCOL_SHA='d4ae1781696f4918b65129b82f52698ab07b1642fdf744f74501187a96984431'


def now():return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def digest(payload):return hashlib.sha256(payload).hexdigest()
def read(path):
    def pairs(values):
        out={}
        for k,v in values:
            if k in out:raise ValueError('Duplicate JSON key: '+k)
            out[k]=v
        return out
    def bad(value):raise ValueError('Nonfinite JSON literal: '+value)
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=bad)
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def source_path(name):
    path=Path(name)
    return (path if path.is_absolute() else ROOT/path).resolve(strict=True)


class Checks:
    def __init__(self):self.rows=[]
    def __call__(self,name,passed,kind='recomputed',detail=None):
        row=dict(name=name,passed=bool(passed),kind=kind)
        if detail is not None:row['detail']=detail
        self.rows.append(row)
        if not passed:raise AssertionError(name)


def inventory(root):
    """Independent walk, regular entries only, without following links."""
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('Expected a real data root')
    root=root.resolve(strict=True);directories=[];files=[]
    for current,dirs,names in os.walk(root,topdown=True,followlinks=False):
        current=Path(current)
        for name in dirs:
            path=current/name;mode=path.lstat().st_mode
            if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):raise ValueError('Non-directory or symbolic entry')
            directories.append(str(path.relative_to(root)))
        for name in names:
            path=current/name;before=path.lstat()
            if not stat.S_ISREG(before.st_mode):raise ValueError('Non-regular file entry')
            h=sha(path);after=path.lstat()
            properties=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
            if properties(before)!=properties(after):raise ValueError('File changed while hashing')
            files.append(dict(path=str(path.relative_to(root)),sha256=h,bytes=after.st_size,
                              inode=[after.st_dev,after.st_ino]))
    return dict(directories=sorted(directories),files=sorted(files,key=lambda row:row['path']))


def independent_subtraction(payload):
    """Recompute the global exclusion mask directly from opaque original lines."""
    lines=payload.splitlines(keepends=True);timestamp_by_line={};positions={}
    for i,line in enumerate(lines,1):
        fields=line.split()
        if not fields or fields[0].startswith(b'#'):continue
        if len(fields)!=8:raise ValueError('GT structure differs at line '+str(i))
        t=float(fields[0])
        if not math.isfinite(t):raise ValueError('GT time is not finite')
        timestamp_by_line[i]=t;positions.setdefault(t,[]).append(i)
    duplicate_times=sorted(t for t,indices in positions.items() if len(indices)>1)
    kept=[];excluded=[];retained=[];line_map=[];output_parts=[]
    for i,line in enumerate(lines,1):
        t=timestamp_by_line.get(i)
        covers=[d for d in duplicate_times if t is not None and abs(t-d)<=.051]
        identity=dict(original_line=i,raw_line_sha256=digest(line))
        if t is not None:identity['timestamp']=t
        if covers:
            excluded.append(dict(identity,duplicate_keys_covering_row=covers,
                reason='within_fixed_closed_binary64_neighborhood_of_duplicate_timestamp'))
            continue
        output_parts.append(line);mapped=dict(identity,derived_line=len(output_parts),
            kind='gt_data' if t is not None else 'comment_or_blank')
        line_map.append(mapped)
        if t is not None:
            kept.append(t);retained.append(dict(identity,derived_line=len(output_parts)))
    if not kept or any(b<=a for a,b in zip(kept,kept[1:])):
        raise ValueError('Retained GT empty, repeated or unordered')
    barriers=[]
    for d in duplicate_times:
        lefts=[r for r in retained if r['timestamp']<d]
        rights=[r for r in retained if r['timestamp']>d]
        left=max(lefts,key=lambda r:r['timestamp']) if lefts else None
        right=min(rights,key=lambda r:r['timestamp']) if rights else None
        if left is not None and right is not None:
            gap=right['timestamp']-left['timestamp'];boundary=None
            if not math.isfinite(gap) or gap<=.100:raise ValueError('Conflict barrier does not exceed 100 ms')
        else:
            gap=None;boundary='left_trajectory_boundary' if left is None else 'right_trajectory_boundary'
        barriers.append(dict(duplicate_timestamp=d,duplicate_original_lines=positions[d],
            left_retained=left,right_retained=right,gap_seconds=gap,boundary=boundary,
            satisfies_strict_gap_or_boundary=True))
    derived=b''.join(output_parts)
    expected=dict(original_gt_sha256=digest(payload),derived_gt_sha256=digest(derived),
        original_total_lines=len(lines),derived_total_lines=len(output_parts),
        original_gt_rows=len(timestamp_by_line),derived_gt_rows=len(retained),
        duplicate_groups=[dict(timestamp=d,count=len(positions[d]),original_lines=positions[d]) for d in duplicate_times],
        excluded_gt_rows=len(excluded),excluded_rows=excluded,retained_gt_rows=retained,
        retained_line_mapping=line_map,barriers=barriers)
    return derived,expected


def audit(args,metadata):
    out=args.output;out.mkdir(parents=True,exist_ok=False);check=Checks()
    shutil.copy2(__file__,out/'verifier_snapshot.py')
    report=dict(status='running',started_utc=now(),verifier_sha256=sha(__file__),checks=check.rows,
        image_pixels_decoded=False,gt_pose_values_parsed=False,model_run=False,samples_selected=False,
        source=str(args.source),derivation=str(args.derivation),
        limitations=['No image decoding, pose-value interpretation, sample selection, model inference or scores.',
            'Original archive gzip/tar validation is not repeated; full extracted source and derivative tree bytes are hashed.',
            'Historical source-tree preservation and freeze order combine saved metadata with actual present-day byte checks; no historical file-access trace is reconstructed.'])
    write(out/'verification.json',report);tracked={}
    def integrity(path,expected,name=None):
        path=Path(path).resolve(strict=True);actual=sha(path)
        check(name or 'sha/'+str(path),actual==expected,'integrity')
        tracked[str(path)]=actual
    try:
        check('completed_metadata',metadata['status']=='completed' and metadata['phase']=='complete','metadata')
        meta_path=args.derivation/'derivation_metadata.json';tracked[str(meta_path)]=sha(meta_path)
        freeze=read(args.freeze);freeze_sha=sha(args.freeze);protocol_sha=sha(args.protocol)
        check('reviewed_protocol',protocol_sha==V2_PROTOCOL_SHA==freeze['protocol_sha256']==metadata['protocol_sha256'],'integrity')
        integrity(args.freeze,metadata['design_freeze_sha256']);integrity(args.protocol,protocol_sha)
        identities={source_path(name):h for name,h in freeze['source_sha256'].items()}
        check('unique_frozen_paths',len(identities)==len(freeze['source_sha256']),'integrity')
        producer=(ROOT/'scripts/prepare_tum_timestamp_derivative.py').resolve()
        check('reviewed_producer_identity',identities[producer]==PRODUCTION_SHA==metadata['runner_sha256'],'integrity')
        for path,h in identities.items():integrity(path,h)
        check('frozen_source_metadata_copy',metadata['frozen_source_sha256']==freeze['source_sha256'],'metadata')
        for name,h in (('frozen_protocol.md',protocol_sha),('design_freeze.json',freeze_sha),('derivation_runner_snapshot.py',PRODUCTION_SHA)):
            integrity(args.derivation/name,h)
        check('schema_and_scope',metadata['schema']=='tum-timestamp-derivative-v1' and
            metadata['derivative_not_original_dataset'] is True and metadata['images_decoded'] is False and
            metadata['gt_pose_values_parsed'] is False and metadata['model_run'] is False and metadata['samples_selected'] is False,'metadata')
        times=[datetime.fromisoformat(t) for t in (freeze['frozen_utc'],metadata['started_utc'],metadata['freeze_verified_utc'],metadata['completed_utc'])]
        check('freeze_start_verification_completion_order',all(a<=b for a,b in zip(times,times[1:])) and
            metadata['design_frozen_utc']==freeze['frozen_utc'],'metadata',detail=[t.isoformat() for t in times])
        derived=args.derivation/DATASET
        check('metadata_paths',Path(metadata['source']).resolve()==args.source and
            Path(metadata['output']).resolve()==args.derivation and Path(metadata['derived_dataset_path']).resolve()==derived.resolve(),'metadata')
        check('rule_halfwidth_and_boundary',metadata['rule']['half_width_seconds']==.051 and
            metadata['rule']['exclusion_predicate']=='any(abs(t - d) <= 0.051 for d in all_duplicate_float_timestamps)' and
            metadata['gt_derivation']['rule']==metadata['rule'],'metadata')
        original=inventory(args.source);copied=inventory(derived)
        check('source_inventory_before_after_current',original==metadata['source_inventory_before']==metadata['source_inventory_after'],'integrity')
        check('derived_inventory_current',copied==metadata['derived_inventory'],'integrity')
        old={r['path']:r for r in original['files']};new={r['path']:r for r in copied['files']}
        check('complete_membership',original['directories']==copied['directories'] and set(old)==set(new),'integrity')
        entries=metadata['files'];by_path={r['path']:r for r in entries}
        check('copy_record_coverage',len(entries)==len(by_path)==len(old) and set(by_path)==set(old),'metadata')
        for name,record in old.items():
            current=new[name];entry=by_path[name]
            check(name+'/distinct_inodes',record['inode']!=current['inode'],'integrity')
            check(name+'/recorded_copy_identity',entry['source_sha256']==record['sha256'] and
                entry['derived_sha256']==current['sha256'] and entry['source_inode']==record['inode'] and
                entry['derived_inode']==current['inode'] and entry['bytes']==current['bytes'] and
                entry['independent_inode'] is True,'integrity')
            if name!='groundtruth.txt':
                check(name+'/byte_identical',record['sha256']==current['sha256'] and record['bytes']==current['bytes'],'integrity')
                check(name+'/copy_semantics',entry['transformation']=='byte_identical_independent_copy','metadata')
        check('GT_transform_semantics',by_path['groundtruth.txt']['transformation']=='fixed_timestamp_neighborhood_exclusion','metadata')
        check('frozen_original_GT_identity',old['groundtruth.txt']['sha256']==freeze['original_gt_sha256']==metadata['original_gt_sha256'],'integrity')
        raw=(args.source/'groundtruth.txt').read_bytes();actual=(derived/'groundtruth.txt').read_bytes()
        expected,gt=independent_subtraction(raw)
        check('GT_exact_bytes_independent_exclusion',actual==expected)
        check('GT_independent_sha',digest(actual)==new['groundtruth.txt']['sha256']==metadata['derived_gt_sha256']==gt['derived_gt_sha256'])
        for key,value in gt.items():check('GT_record/'+key,value==metadata['gt_derivation'][key])
        validation=metadata['gt_derivation']['validation']
        expected_flags=('nonempty_gt','timestamps_strictly_increasing_and_unique','every_duplicate_key_removed',
            'every_barrier_valid','exact_original_minus_declared_excluded_lines','retained_line_bytes_and_order_exact','all_passed')
        check('GT_validation_metadata',set(validation)==set(expected_flags) and all(validation[k] is True for k in expected_flags),'metadata')
        check('top_level_success_metadata',metadata['source_tree_unchanged'] is True and metadata['original_gt_unchanged'] is True and
            metadata['all_copy_inodes_independent'] is True and metadata['exact_declared_line_subtraction_verified'] is True and
            metadata['non_gt_copies_verified']==len(old)-1,'metadata')
        check('three_text_SHA',metadata['text_file_sha256']=={name:new[name]['sha256'] for name in ('rgb.txt','depth.txt','groundtruth.txt')},'integrity')
        # Rehash both complete trees at the end of the read-only audit.
        check('source_tree_unchanged_during_audit',inventory(args.source)==original,'integrity')
        check('derived_tree_unchanged_during_audit',inventory(derived)==copied,'integrity')
        for path,h in tracked.items():check('unchanged/'+path,sha(path)==h,'integrity')
        write(out/'independent_gt_derivation.json',gt)
        write(out/'source_inventory.json',original);write(out/'derived_inventory.json',copied)
        report.update(status='passed',source_files=len(old),non_gt_copies_verified=len(old)-1,
            duplicate_groups=len(gt['duplicate_groups']),original_gt_rows=gt['original_gt_rows'],
            derived_gt_rows=gt['derived_gt_rows'],excluded_gt_rows=gt['excluded_gt_rows'],
            original_gt_sha256=gt['original_gt_sha256'],derived_gt_sha256=gt['derived_gt_sha256'],
            barriers=gt['barriers'],protocol_sha256=protocol_sha,design_freeze_sha256=freeze_sha,
            producer_sha256=PRODUCTION_SHA,source_and_derivative_unchanged_during_audit=True)
    except Exception as error:
        report.update(status='failed',error=str(error),traceback=traceback.format_exc())
    report.update(completed_utc=now(),checks_count=len(check.rows),checks_by_kind=dict(Counter(r['kind'] for r in check.rows)),source_sha256=tracked)
    write(out/'verification.json',report)
    print(json.dumps({k:report[k] for k in ('status','checks_count','checks_by_kind','completed_utc')}))
    if report['status']!='passed':print(report['traceback']);return 1
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','derivation','protocol','freeze','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:metadata=read(args.derivation/'derivation_metadata.json')
    except Exception as error:parser.error('Cannot verify derivation completion: '+str(error))
    if metadata.get('status')!='completed' or metadata.get('phase')!='complete':
        parser.error('Derivative is not completed; do not inspect its data tree')
    if args.output.exists() or args.output.is_symlink():parser.error('Preserve prior audits; use a fresh output directory')
    for name in ('source','derivation','protocol','freeze'):setattr(args,name,getattr(args,name).resolve(strict=True))
    args.output=args.output.absolute()
    return audit(args,metadata)


if __name__=='__main__':sys.exit(main())
