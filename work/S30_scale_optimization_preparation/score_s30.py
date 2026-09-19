"""Score saved S29 starts and sealed S30 final outputs with unchanged S26 math."""
import argparse
import csv
import io
from pathlib import Path
import run_s30 as run


def score(c):
    out=Path(c['output_root'])/'scoring';run.require(not out.exists(),'No repeat or overwrite scoring');out.mkdir(parents=True)
    receipt=dict(status='RUNNING',started_utc=run.utc(),contract_sha256=c['_sha'],sensor_GT_started=False,
                 new_MST=0,new_model=0,new_Adam=0,evidence_scope='Four prespecified initial/final common4 endpoints, previously seen data')
    run.write(out/'receipt.json',receipt)
    try:
        p=run.module(c['parent_scorer'],'s30_frozen_depth_math');p.COUNTS={arm:4 for arm in c['arms']}
        config=dict(producer_dirs={arm:str(Path(c['output_root'])/arm) for arm in c['arms']});identities=dict(c['identities']);initial_bytes={}
        for arm in c['arms']:
            directory=Path(config['producer_dirs'][arm]);rec=run.read(directory/'receipt.json')
            run.require(rec['status']=='PASS' and rec['s30_contract_sha256']==c['_sha'],'Both complete S30 producers must PASS')
            run.require(rec['iterations']==rec['adam_steps']==400 and rec['clean_calls']==1 and rec['observer']['s30_gradient_steps']==400,'Complete original trajectories and gradient observations')
            init=rec['observer']['s30_initialization']
            run.require(init['reference_S29_raw_exact'] is True and init['getter_forward_bytes_exact'] is True and init['getter_repair_active'] is True,'Own S29 start and fixed getter')
            for name,h in rec['outputs'].items():
                target=directory/name;run.require(run.sha(target)==h,'Sealed producer artifact: '+name);identities[str(target)]=h
            run.require(run.read(directory/'inputs_seal.json')['s30_contract_sha256']==c['_sha'],'S30 input contract')
            ref=c['s29_reference'][arm];old=run.read(ref['receipt'])
            run.require(old['status']=='PASS_INITIALIZATION_EXECUTED' and old['contract_sha256']==c['s29_contract_sha256'] and old['arm']==arm,'S29 initial producer seal')
            run.require(old['counts']==dict(MST=1,PnP=3,alignment=1,objective=1,backward=0,Adam=0,clean=0,model=0,GT=0),'Historical initial endpoint is zero-step')
            identities[ref['receipt']]=run.sha(ref['receipt'])
            for name,item in ref['files'].items():
                raw=Path(item['path']).read_bytes();run.require(run.hashlib.sha256(raw).hexdigest()==item['sha256']==old['outputs'][name],'Original zero-step artifact seal: '+name)
                identities[item['path']]=item['sha256']
                if name=='initial_decoded.npz':initial_bytes[arm]=raw
        final_bytes,producer_ids=p.seal_producers(config,c['parent_manifest_sha256']);identities.update(producer_ids)
        run.write(out/'pre_score_seal.json',dict(status='PASS',utc=run.utc(),contract_sha256=c['_sha'],input_sha256=identities,
            both_final_producers_complete=True,both_saved_S29_starts_bound=True,scoring_arrays_decoded=False,sensor_GT_bytes_read=False))
        import numpy as np
        final,schema=p.decode_outputs(final_bytes);del final_bytes
        starts={}
        for arm,raw in initial_bytes.items():
            with np.load(io.BytesIO(raw),allow_pickle=False) as z:starts[arm]=z['depth'].copy()
            run.require(starts[arm].shape==(4,384,512) and starts[arm].dtype==np.float32,'Saved zero-step depth schema')
        del initial_bytes
        run.write(out/'output_schema.json',schema)
        receipt.update(sensor_GT_started=True,sensor_GT_started_utc=run.utc());run.write(out/'receipt.json',receipt)
        gt,gt_records,gt_ids=p.load_sensor_depths(c['gt_depth_frames']);identities.update(gt_ids)
        run.write(out/'gt_receipt.json',dict(utc=run.utc(),files=gt_records,already_seen_in_s23=True,role='Same scoring-only depth for all four endpoints'))
        rows=[]
        for arm in c['arms']:
            for endpoint,depth in [('initial',starts[arm]),('final',final[arm]['depth'])]:
                for i in range(4):rows.append(dict(mode=arm,endpoint=endpoint,index=i,**p.depth_metrics(depth[i],gt[i])))
        with (out/'per_frame.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        means={arm:{endpoint:p.aggregate([row for row in rows if row['mode']==arm and row['endpoint']==endpoint],list(range(4)))
                    for endpoint in ['initial','final']} for arm in c['arms']}
        delta={arm:{key:means[arm]['final'][key]-means[arm]['initial'][key] if means[arm]['final'][key] is not None and means[arm]['initial'][key] is not None else None
                    for key in ['absrel','rmse_m','delta1','prediction_invalid_fraction_on_gt']} for arm in c['arms']}
        run.write(out/'metrics.json',dict(contract_sha256=c['_sha'],utc=run.utc(),common4=means,final_minus_initial=delta,per_frame=rows,
            scale_fit=False,confidence_mask=False,far_depth_cut=False,
            evidence_limits=['Previously seen four adjacent frames; no blind-test or generalization claim',
                'Shared given GT camera is an oracle input; sensor depth is scoring only',
                'Both use the corrected getter and original objective; only the centered initialization-scale family differs',
                'Initial scores use the saved S29 zero-step outputs, not another initialization run',
                'Exactly the 400-step final endpoint; no best-step selection, scale fit or GT prior',
                'Ordinary engineering scale control; no method novelty or generated-video measurement']))
        for path,h in identities.items():run.require(run.sha(path)==h,'Input changed during scoring: '+path)
        receipt.update(status='PASS',completed_utc=run.utc(),sensor_depth_images_decoded=4,per_frame_rows=16,endpoint_groups=4,
            input_sha256=identities,outputs={x.name:run.sha(x) for x in out.iterdir() if x.is_file() and x.name!='receipt.json'})
        run.write(out/'receipt.json',receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=run.utc(),error=str(e));run.write(out/'receipt.json',receipt);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True)
    args=p.parse_args();score(run.contract(args.contract,args.sha256))
