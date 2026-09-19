#!/usr/bin/env python3
"""Report all prespecified S8 comparisons without selecting favorable queries."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MAPS=['A0P0','A0P1','A1P0','A1P1']
READOUTS=['official','candidate_no_nms','all20_nms','all20_no_nms']
PAIRS={'P_at_A0':('A0P0','A0P1'),'P_at_A1':('A1P0','A1P1'),
       'A_at_P0':('A0P0','A1P0'),'A_at_P1':('A0P1','A1P1'),
       'diagonal':('A0P0','A1P1')}


def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def mean(xs):
    good=[x for x in xs if x is not None]
    return float(np.mean(good)) if good else None


def compare(a,b):
    ds=[y['support']-x['support'] for x,y in zip(a,b)]
    return dict(delta_pp=[100*d for d in ds], mean_delta_pp=100*mean(ds),
        increased=sum(d>1e-12 for d in ds), decreased=sum(d< -1e-12 for d in ds),
        unchanged=sum(abs(d)<=1e-12 for d in ds),
        selection_set_changed=sum(set(x['selected'])!=set(y['selected']) for x,y in zip(a,b)),
        ordered_selection_changed=sum(x['selected']!=y['selected'] for x,y in zip(a,b)),
        order_only_changed=sum(x['selected']!=y['selected'] and set(x['selected'])==set(y['selected']) for x,y in zip(a,b)))


def summarize(rows):
    official={m:[r['readouts'][m]['official'] for r in rows] for m in MAPS}
    contrasts={name:compare(official[a],official[b]) for name,(a,b) in PAIRS.items()}
    interaction=[b-a for a,b in zip(contrasts['P_at_A0']['delta_pp'],contrasts['P_at_A1']['delta_pp'])]
    checks=[]
    for r in (rows if rows[0]['stride']==12 else []):
        a,b,c=[r['readouts'][m]['official'] for m in ('A0P0','A1P0','A1P1')]
        ids=a['selected']==c['selected'] and a['selected']!=b['selected']
        support=abs(a['support']-c['support'])<=1e-12 and abs(a['support']-b['support'])>1e-12
        checks.append(dict(block=r['block'],frame=r['frame'],ordered_id_cancellation=ids,
                           support_cancellation=support,both=ids and support))
    return dict(query_ids=[[r['block'],r['frame']] for r in rows],queries=len(rows),
        support_percent={readout:{m:100*mean([r['readouts'][m][readout]['support'] for r in rows]) for m in MAPS} for readout in READOUTS},
        contrasts=contrasts, interaction=dict(delta_pp=interaction,mean_delta_pp=mean(interaction)),
        nms_removal={m:compare([r['readouts'][m]['official'] for r in rows],
                              [r['readouts'][m]['candidate_no_nms'] for r in rows]) for m in MAPS},
        all20_nms_removal=compare([r['readouts']['A0P0']['all20_nms'] for r in rows],
                                 [r['readouts']['A0P0']['all20_no_nms'] for r in rows]),
        concrete_S7_P_sign_pattern=(contrasts['P_at_A0']['mean_delta_pp']< -1e-10 and contrasts['P_at_A1']['mean_delta_pp']>1e-10) if rows[0]['stride']==8 else None,
        predefined_cancellation_path='A0P0 -> A1P0 -> A1P1' if rows[0]['stride']==12 else None,cancellation_checks=checks,
        simultaneous_id_and_support_cancellation_count=sum(c['both'] for c in checks) if rows[0]['stride']==12 else None,
        common_four_coverage_percent=100*mean([r['common_four_pixels']/r['valid_pixels'] for r in rows]),
        common_four_pixels=[r['common_four_pixels'] for r in rows],
        geometry={m:dict(common_four={key:mean([r['geometry'][m]['common_four'][key] for r in rows]) for key in ('mae_mm','median_abs_mm','p90_abs_mm')},
                          own={key:mean([r['geometry'][m]['own'][key] for r in rows]) for key in ('mae_mm','median_abs_mm','p90_abs_mm')},
                          diagonal={key:mean([r['geometry'][m]['common_diagonal'][key] for r in rows]) for key in ('mae_mm','median_abs_mm','p90_abs_mm')} if m in ('A0P0','A1P1') else None,
                          zero_common_queries=sum(r['common_four_pixels']==0 for r in rows),
                          zero_own_queries=sum(r['geometry'][m]['own']['n']==0 for r in rows),
                          own_coverage_percent=100*mean([r['geometry'][m]['coverage'] for r in rows])) for m in MAPS})


def run(args):
    if args.output.exists():raise ValueError('Use fresh analysis output')
    meta=read(args.results/'run_metadata.json')
    if meta['status']!='completed':raise ValueError('S8 run incomplete')
    records=read(args.results/'records.json')
    assert len(records)==24 and all(r['split']=='test' for r in records)
    assert len({(r['block'],r['frame']) for r in records})==12
    args.output.mkdir(parents=True)
    summary=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        evidence='one additional physical scene; 12 correlated queries; component support, not video quality',
        source_sha256={str(args.results/'records.json'):sha(args.results/'records.json'),str(Path(__file__)):sha(__file__)},
        per_stride={})
    csvrows=[]
    for stride in (8,12):
        rows=sorted([r for r in records if r['stride']==stride],key=lambda r:(r['block'],r['frame']))
        assert len(rows)==12
        summary['per_stride'][str(stride)]={'all':summarize(rows),
            'blocks':{str(b):summarize([r for r in rows if r['block']==b]) for b in range(3)}}
        for r in rows:
            for m in MAPS:
                for readout in READOUTS:
                    v=r['readouts'][m][readout]
                    csvrows.append(dict(block=r['block'],frame=r['frame'],stride=stride,map=m,readout=readout,
                        selected=' '.join(map(str,v['selected'])),supported_pixels=v['supported_pixels'],
                        valid_pixels=r['valid_pixels'],support_percent=100*v['support']))
    with (args.output/'all_384_readouts.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
    write(args.output/'summary.json',summary)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
    colors=['#475569','#0891b2','#d97706','#7c3aed']
    for ax,stride in zip(axes,(8,12)):
        g=summary['per_stride'][str(stride)]['all']
        vals=[g['support_percent']['official'][m] for m in MAPS]
        ax.bar(MAPS,vals,color=colors,width=.64)
        ax.set_ylim(0,100);ax.set_ylabel('Measured reference support (%)')
        ax.set_title(f'fr2/desk: stride {stride} | 12 test queries')
        for i,v in enumerate(vals):ax.text(i,v+1.3,f'{v:.2f}',ha='center',fontsize=10)
        ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    for ext in ('png','svg'):fig.savefig(args.output/f'external_scene_support.{ext}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
    for ax,stride in zip(axes,(8,12)):
        g=summary['per_stride'][str(stride)]['all']
        for name,color in zip(('P_at_A0','P_at_A1'),('#0891b2','#7c3aed')):
            ax.plot(range(12),g['contrasts'][name]['delta_pp'],'o-',label=name.replace('_',' '),color=color,ms=4)
        ax.axhline(0,color='#64748b',lw=.7)
        for x in (3.5,7.5):ax.axvline(x,color='#94a3b8',ls=':',lw=.8)
        ax.set_xticks(range(12),[f'B{b}Q{q}' for b,q in g['query_ids']],rotation=60,ha='right',fontsize=8)
        ax.set_ylabel('Position-rule support change (percentage points)')
        ax.set_title(f'All preselected queries | stride {stride}');ax.legend(fontsize=9)
    for ext in ('png','svg'):fig.savefig(args.output/f'per_query_position_effects.{ext}',dpi=180)
    plt.close(fig)
    print(json.dumps({s:summary['per_stride'][s]['all']['support_percent']['official'] for s in ('8','12')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args())
