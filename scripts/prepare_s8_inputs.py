#!/usr/bin/env python3
"""Freeze fixed-time S8 input identities using timestamps, never image pixels."""
import argparse
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from tum_rgbd import read_timestamp_file, associate_rgb_depth
from run_s8_sequence import parse_protocol, validate_manifest, safe_data_path

LENGTH, GAP, SNAP, COUNT = 8.840, .100, .050, 24


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def gt_time_intervals(path):
    """Only parse timestamp token; ignore pose-value tokens until scoring."""
    times = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'): continue
        fields = line.split()
        if len(fields) != 8: raise ValueError(f'GT row structure at line {number}')
        timestamp = float(fields[0])
        if not math.isfinite(timestamp): raise ValueError('Nonfinite GT timestamp')
        times.append(timestamp)
    times.sort()
    if not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Missing or duplicate GT timestamps')
    intervals = [[times[0], times[0]]]
    for a, b in zip(times, times[1:]):
        if b-a > GAP: intervals.append([b,b])
        else: intervals[-1][1] = b
    return times, intervals


def interval_at(t, intervals):
    starts = [x[0] for x in intervals]
    i = bisect_right(starts, t)-1
    return i if i >= 0 and t <= intervals[i][1] else None


def plan_windows(matches, intervals):
    segments, valid, rejected = [], [], []
    for i, match in enumerate(matches):
        ri = interval_at(match.rgb.timestamp, intervals)
        di = interval_at(match.depth.timestamp, intervals)
        if ri is None or di != ri:
            rejected.append(dict(match_index=i, reason='both_times_require_same_gt_interval'))
            continue
        row = dict(match_index=i, rgb_timestamp=match.rgb.timestamp,
                   depth_timestamp=match.depth.timestamp, gt_interval=ri)
        if not valid or valid[-1]['gt_interval'] != ri or match.rgb.timestamp-valid[-1]['rgb_timestamp'] > GAP:
            segments.append([])
        segments[-1].append(row)
        valid.append(row)
    accepted, attempts = [], []
    available_after = -math.inf
    for si, segment in enumerate(segments):
        times = [x['rgb_timestamp'] for x in segment]
        for start in times:
            if start <= available_after: continue
            end = start+LENGTH
            if end > times[-1]:
                attempts.append(dict(segment=si, start=start, reason='insufficient_remaining_duration'))
                break
            targets = [start+LENGTH*i/(COUNT-1) for i in range(COUNT)]
            positions, errors = [], []
            for t in targets:
                right = bisect_left(times, t)
                choices = [j for j in (right-1,right) if 0 <= j < len(times)]
                j = min(choices, key=lambda x: (abs(times[x]-t), times[x]))
                positions.append(j)
                errors.append(abs(times[j]-t))
            reason = None
            if max(errors) > SNAP: reason = 'nearest_rgb_exceeds_50ms'
            elif len(set(positions)) != COUNT: reason = 'duplicate_nearest_frame'
            if reason:
                attempts.append(dict(segment=si, start=start, reason=reason, max_snap_error=max(errors)))
                continue
            selected = [segment[j] for j in positions]
            window = dict(index=len(accepted), segment=si, nominal_start=start, nominal_end=end,
                          target_timestamps=targets, snap_errors_seconds=errors,
                          match_indices=[r['match_index'] for r in selected],
                          rgb_timestamps=[r['rgb_timestamp'] for r in selected],
                          gt_interval=selected[0]['gt_interval'])
            accepted.append(window)
            attempts.append(dict(segment=si, start=start, reason='accepted', accepted_index=window['index']))
            available_after = end+GAP
    chosen = [0, (len(accepted)-1)//2, len(accepted)-1] if len(accepted) >= 3 else []
    return dict(valid_pairs=len(valid), excluded_pairs=rejected,
                segments=[dict(index=i, size=len(s), start=s[0]['rgb_timestamp'],
                               end=s[-1]['rgb_timestamp'], gt_interval=s[0]['gt_interval'])
                          for i,s in enumerate(segments)],
                candidate_attempts=attempts, accepted_windows=accepted, selected_window_indices=chosen)


def run(args):
    if args.output.exists() or args.output.is_symlink(): raise ValueError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    meta = dict(status='running', started_utc=utc(), images_decoded=False, gt_pose_values_parsed=False)
    try:
        protocol = parse_protocol(args.protocol.read_text())
        freeze = json.loads(args.design_freeze.read_text())
        digest = sha(args.protocol)
        if freeze['protocol_sha256'] != digest: raise ValueError('Design protocol changed')
        if args.data.name != 'rgbd_dataset_freiburg2_desk': raise ValueError('Unexpected dataset')
        if args.archive.stat().st_size != 1893351095: raise ValueError('Archive size changed')
        rgb = read_timestamp_file(args.data/'rgb.txt')
        depth = read_timestamp_file(args.data/'depth.txt')
        times, intervals = gt_time_intervals(args.data/'groundtruth.txt')
        matches = associate_rgb_depth(rgb, depth, max_difference=.020)
        plan = plan_windows(matches, intervals)
        meta.update(rgb_count=len(rgb), depth_count=len(depth), paired_count=len(matches),
                    gt_timestamp_count=len(times), gt_intervals=intervals, plan=plan,
                    archive_sha256=sha(args.archive), protocol_sha256=digest,
                    preparation_source_sha256=sha(__file__),
                    text_file_sha256={name:sha(args.data/name) for name in ('rgb.txt','depth.txt','groundtruth.txt')})
        write(args.output/'sampling_metadata.json', meta)
        if not plan['selected_window_indices']: raise ValueError('Fewer than three eligible fixed-duration windows')
        manifest = dict(schema='s8-inputs-v1', dataset=args.data.name,
                        protocol_sha256=digest, runner_sha256=protocol['runner_sha256'],
                        archive_sha256=meta['archive_sha256'],
                        text_file_sha256=meta['text_file_sha256'], blocks=[])
        for b, wi in enumerate(plan['selected_window_indices']):
            window = plan['accepted_windows'][wi]
            frames = []
            for fi, mi in enumerate(window['match_indices']):
                pair = matches[mi]
                row = dict(frame=fi, match_index=mi,
                           target_timestamp=window['target_timestamps'][fi],
                           snap_error_seconds=window['snap_errors_seconds'][fi])
                for kind in ('rgb','depth'):
                    item = getattr(pair, kind)
                    path = safe_data_path(args.data, item.path)
                    row[kind] = dict(timestamp=item.timestamp, path=item.path)
                    row[kind+'_sha256'] = sha(path)
                frames.append(row)
            stamps = [f['rgb']['timestamp'] for f in frames]
            manifest['blocks'].append(dict(block=b, split='test', accepted_window_index=wi,
                nominal_start=window['nominal_start'], nominal_end=window['nominal_end'],
                actual_duration_seconds=stamps[-1]-stamps[0],
                rgb_minus_depth_seconds=[f['rgb']['timestamp']-f['depth']['timestamp'] for f in frames],
                rgb_intervals_seconds=[t-s for s,t in zip(stamps,stamps[1:])], frames=frames))
        validate_manifest(manifest, args.data, digest, protocol)
        write(args.output/'S8_inputs.json', manifest)
        meta.update(status='completed', manifest_sha256=sha(args.output/'S8_inputs.json'),
                    selected_rgb_frames=72, selected_depth_files=72)
    except Exception:
        meta.update(status='failed', traceback=traceback.format_exc())
        raise
    finally:
        meta['completed_utc']=utc()
        write(args.output/'sampling_metadata.json',meta)
    print(json.dumps({k:meta[k] for k in ('status','completed_utc','rgb_count','depth_count','paired_count','manifest_sha256')}))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('data','protocol','design-freeze','archive','output'): p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
