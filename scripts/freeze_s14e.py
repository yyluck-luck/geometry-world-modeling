#!/usr/bin/env python3
"""Freeze S14E stage inputs and seal completed predictions; never decode arrays."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,x):
    p=Path(p)
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'path':str(p),'sha256':sha(p)}))
def ident(paths):return {str(Path(p).resolve()):sha(p) for p in paths}


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['initial','model','seal']);a=p.parse_args()
    r=ROOT;docs=r/'docs';old=r/'results/S14D_ray_only_probe'
    pre=r/'results/S14E_known_camera_prepare';model=r/'results/S14E_known_camera_queries'
    python=str(r/'.venv-cut3r/bin/python')
    prior_manifest=docs/'S14D_RAY_ONLY_EXECUTION_MANIFEST_V2.json'; prior=read(prior_manifest)
    controls=[docs/'S14E_FINAL_PROTOCOL.md',r/'RESEARCH_PRINCIPLES.md',r/'scripts/freeze_s14e.py',
              r/'scripts/verify_s14e_independent.py',r/'scripts/run_s14d_controlled.py',
              docs/'S14E_PRE_RUN_REVIEW.md',r/'work/S14E_pre_run_review/final_review_receipt.json']
    if a.phase=='initial':
        audit=read(controls[-1]);assert audit['status']=='PASS'
        assert audit['sources']
        for path,digest in audit['sources'].items():assert sha(path)==digest, 'Reviewed source changed: '+path
        dataset=r/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk'
        config=dict(schema='s14e-known-camera-prepare-manifest-v1',frozen_utc=utc(),python=python,dataset_root=str(dataset),
                    runner=str(r/'scripts/prepare_s14e_known_camera.py'),frozen_inputs=str(r/'results/S8_cut3r_cpu_v2/frozen_inputs.json'),
                    s8_metadata=str(r/'results/S8_cut3r_cpu_v2/block0/run_metadata.json'),s14d_metadata=str(old/'run_metadata.json'),
                    s14d_manifest=str(prior_manifest),history_predictions_npz=str(r/'results/S8_cut3r_cpu_v2/block0/predictions.npz'),
                    s14d_probe_npz=str(old/'probe_inputs.npz'),trajectory=str(dataset/'groundtruth.txt'),viewer_path=str(Path(prior['repo'])/'viser_utils.py'),
                    contract=dict(history_count=20,target_indices=[20,21,22,23],history_time='rgb',target_time='depth',
                                  K=[[245.2734375,0,112],[0,245,111.5],[0,0,1]],size=[224,224],max_trajectory_gap_seconds=.1,
                                  max_rgb_depth_offset_seconds=.02,minimum_alignment_D_metric_squared=1e-12,rotation_atol=1e-5,
                                  roundtrip_atol=1e-5,roundtrip_rtol=1e-5,history_rgb_allowed=False,target_rgb_allowed=False,target_depth_allowed=False))
        roles=['runner','frozen_inputs','s8_metadata','s14d_metadata','s14d_manifest','history_predictions_npz','s14d_probe_npz','trajectory','viewer_path']
        config['identities']=ident([config[k] for k in roles]+controls+[docs/'S14E_PREPARE_INTERFACE.md'])
        write(docs/'S14E_PREPARE_EXECUTION_MANIFEST.json',config)
        f=read(config['frozen_inputs']);targets=[]
        for frame in f['blocks'][0]['frames'][20:24]:
            targets.append(dict(query_index=frame['frame'],depth_path=str(dataset/frame['depth']['path']),depth_sha256=frame['depth_sha256']))
        score=dict(schema='s14e-score-manifest-v1',frozen_utc=utc(),runner=str(r/'scripts/score_s14e_depth.py'),python=python,
                   model_result_dir=str(model),prepare_result_dir=str(pre),targets=targets,
                   identities=ident(controls+[r/'scripts/score_s14e_depth.py',docs/'S14E_SCORE_INTERFACE.md']),
                   target_identity_source='Previously frozen S8 target SHA; no target depth bytes read by this freeze utility')
        score['identities'].update({t['depth_path']:t['depth_sha256'] for t in targets})
        write(docs/'S14E_SCORE_EXECUTION_MANIFEST.json',score)
    elif a.phase=='model':
        meta=read(pre/'run_metadata.json');seal=read(pre/'condition_seal.json')
        assert meta['status']=='SUCCESS' and seal['condition_npz_sha256']==sha(pre/'condition.npz')
        for n,h in seal['payload_sha256'].items():assert sha(pre/n)==h
        config=dict(schema='s14e-state-reuse-manifest-v1',frozen_utc=utc(),repo=prior['repo'],commit=prior['commit'],python=python,
                    runner=str(r/'scripts/run_s14e_state_reuse_queries.py'),checkpoint=prior['checkpoint'],rope_check=prior['rope_check'],
                    prior_run_metadata=str(old/'run_metadata.json'),state_npz=str(old/'state_before.npz'),
                    parity_inputs_npz=str(old/'probe_inputs.npz'),parity_output_npz=str(old/'query_call_1.npz'),
                    condition_npz=str(pre/'condition.npz'),condition_seal=str(pre/'condition_seal.json'),
                    contract=dict(target_count=4,query_count=5,dummy_values=['zero']*5,
                                  query_flags=dict(img_mask=False,ray_mask=True,update=False,reset=False),device='cpu',cpu_threads=8,seed=0,
                                  size=[224,224],dtype='float32',wall_seconds=600,monitored_rss_bytes=34359738368,
                                  history_rgb_allowed=False,target_rgb_allowed=False,target_depth_allowed=False))
        paths=[config[k] for k in ['runner','checkpoint','rope_check','prior_run_metadata','state_npz','parity_inputs_npz','parity_output_npz','condition_npz','condition_seal']]
        paths += [Path(k) for k in prior['identities'] if Path(k).is_relative_to(Path(prior['repo'])) and Path(k).suffix=='.py']
        paths += controls+[r/'scripts/cut3r_rope_compat.py',docs/'S14E_PREDICTOR_PREPARATION.md',pre/'run_metadata.json',docs/'S14E_PREPARE_EXECUTION_MANIFEST.json',docs/'S14E_SCORE_EXECUTION_MANIFEST.json']
        config['identities']=ident(paths)
        reused=[config['checkpoint'],config['rope_check'],str(r/'scripts/cut3r_rope_compat.py')]
        reused += [k for k in config['identities'] if Path(k).is_relative_to(Path(prior['repo'])) and Path(k).suffix=='.py']
        for path in reused:
            assert config['identities'][path]==prior['identities'][path], 'Prior model/source identity changed: '+path
        write(docs/'S14E_MODEL_EXECUTION_MANIFEST.json',config)
    else:
        for path in [pre,model]:
            meta=read(path/'run_metadata.json');assert meta['status']=='SUCCESS'
            for n,h in meta['output_sha256'].items():assert sha(path/n)==h
        seal=dict(schema='s14e-combined-prediction-seal-v1',sealed_utc=utc(),
                  identities=ident([p for d in [pre,model] for p in d.rglob('*') if p.is_file()]))
        write(docs/'S14E_COMBINED_PREDICTION_SEAL.json',seal)


if __name__=='__main__':main()
