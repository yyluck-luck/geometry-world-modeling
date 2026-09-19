#!/usr/bin/env python3
"""S1: paired synthetic geometry interventions through official final selection."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import scipy
import torch
from retrieval_diagnostic import build_fixture, warm_threshold, evaluate, camera, perturb, reference_coverage


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/retrieval_sensitivity.json')
    parser.add_argument('--out',type=Path,default=ROOT/'results/S1_retrieval_sensitivity')
    args = parser.parse_args()
    args.config, args.out = args.config.resolve(), args.out.resolve()
    if (args.out/'records.jsonl').exists():
        raise FileExistsError('Existing results are preserved; choose a new --out directory.')
    cfg = json.loads(args.config.read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'fixtures').mkdir(exist_ok=True)
    started, tick = now(), time.perf_counter()
    (args.out/'status.json').write_text(json.dumps(dict(status='running',started_utc=started),indent=2))
    rows = []
    with (args.out/'records.jsonl').open('w') as record_file:
        for scenario,seed,scale in itertools.product(cfg['scenarios'],cfg['seeds'],cfg['resolution_scales']):
            fixture = build_fixture(scenario,seed,scale,cfg)
            threshold = warm_threshold(fixture,cfg)
            name = f'{scenario}_seed{seed}_scale{scale}'
            np.savez_compressed(args.out/'fixtures'/f'{name}.npz',points=fixture['points'],
                                radii=fixture['radii'],blocks=fixture['blocks'],poses=np.array(fixture['poses']))
            (args.out/'fixtures'/f'{name}.json').write_text(json.dumps(dict(mapping=fixture['mapping'],
                 threshold=threshold,width=fixture['width'],height=fixture['height'],source_focal=fixture['source_focal']),indent=2))
            for query_x in cfg['query_x']:
                query = camera(x=query_x,y=cfg['query_y'])
                reference, clean_render = evaluate(fixture,cfg,fixture['points'],query,threshold)
                ref_support = reference_coverage(reference['selected'],clean_render,fixture)
                for kind,level in itertools.product(cfg['corruptions'],cfg['levels']):
                    row = dict(scenario=scenario,seed=seed,scale=scale,query_x=query_x,
                               corruption=kind,level=level,magnitude=cfg[kind][level])
                    try:
                        changed_points = perturb(fixture,kind,cfg[kind][level],cfg)
                        if level=='clean':
                            # Reuse the clean selection; this cell is explicitly not an independent trial.
                            treatment = reference
                        else:
                            treatment,_ = evaluate(fixture,cfg,changed_points,query,threshold)
                        support = reference_coverage(treatment['selected'],clean_render,fixture)
                        ref_w, new_w = dict(reference['weights']),dict(treatment['weights'])
                        row.update(status='ok',
                            candidate_set_changed=set(reference['candidates'])!=set(treatment['candidates']),
                            selected_set_changed=set(reference['selected'])!=set(treatment['selected']),
                            selected_order_changed=reference['selected']!=treatment['selected'],
                            reference_selected=','.join(map(str,reference['selected'])),
                            treatment_selected=','.join(map(str,treatment['selected'])),
                            weight_l1=sum(abs(ref_w.get(i,0)-new_w.get(i,0)) for i in set(ref_w)|set(new_w)),
                            clean_reference_support=ref_support, treatment_reference_support=support,
                            reference_support_delta=support-ref_support if support is not None and ref_support is not None else None,
                            reference_render_coverage=reference['rendered_coverage'],
                            treatment_render_coverage=treatment['rendered_coverage'],
                            reference_cutoff_gap=reference['cutoff_gap_14_15'],
                            treatment_cutoff_gap=treatment['cutoff_gap_14_15'],
                            min_pose_gap=treatment['minimum_candidate_pose_distance_gap'],
                            pose_tie_count=treatment['candidate_pose_tie_count'])
                        record=dict(**row,reference_trace=reference,treatment_trace=treatment)
                    except Exception as error:
                        row.update(status='error',error=f'{type(error).__name__}: {error}')
                        record=dict(row)
                    rows.append(row)
                    record_file.write(json.dumps(record)+'\n')
                    record_file.flush()
            print(f'Completed {name}: {len(rows)} paired configurations',flush=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (args.out/'pairs.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)
    summaries=[]
    for scenario,kind,level,scale in itertools.product(cfg['scenarios'],cfg['corruptions'],cfg['levels'],cfg['resolution_scales']):
        selected=[r for r in rows if r['scenario']==scenario and r['corruption']==kind and r['level']==level and r['scale']==scale]
        valid=[r for r in selected if r['status']=='ok']
        summaries.append(dict(scenario=scenario,corruption=kind,level=level,scale=scale,
            configurations=len(selected),errors=len(selected)-len(valid),
            changed_final_sets=sum(r['selected_set_changed'] for r in valid),
            changed_candidate_sets=sum(r['candidate_set_changed'] for r in valid),
            lower_reference_support=sum(r['reference_support_delta'] < -1e-12 for r in valid),
            mean_reference_support_delta=float(np.mean([r['reference_support_delta'] for r in valid])) if valid else None))
    (args.out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    sources=[ROOT/'src/vmem_retrieval_kernel.py',ROOT/'src/retrieval_diagnostic.py',Path(__file__),
             args.config,ROOT/'docs/S1_PROTOCOL.md',ROOT/'docs/S1_AUDIT_NOTES.md',ROOT/'requirements-retrieval.txt']
    hashes={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    metadata=dict(experiment_id=cfg['experiment_id'],started_utc=started,completed_utc=now(),
        elapsed_seconds=time.perf_counter()-tick,config=cfg,rows=len(rows),errors=sum(r['status']!='ok' for r in rows),
        torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,python=sys.version,
        platform=platform.platform(),device='cpu',source_sha256=hashes,
        selection_tensor_dtype='torch.float64',distance_sort_dtype=str(torch.get_default_dtype()),
        upstream_commit=json.loads((ROOT/'vendor/provenance.json').read_text())['commit'],
        evidence_type=cfg['evidence_type'],no_model_weights_loaded=True,no_real_images_used=True,
        dummy_contexts_only_for_return_packaging=True)
    (args.out/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (args.out/'status.json').write_text(json.dumps(dict(status='complete',rows=len(rows),errors=metadata['errors'],completed_utc=metadata['completed_utc']),indent=2)+'\n')
    print(json.dumps(dict(rows=len(rows),errors=metadata['errors'],seconds=metadata['elapsed_seconds'])))


if __name__=='__main__':
    main()
