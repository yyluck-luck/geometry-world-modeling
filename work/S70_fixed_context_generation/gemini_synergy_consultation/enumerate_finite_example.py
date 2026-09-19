"""Exact finite probability arithmetic; no video, model or research data."""
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,time

d=Path(__file__).resolve().parent
started=datetime.now(timezone.utc).isoformat(); tick=time.monotonic()
states=[]
for a,b,e in product((0,1),repeat=3):
    y=a^b; x=(a,b,y^e)
    p=F(1,4)*(F(4,5) if e==0 else F(1,5))
    states.append((x,y,p))
assert sum(p for _,_,p in states)==1
rows=[]
for k in range(4):
    for idx in combinations(range(3),k):
        joint=defaultdict(lambda:F(0)); px=defaultdict(lambda:F(0)); py=defaultdict(lambda:F(0))
        for x,y,p in states:
            obs=tuple(x[i] for i in idx)
            joint[(obs,y)]+=p;px[obs]+=p;py[y]+=p
        risk=sum(min(joint[(obs,0)],joint[(obs,1)]) for obs in px)
        info=sum(float(p)*math.log2(float(p/(px[obs]*py[y]))) for (obs,y),p in list(joint.items()) if p)
        rows.append({'indices':[i+1 for i in idx],'bayes_zero_one_risk_exact':str(risk),'mutual_information_bits_float':info})
lookup={tuple(row['indices']):row for row in rows}
assert lookup[(1,2)]['bayes_zero_one_risk_exact']=='0'
assert lookup[(1,3)]['bayes_zero_one_risk_exact']==lookup[(2,3)]['bayes_zero_one_risk_exact']=='1/5'
assert lookup[(1,)]['bayes_zero_one_risk_exact']==lookup[(2,)]['bayes_zero_one_risk_exact']=='1/2'
# Ordinary Gaussian redundancy control, analytic conjugate precision arithmetic.
# Y~N(0,1), X1=X2=Y+e1, Var(e1)=1, X3=Y+e3, Var(e3)=2; independent noises.
gaussian={'duplicate_pair_mse_exact':str(1/(F(1)+F(1))),
          'independent_pair_mse_exact':str(1/(F(1)+F(1)+F(1,2))),
          'single_I_X1_bits':.5*math.log2(2),
          'single_I_X3_bits':.5*math.log2(1.5),
          'joint_I_X1_X3_bits':.5*math.log2(2.5),
          'joint_minus_sum_single_bits':.5*math.log2(2.5)-.5*math.log2(2)-.5*math.log2(1.5)}
report={'status':'PASS_FINITE_PROBABILITY_ARITHMETIC_ONLY','started_utc':started,
        'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'enumerated_states':8,'rows':rows,'ordinary_gaussian_analytic_control':gaussian,
        'scope':'Exact finite-state risks; floating log2 for information. Gaussian formulas algebraic, not simulation or fitted data.',
        'real_video_frames_read':0,'model_runs':0,'new_method_validated':False}
with (d/'FINITE_ARITHMETIC_RECEIPT.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report))
