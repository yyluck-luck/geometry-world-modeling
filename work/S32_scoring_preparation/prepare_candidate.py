#!/usr/bin/env python3
"""Create unbound S32 scoring inputs from existing selection JSON, not images."""
import ast
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ENDPOINTS=('initial_0step','corrected_getter_400','global_rescaled_400')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    target=HERE/'manifest_candidate.json';assert not target.exists(),'No candidate overwrite'
    start=datetime.now(timezone.utc).isoformat()
    selection=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json'
    metadata=ROOT/'work/S32_selection/selected_windows.json'
    assert sha(selection)=='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
    assert sha(metadata)=='4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6'
    d=json.loads(selection.read_text());assert d['parent_selection_sha256']==sha(metadata)
    windows=[]
    for w in d['windows']:
        blocked=w['id']=='fr2_desk_j1';directory=ROOT/'results/S32_consumer_windows'/w['id']
        frames=[dict(index=f['index'],rgb_time=f['rgb_time'],depth_path=f['sensor_depth_association']['path'],
            depth_time=f['sensor_depth_association']['time'],depth_sha256=None,
            depth_identity_status='PENDING_ROOT_BYTE_SEAL_AFTER_ALL_PREDICTION_ENDPOINTS') for f in w['frames']]
        windows.append(dict(id=w['id'],availability='UNAVAILABLE_MISSING_POSE' if blocked else 'PENDING_PRODUCER_TERMINAL',
            reason='All four fixed frames lack the original <20ms GT-pose association; no replacement' if blocked else 'Pending actual whole-window PASS or FAILED; no result assumed',
            producer_receipt=dict(path=str(directory/'receipt.json'),sha256=None),frames=frames,
            endpoints={e:dict(status='UNAVAILABLE' if blocked else 'PENDING',path=None if blocked else str(directory/(e+'.npz')),
                sha256=None,depth_key='depth',dtype='float64' if e=='global_rescaled_400' else 'float32') for e in ENDPOINTS}))
    source=HERE/'score_s32.py';protocol=HERE/'protocol.md';original=ROOT/'scripts/score_s26b_consumer.py'
    assert sha(original)=='02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7'
    for p in (source,Path(__file__).resolve()):ast.parse(p.read_text());compile(p.read_text(),str(p),'exec')
    candidate=dict(schema='s32-complete-window-scoring-v1',status='CANDIDATE_UNBOUND_DO_NOT_EXECUTE',prepared_utc=datetime.now(timezone.utc).isoformat(),
        selection_path=str(selection),selection_sha256=sha(selection),metadata_selection_path=str(metadata),metadata_selection_sha256=sha(metadata),
        endpoints=list(ENDPOINTS),windows=windows,output_root=str(ROOT/'results/S32_consumer_scoring'),
        resource=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),
        control_sha256={str(p):sha(p) for p in (source,protocol,original,Path(__file__).resolve())},
        upstream_seal_receipts=[],upstream_seal_receipts_status='PENDING_ROOT_RECEIPTS_FOR_ALL_ENDPOINT_AND_GT_BYTE_FREEZE',
        fixed_denominators=dict(prespecified_windows=4,pose_eligible_windows=3,endpoint_groups=12,per_frame_rows=48),
        no_GT_fit=True,no_confidence_mask=True,no_far_cut=True,no_frame_or_pixel_significance=True,
        missing_policy='Keep first missing-pose window and any terminal producer failures as 12 NA rows/window; no partial-start scoring or available-case means',
        freeze_requirements=['Actual shared terminal receipts and output SHA for all four windows','Available window all three depth NPZ, FP32/FP32/FP64',
            'GT SHA obtained by root only after available endpoints and all window terminal receipts seal','Root reviews this scorer/protocol, binds receipt evidence, sets FROZEN and supplies manifest SHA'])
    write(target,candidate)
    write(HERE/'preparation_receipt.json',dict(status='PASS_METADATA_AND_STATIC_ONLY_NOT_SCIENTIFIC_RUN',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(source),protocol_sha256=sha(protocol),candidate_sha256=sha(target),prepare_script_sha256=sha(Path(__file__).resolve()),
        metadata_sources_sha256={str(selection):sha(selection),str(metadata):sha(metadata)},
        actual_checks=['Read original frozen scorer source and fixed selection metadata only','AST parse and compile, no exec/import of scientific modules or functions',
            'Candidate retains all4 windows/all3 endpoints/all4 frames and unbound future producer/GT SHA'],
        actual_access=dict(RGB_bytes=0,prediction_NPZ_bytes=0,sensor_depth_PNG_bytes=0,scientific_numeric_function_calls=0,model_runs=0,GA_runs=0),
        limitations=['No runtime check or result verification yet','Manifest intentionally pending; cannot be executed','Root future independent numerical review remains separate']))
    print(json.dumps(dict(status='PREPARED_NOT_EXECUTED',candidate_sha256=sha(target),source_sha256=sha(source),protocol_sha256=sha(protocol))))

if __name__=='__main__':main()
