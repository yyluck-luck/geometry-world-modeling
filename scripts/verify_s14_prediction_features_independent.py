#!/usr/bin/env python3
"""Independent NumPy recomputation of frozen S14A unlabeled JSON features.

This verifier does not import the extractor and never opens scoring/GT/NPZ.
It is authored by the root reviewer, distinct from the extractor author.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, json, math, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())


def main(result, output):
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(),status='running',
                   role='root verifier distinct from feature extractor author',
                   scope='unlabeled saved JSON only; no scoring, model, new selection or predictive value test',
                   float_atol=1e-12,integer_id_saved_gap_tolerance=0,
                   environment=dict(python=sys.version,numpy=np.__version__,executable=sys.executable))
    try:
        meta = read(result/'run_metadata.json')
        assert meta['status'] == 'completed'
        manifest = read(result/'frozen_manifest.json')
        assert sha(result/'frozen_manifest.json') == meta['manifest_sha256'] == meta['manifest_sha256_after']
        assert sha(result/'extractor_snapshot.py') == meta['extractor_sha256'] == meta['extractor_sha256_after']
        declared={x['path']:x['sha256'] for x in manifest['inputs']}
        expect=set()
        for st in ('S7','S8'):
            folder='S7_event_replay' if st=='S7' else 'S8_event_replay_v2'
            for b in range(3):
                expect.add(f'results/{folder}/block{b}_stride8/prediction_only_selection.json')
                expect.update(f'results/S12_matched_budget/selections/{st}_block{b}_query{q}.json' for q in range(20,24))
        assert set(declared)==expect and len(manifest['inputs'])==30
        assert all(sha(ROOT/p)==h for p,h in declared.items())
        docs={p:read(ROOT/p) for p in sorted(expect)}
        saved=read(result/'features.json');lineage=read(result/'row_provenance.json')
        rows=saved['rows']; cols=saved['feature_columns']
        csvrows=list(csv.DictReader((result/'features.csv').open()))
        assert len(rows)==len(csvrows)==len(lineage)==24 and len(cols)==15
        assert tuple(cols)==('candidate_intersection_count','candidate_jaccard','selected_intersection_count','selected_jaccard','source_weight_hhi','source_weight_max_share','source_weight_normalized_entropy','source_weight_gap_14_15_raw','pose_query_distance_gap_14_15_f32','source_selected_query_distance_mean_f32','pose_selected_query_distance_mean_f32','source_selected_pair_distance_mean_f64','source_selected_pair_distance_min_f64','pose_selected_pair_distance_mean_f64','pose_selected_pair_distance_min_f64')
        diffs=[];pair_uses=0
        keys=set()
        for i,row in enumerate(rows):
            st,b,q=row['stage'],row['block'],row['query'];keys.add((st,b,q))
            folder='S7_event_replay' if st=='S7' else 'S8_event_replay_v2'
            sp=f'results/{folder}/block{b}_stride8/prediction_only_selection.json'
            pp=f'results/S12_matched_budget/selections/{st}_block{b}_query{q}.json'
            sd=docs[sp];pd=docs[pp]
            source=next(x for x in sd['queries'] if x['frame']==q)['maps']['A0P0']
            off=source['official_trace'];gt=source['readouts']['official'];pt=pd['trace']
            split='development' if (st,b)==('S7',0) else 'test'
            assert (row['split'],row['arm'],row['stride'])==(split,'A0P0',8)
            assert lineage[i]['source_path']==sp and lineage[i]['pose_path']==pp
            assert lineage[i]['source_sha256']==declared[sp] and lineage[i]['pose_sha256']==declared[pp]
            cg,cp=set(off['candidates']),set(pd['pose14_ranked_candidates'])
            sg,ps=set(gt['selected']),set(pt['selected'])
            assert len(cg)==len(cp)==14 and len(sg)==len(ps)==4
            w=np.array([x[1] for x in off['weights']],dtype=np.float64)
            assert w.size==20 and np.isfinite(w).all() and (w>=0).all() and w.sum()>0
            p=w/w.sum();nz=p[p>0]
            ws=np.sort(w.astype(np.float32))[::-1]
            gap=float(np.subtract(ws[13],ws[14],dtype=np.float32))
            assert gap==off['cutoff_gap_14_15']
            ds={int(k):float(v) for k,v in zip(pd['full20_frame_order'],pd['full20_distances_float32'])}
            ordered=sorted(ds.values())
            metrics=[len(cg&cp),len(cg&cp)/len(cg|cp),len(sg&ps),len(sg&ps)/len(sg|ps),
                     float(np.dot(p,p)),float(p.max()),float(-np.dot(nz,np.log(nz))/np.log(20)),gap,
                     ordered[14]-ordered[13],float(np.mean([ds[k] for k in sg])),float(np.mean([ds[k] for k in ps]))]
            for tr,tag in [(gt,'source'),(pt,'pose')]:
                selected=tr['selected'];pair_map={};locations={}
                for index,step in enumerate(tr['steps']):
                    if step.get('accepted') is True:
                        frame=step['frame']
                        assert frame in selected[1:]
                        pos=selected.index(frame)
                        assert [x[0] for x in step['comparisons']]==selected[:pos]
                        for ci,(other,distance) in enumerate(step['comparisons']):
                            key=tuple(sorted((frame,other)))
                            assert key not in pair_map
                            pair_map[key]=distance;locations[key]=(index,ci)
                assert set(pair_map)=={tuple(sorted((a,bb))) for a in selected for bb in selected if a<bb}
                assert len(pair_map)==6
                a=np.array(list(pair_map.values()),dtype=np.float64)
                assert np.isfinite(a).all()
                metrics.extend((float(a.mean()),float(a.min())))
                for item in lineage[i][tag+'_pair_provenance']:
                    key=tuple(item['pair'])
                    assert item['saved_distance']==pair_map[key]
                    assert (item['step_index'],item['comparison_index'])==locations[key]
                assert len(lineage[i][tag+'_pair_provenance'])==6
                pair_uses+=6
            for col,value in zip(cols,metrics):
                difference=abs(row[col]-value)
                assert math.isfinite(value) and difference<=1e-12
                if col in (cols[0],cols[2],cols[7]):assert row[col]==value
                assert float(csvrows[i][col])==row[col]
                diffs.append(dict(stage=st,block=b,query=q,column=col,difference=difference))
            for k in saved['metadata_columns']:assert csvrows[i][k]==str(row[k])
        assert keys=={(s,b,q) for s in ('S7','S8') for b in range(3) for q in range(20,24)}
        assert pair_uses==288
        assert all(sha(ROOT/p)==h for p,h in declared.items())
        assert all(sha(result/p)==h for p,h in meta['output_sha256'].items())
        receipt.update(status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),
                       actual_json_inputs=30,actual_queries=24,feature_values_recomputed=len(diffs),
                       pair_uses_checked=pair_uses,max_difference=max(d['difference'] for d in diffs),
                       inputs_unchanged=True,production_imports=False,
                       verifier_sha256=sha(Path(__file__)),run_metadata_sha256=sha(result/'run_metadata.json'))
        (output/'differences.json').write_text(json.dumps(diffs,indent=2)+'\n')
    except Exception as e:
        receipt.update(status='FAILED',completed_utc=datetime.now(timezone.utc).isoformat(),error=repr(e))
        raise
    finally:
        (output/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.result,a.output)
