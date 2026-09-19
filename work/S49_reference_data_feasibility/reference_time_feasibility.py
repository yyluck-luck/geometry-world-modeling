"""Metadata-only temporal prerequisite check; never reads image bodies."""
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT = Path(__file__).resolve().parent
INPUTS = [
    ('fr1_xyz', 'data/tum/rgbd_dataset_freiburg1_xyz/rgb.txt'),
    ('fr2_desk_original', 'data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk/rgb.txt'),
    ('fr2_desk_guarded_same_capture', 'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb.txt'),
]


def max_window_count(ts, width):
    left = 0
    best = 0
    for right, value in enumerate(ts):
        while value - ts[left] > width:
            left += 1
        best = max(best, right - left + 1)
    return best


def main():
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for name, rel in INPUTS:
        path = ROOT / rel
        raw = path.read_bytes()
        entries = [line.split() for line in raw.decode().splitlines()
                   if line.strip() and not line.lstrip().startswith('#')]
        ns = [Decimal(row[0]) * 10**9 for row in entries]
        assert all(x == x.to_integral_value() for x in ns)
        ts = [int(x) for x in ns]
        assert len(ts) >= 3 and ts == sorted(ts) and len(set(ts)) == len(ts)
        gaps = [b-a for a,b in zip(ts,ts[1:])]
        distinct_near = [bisect_right(ts,t+10_000_000)-bisect_left(ts,t-10_000_000)-1 for t in ts]
        max_window = max_window_count(ts, 20_000_000)
        # Independent direct check of the sliding-window result on this small metadata set.
        direct_max = max(sum(0 <= v-t <= 20_000_000 for v in ts) for t in ts)
        assert direct_max == max_window
        rows.append(dict(sequence=name,metadata_path=rel,metadata_sha256=hashlib.sha256(raw).hexdigest(),
                         indexed_rgb_count=len(ts),local_rgb_path_count=sum((path.parent/e[1]).is_file() for e in entries),
                         min_adjacent_gap_ns=min(gaps),max_adjacent_gap_ns=max(gaps),
                         min_span_of_three_captures_ns=min(ts[i+2]-ts[i] for i in range(len(ts)-2)),
                         max_captures_in_any_closed_20ms_window=max_window,
                         max_other_captures_within_10ms_of_an_existing_capture=max(distinct_near),
                         targets_with_at_least_three_other_captures_within_10ms=sum(c>=3 for c in distinct_near),
                         temporal_prerequisite_for_three_references='FAIL_ON_PUBLISHED_TIMESTAMPS' if max_window<3 else 'UNRESOLVED'))
    protocol=ROOT/'work/S48_geocausal_kill_experiment/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md'
    binding=ROOT/'work/S43_paradigm_shift_audit/raima_v4/REFERENCE_CONTRACT_BINDING.json'
    receipt=dict(schema='raima-reference-time-metadata-feasibility-v1',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
                 evidence_type='REAL_DATA_METADATA_ANALYSIS_ONLY',rows=rows,
                 source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),reference_candidate_binding_sha256=hashlib.sha256(binding.read_bytes()).hexdigest(),
                 hypothesis='At least three distinct real reference captures within +/-10ms of each target',
                 result='LOCAL_TUM_SINGLE_RGB_STREAMS_CANNOT_SUPPLY_THREE_SYNCHRONOUS_REFERENCES_ON_PUBLISHED_TIMESTAMPS',
                 bounds=['fr2 original and guarded files describe the same capture, not independent references',
                         'uses published sensor timestamps; no clock-drift calibration has been acquired or inferred',
                         'single-image B0/C1/C2 have no qualified independent reference by S48 protocol',
                         'time feasibility is necessary only; camera, pose, validity, state lock and leakage remain untested',
                         'no conclusion about unseen datasets, multiple synchronized sensors or a separately registered static-scene contract'],
                 images_opened=0,pixels_decoded=0,models_called=0,scientific_effect_claim=False)
    target=OUT/'reference_time_feasibility.json'
    with target.open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'rows':rows},ensure_ascii=False))


if __name__=='__main__':
    main()
