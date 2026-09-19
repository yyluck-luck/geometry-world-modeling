#!/usr/bin/env python3
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
import json
from pathlib import Path
import sys
import traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from experiment_io import begin_run,complete_run,write_json,append_jsonl,utc_now,sha256
from rgbd_dataset import dataset_index,frame_dict
from rgbd_experiment import compare_case


def task(data,output,block,stride,bias,resolutions):
    matches,trajectory,manifest=dataset_index(data)
    frames=[frame_dict(data,matches[i],trajectory) for i in manifest['blocks'][block]]
    return compare_case(frames,block,stride,bias,Path(output)/f'block{block}_stride{stride}_bias{round(bias*1000):02}',resolutions)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    p.add_argument('--output',type=Path,default=ROOT/'results/S3_rgbd_memory')
    p.add_argument('--workers',type=int,default=2)
    p.add_argument('--blocks',type=int,nargs='+',default=[0,1,2])
    p.add_argument('--strides',type=int,nargs='+',default=[16,24])
    p.add_argument('--biases',type=float,nargs='+',default=[0.,.02,.05])
    p.add_argument('--resolutions',type=int,nargs='+',default=[160,320])
    args=p.parse_args()
    config={k:v for k,v in vars(args).items() if k not in ('data','output')}
    meta=begin_run(args.output,'docs/S2_S3_PROTOCOL.md',config)
    _,_,manifest=dataset_index(args.data)
    write_json(args.output/'selection_manifest.json',manifest)
    cases=[(b,s,v) for b in args.blocks for s in args.strides for v in args.biases]
    results,errors=[],[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(task,args.data,args.output,b,s,v,args.resolutions):(b,s,v) for b,s,v in cases}
        for future in as_completed(futures):
            condition=futures[future]
            try:
                result=future.result();results.append(result)
                for record in result['records']: append_jsonl(args.output/'records.jsonl',record)
                status=dict(condition=condition,status='completed',elapsed_seconds=result['elapsed_seconds'],utc=utc_now())
            except Exception as e:
                status=dict(condition=condition,status='error',error=str(e),traceback=traceback.format_exc(),utc=utc_now())
                errors.append(status)
            append_jsonl(args.output/'progress.jsonl',status)
            print(json.dumps(status),flush=True)
    rows=[]
    for case in results:
        for record in case['records']:
            for width,pair in record['retrieval'].items():
                row={k:record[k] for k in ('block','split','stride','first_frame_depth_axis_bias_m','query','timestamp','common_prediction_pixels')}
                row.update(width=int(width),selection_set_changed=pair['selection_set_changed'],support_coverage_delta=pair['coverage_delta'])
                for name in ('first_write','frame_mean'):
                    row[f'{name}_selected']=','.join(map(str,pair[name]['selected']))
                    row[f'{name}_support_coverage']=pair[name]['fixed_measurement_support_coverage']
                    row[f'{name}_median_abs_mm']=record['geometry'][name]['median_abs_mm']
                    row[f'{name}_mae_mm']=record['geometry'][name]['mae_mm']
                    row[f'{name}_map_points']=case['maps'][name]['points']
                rows.append(row)
    rows.sort(key=lambda r:(r['block'],r['stride'],r['first_frame_depth_axis_bias_m'],r['query'],r['width']))
    if rows:
        with (args.output/'pairs.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write_json(args.output/'errors.json',errors)
    complete_run(args.output,meta,completed_cases=len(results),expected_cases=len(cases),errors=len(errors),
                 paired_queries=sum(len(r['records']) for r in results),paired_retrieval_rows=len(rows),
                 dataset_archive_manifest_sha256=sha256(args.data.parent/'download_manifest.json'))
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
