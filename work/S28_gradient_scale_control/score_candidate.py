"""S28 paired common4 scorer. Existing frozen scoring math is called unchanged."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import sys

import run_candidate as run


def score(c):
    p=run.module(c['parent_scorer'],'s28_original_depth_math')
    p.COUNTS={arm:4 for arm in c['arms']}
    out=Path(c['output_root'])/'scoring'
    run.require(not out.exists(),'Never overwrite or rescore this pair')
    out.mkdir(parents=True)
    r=dict(status='RUNNING',started_utc=run.utc(),s28_contract_sha256=c['_sha'],
           sensor_gt_byte_reads_started=False,model_forwards=0,GA_runs=0,
           evidence_scope='Two new matched common4 engineering controls on previously seen data, not a novel method or video result')
    run.write(out/'receipt.json',r)
    try:
        # Reuse exact original producer/input/NPZ byte gates, adapting only the
        # declared producer domain to the two four-image arms.
        config=dict(producer_dirs={arm:str(Path(c['output_root'])/arm) for arm in c['arms']})
        identities=dict(c['identities'])
        for arm in c['arms']:
            directory=Path(config['producer_dirs'][arm]);rec=run.read(directory/'receipt.json')
            run.require(rec['status']=='PASS' and rec['s28_contract_sha256']==c['_sha'],'Both S28 producers must PASS')
            run.require(rec['iterations']==rec['adam_steps']==400 and rec['clean_calls']==1,'Both complete original 400-step trajectories')
            run.require(rec['observer']['s28_gradient_steps']==400 and rec['parent_identities_rechecked'] is True,'Complete S28 observation')
            run.require(rec['observer']['s28_initialization']['getter_forward_bytes_exact'] is True,'Getter value contract')
            if arm=='gradient_only':run.require(rec['observer']['s28_initialization']['cross_arm_raw_exact'] is True,'Matched raw initial state')
            for name,h in rec['outputs'].items():
                target=directory/name;run.require(run.sha(target)==h,'All producer artifact seals before GT: '+name)
                identities[str(target)]=h
            run.require(run.read(directory/'inputs_seal.json')['s28_contract_sha256']==c['_sha'],'S28 input contract identity')
        buffers,producer_ids=p.seal_producers(config,c['parent_manifest_sha256'])
        identities.update(producer_ids)
        run.write(out/'pre_score_seal.json',dict(status='PASS',utc=run.utc(),s28_contract_sha256=c['_sha'],
            all_two_complete_producer_outputs_verified=True,prediction_arrays_decoded=False,sensor_gt_bytes_read=False,input_sha256=identities))
        arrays,schema=p.decode_outputs(buffers);del buffers
        run.write(out/'output_schema.json',schema)
        # No old-depth invariance comparison: both common4 arms have depths=None.
        # No pixel/scale/confidence change relative to the original scorer.
        r.update(sensor_gt_byte_reads_started=True,sensor_gt_read_started_utc=run.utc());run.write(out/'receipt.json',r)
        gt,gt_records,gt_ids=p.load_sensor_depths(c['gt_depth_frames'])
        identities.update(gt_ids)
        run.write(out/'gt_receipt.json',dict(utc=run.utc(),files=gt_records,already_seen_in_s23=True,source_role='scoring only'))
        rows=[]
        for arm in c['arms']:
            for i in range(4):rows.append(dict(mode=arm,index=i,**p.depth_metrics(arrays[arm]['depth'][i],gt[i])))
        with (out/'per_frame.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        metrics=dict(s28_contract_sha256=c['_sha'],utc=run.utc(),primary_common4={
            arm:p.aggregate([row for row in rows if row['mode']==arm],list(range(4))) for arm in c['arms']},
            per_frame=rows,scale_fit=False,confidence_mask=False,gt_far_cut=False,
            evidence_limits=['Previously seen four adjacent fr2_desk frames; not independent test or generalization',
                'Given GT cameras are a shared control condition, not deployment pose estimates',
                'Only gradient connectivity changed after the original MST; original orientation and scale initialization retained',
                'Ordinary autograd repair is not a research novelty; consumer depth is not generated video quality'])
        run.write(out/'metrics.json',metrics)
        for path,h in identities.items():run.require(run.sha(path)==h,'Changed scoring identity: '+path)
        r.update(status='PASS',completed_utc=run.utc(),sensor_gt_images_decoded=4,per_frame_rows=8,
                 inputs_unchanged=True,input_sha256_before_after=identities,
                 outputs={x.name:run.sha(x) for x in out.iterdir() if x.is_file() and x.name!='receipt.json'})
        run.write(out/'receipt.json',r)
    except BaseException as e:
        r.update(status='FAILED',failed_utc=run.utc(),error=str(e));run.write(out/'receipt.json',r);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();c=run.contract(args.contract,args.sha256);c['_sha']=args.sha256;score(c)
