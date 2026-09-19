#!/usr/bin/env python3
"""Different-author artificial scalar checks; no real input files or entrypoint run."""
from pathlib import Path
import hashlib, importlib.util, json, math, datetime
from fractions import Fraction
import numpy as np
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
SRC=ROOT/'scripts/measure_s14c_selection_disagreement.py'
source_bytes=SRC.read_bytes()
spec=importlib.util.spec_from_file_location('s14c_review_target',SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
checks=[]
def check(name, actual, expected, atol=1e-12):
    if isinstance(expected, (float,int)) and not isinstance(expected,bool):
        ok=math.isclose(float(actual),float(expected),abs_tol=atol,rel_tol=1e-10)
    else:
        ok=actual==expected
    checks.append(dict(name=name, actual=actual, expected=expected, passed=bool(ok)))
    assert ok, name
def point(coords, radius=2):
    return dict(radius=radius,m=len(coords),frames={i:dict(xyz=np.array(x,dtype=np.float64),n_obs=1)
                                                  for i,x in coords.items()})
meta=dict(stage='S7',block=0,query=20,split='development',arm='A0P0',stride=8)
allcoords={0:(0,0,0),1:(2,0,0),2:(0,2,0),3:(2,2,0),4:(1,1,0),5:(7,0,0)}
g=dict(selected=[0,1,2,3],candidates=list(range(14)),ranked_candidates=list(range(14)),camera_pair=2.,query_distance=5.)
p=dict(selected=[0,1,4,5],candidates=list(range(14)),ranked_candidates=list(range(14)),camera_pair=7.,query_distance=3.)
points={0:point(allcoords),1:point({0:(0,0,0),1:(2,0,0)}),
        2:point({2:(0,0,0),3:(2,0,0)})}
# Hand-derived pair sums: G=32/(6*4), P=119/(6*4) at point0; point1=1.
row, detail=mod.measure_query(meta,points,g,p)
check('two common points',row['common_points'],2)
check('full map denominator',row['common_fraction'],float(Fraction(2,3)))
check('G common denominator',row['common_fraction_of_g'],float(Fraction(2,3)))
check('P common denominator',row['common_fraction_of_p'],1.)
check('frame pair then point mean G',row['disagreement_g'],float(Fraction(7,6)))
check('frame pair then point mean P',row['disagreement_p'],float(Fraction(143,48)))
check('signed primary',row['disagreement_g_minus_p'],float(Fraction(-29,16)))
check('camera baseline fixed P-G',row['camera_pair_p_minus_g'],5.)
check('query baseline fixed G-P',row['query_distance_g_minus_p'],2.)
check('source difference equal counts',row['source_count_p_minus_g'],0.)
check('all25 cells',len(detail['source_count_grid']),25)
check('all25 sum',sum(c['n_points'] for c in detail['source_count_grid']),3)
same, _=mod.measure_query(meta,points,g,g)
check('identical choices exact zero',same['disagreement_g_minus_p'],0.,0)
check('identical choice flag',same['same_selected_set'],True)
empty,_=mod.measure_query(meta,{0:point({2:(0,0,0),3:(2,0,0)})},g,p)
check('no common is null',empty['disagreement_g_minus_p'],None)
check('no common source is null',empty['source_count_p_minus_g'],None)
check('no common status',empty['status'],'NO_COMMON_MULTISOURCE_POINTS')
check('no common P denominator null',empty['common_fraction_of_p'],None)
# Non-uniform k exposes point vs pooled-pair weighting; point0 kG4,kP2.
newpoints={0:point({0:(0,0,0),1:(2,0,0),2:(0,2,0),3:(2,2,0)}),
           1:point({0:(0,0,0),1:(2,0,0)})}
unequal,_=mod.measure_query(meta,newpoints,g,p)
check('unequal source baseline',unequal['source_count_p_minus_g'],-1.)
check('unequal pair point weights',unequal['disagreement_g_minus_p'],float(Fraction(1,6)))
check('rank ties midpoint',mod.tied_ranks([5,1,1,9]).tolist(),[3.,1.5,1.5,4.])
check('spearman preserved negative sign',mod.spearman([1,2,3,4],[4,3,2,1])['rho'],-1.)
check('ties perfect rank correlation',mod.spearman([1,1,4,9],[5,5,7,10])['rho'],1.)
check('constant null',mod.spearman([2,2,2],[1,2,3])['rho'],None)
check('two only null',mod.spearman([1,2],[1,2])['rho'],None)
check('all missing null',mod.spearman([None,None,None],[1,2,3])['rho'],None)
assert SRC.read_bytes()==source_bytes, 'Source changed during checks'
out=dict(schema='s14c-independent-scalar-pre-review-v1',status='PASS',
         started_utc=started,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         source_sha256=hashlib.sha256(source_bytes).hexdigest(),
         checks=checks,check_count=len(checks),
         real_input_files_read=0,real_arrays_decoded=0,score_files_read=0,
         production_entrypoint_runs=0,scope='Artificial pure function checks by design/pre-review author; not real experiment.')
dest=ROOT/'work/S14C_pre_run_review/scalar_check_receipt.json'
with dest.open('x') as f: json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:out[k] for k in ('status','source_sha256','check_count','completed_utc')}))

