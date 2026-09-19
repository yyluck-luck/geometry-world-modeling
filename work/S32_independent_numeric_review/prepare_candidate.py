#!/usr/bin/env python3
"""Prepare source/metadata-only S32 independent review; never reads scientific data."""
import ast
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,x):(HERE/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    assert not (HERE/'candidate.json').exists(),'Do not overwrite candidate'
    started=datetime.now(timezone.utc).isoformat()
    score=ROOT/'work/S32_scoring_preparation'
    expected={str(score/'score_s32.py'):'adb646284110b38741c311e893064558ca4d409ecc3b5e7e75c4540f1203c319',
        str(score/'protocol.md'):'a74e52e4e8d7fbed84ff31e3c16f6e33cecd26230527fc5b0b5a5923fa335646',
        str(score/'manifest_candidate.json'):'d81e719029732d2fb1219aa04175d6af173db620feeead980decf83503ccd186',
        str(ROOT/'work/S28_independent_numeric_review/recompute.py'):'2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2',
        str(ROOT/'work/S32_preparation/contract.json'):'1749d83fac56a8c7f50b74d37e2278239df25534318967fa93f4798eb5054124',
        str(ROOT/'work/S32_preparation/B_contract.json'):'340c1b7b9e246fb088db8a50194d3003e1e384ecb05a24dc901bda2ff7bdca60',
        str(ROOT/'work/S32_continuation/score_root_pre_review.json'):'baecde6f8b723075d0550389623245e2cc68d6aae8ce461b1761818d05a36f32',
        str(ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json'):'ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318',
        str(ROOT/'work/S32_selection/selected_windows.json'):'4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6',
        str(ROOT/'work/S32_preparation/run_consumer.py'):'7552b65cf9913eafecec781437bc898f962e00df1d845a57130abe4c82d4cfcd'}
    for p,h in expected.items():assert sha(p)==h,'Changed preparation source: '+p
    sc=json.loads((score/'manifest_candidate.json').read_text())
    for p,h in sc['control_sha256'].items():assert sha(p)==h;expected[p]=h
    bc=json.loads((ROOT/'work/S32_preparation/B_contract_candidate.json').read_text())
    b_sources=[bc[k] for k in ('runner','parent_runner','s28_runner','s30_runner','s31_normalizer')]
    for p in b_sources:assert sha(p)==bc['identities'][p];expected[p]=bc['identities'][p]
    for p in (HERE/'recompute.py',HERE/'protocol.md',Path(__file__).resolve()):expected[str(p)]=sha(p)
    for p in (HERE/'recompute.py',Path(__file__).resolve()):ast.parse(p.read_text());compile(p.read_text(),str(p),'exec')
    candidate=dict(schema='s32-independent-numeric-candidate-v1',status='CANDIDATE_UNBOUND_DO_NOT_EXECUTE',
        prepared_utc=datetime.now(timezone.utc).isoformat(),source_sha256=expected,B_execution_sources=b_sources,
        A_contract=dict(path=str(ROOT/'work/S32_preparation/contract.json'),sha256=expected[str(ROOT/'work/S32_preparation/contract.json')]),
        B_contract=dict(path=str(ROOT/'work/S32_preparation/B_contract.json'),sha256=expected[str(ROOT/'work/S32_preparation/B_contract.json')]),
        windows=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2'],
        endpoints=['initial_0step','corrected_getter_400','global_rescaled_400'],
        resource=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),
        expected_complete_matrix=dict(all_rows=48,all_groups=12,pose_eligible_windows=3,
            scored_rows_if_all_eligible_PASS=36,NA_rows_if_all_eligible_PASS=12,
            scale_pixels_if_all_eligible_PASS=3*4*384*512,GT_images_if_all_eligible_PASS=12),
        runtime_binding=dict(schema='s32-independent-numeric-binding-v1',status='FROZEN',candidate_sha256='ROOT_BINDS_THIS_CANDIDATE',
            B_contract=dict(path=None,sha256=None),scoring_manifest=dict(path=None,sha256=None),
            scoring_receipt=dict(path=None,sha256=None),root_seal_receipts=[]),
        actual_preparation_access=dict(RGB_bytes=0,NPZ_bytes=0,sensor_PNG_bytes=0,GT_pose_text_bytes=0,scientific_compute=0,new_models=0,new_GA=0),
        scope='Independent full saved-depth table, all-pixel prediction-only scalar and saved 400-step/raw-boundary audit; no new experiment or component-SS-share recomputation')
    write('candidate.json',candidate)
    write('preparation_receipt.json',dict(status='PASS_SOURCE_METADATA_PREPARATION_ONLY',started_utc=started,
        completed_utc=datetime.now(timezone.utc).isoformat(),candidate_sha256=sha(HERE/'candidate.json'),runner_sha256=sha(HERE/'recompute.py'),
        source_sha256=expected,checks=['Read frozen source and JSON metadata only','AST/compile both new Python files; no scientific imports'],
        actual_access=candidate['actual_preparation_access'],runtime_binding='Pending root review and actual completed result SHA; do not execute'))
    print(json.dumps(dict(status='CANDIDATE_READY_NOT_EXECUTED',runner_sha256=sha(HERE/'recompute.py'),candidate_sha256=sha(HERE/'candidate.json'))))

if __name__=='__main__':main()
