"""Reproducible artificial-only S16 independent-verifier preparation checks."""
from pathlib import Path
import sys,json,hashlib,itertools
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_s16_interference as v
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name)
old=np.full((4,4,1,3),2.);new=old.copy()
ids=np.stack([np.broadcast_to(i*v.PIXELS+np.arange(3),(4,1,3)) for i in range(4)]).copy();newids=ids.copy()
old[0,:,:,0]=1.3;new[0,:,:,0]=.9;new[1,:,:,0]=.5
old[0,:,:,1]=new[0,:,:,1]=1.;newids[0,:,:,1]+=13
old[0,:,:,2]=0;ids[0,:,:,2]=-1;new[0,:,:,2]=1.
result,maps,invariants=v.diagnose_independent(old,new,ids,newids,1.,np.ones((4,1,3)))
check('10 unique selected subsets include all leave-one-out',len(v.SUBSETS)==len(set(v.SUBSETS))==10 and set(v.SUBSETS)=={0,1,2,4,8,15,14,13,11,7})
check('fixed/routing/coverage classes independently assigned',maps['fixed_candidates_depth_competition'][0,0].tolist()==[True,False,False] and maps['source_pixel_routing'][0,0].tolist()==[False,True,False] and maps['coverage_change'][0,0].tolist()==[False,False,True])
check('negative joint-minus-single interaction',result['interaction_correct_counts']==[-1]*4)
check('three integer class contributions recover total',result['components'][0]['interaction_correct_count_contribution']==[-1]*4 and result['components'][1]['interaction_correct_count_contribution']==[0]*4 and result['components'][2]['interaction_correct_count_contribution']==[0]*4)
check('frozen owner pointwise zero identity',invariants['frozen_interaction_nonzero']==0 and result['frozen_owner_exact_zero'])
check('solo means source alone',result['marginals'][0]['solo_old_correct_counts']==[1]*4 and result['marginals'][0]['solo_new_correct_counts']==[3]*4)
check('all frozen subset counts and means materialized',len(result['frozen_owner_subsets'])==10 and all('equal_four_frame_delta1' in x for x in result['frozen_owner_subsets']))
old=np.full((4,4,1,2),3.);new=old.copy();ids=np.stack([np.broadcast_to(i*v.PIXELS+np.arange(2),(4,1,2)) for i in range(4)]).copy()
old[0]=[1.4,.9];new[0]=[.9,1.4];old[1]=[2.,.7];new[1]=[.7,2.]
result,maps,invariants=v.diagnose_independent(old,new,ids,ids,1.,np.ones((4,1,2)))
check('aggregate sign reversal fixture',result['marginals'][0]['single_correct_delta']==[1]*4 and result['marginals'][0]['joint_marginal_correct_delta']==[-1]*4 and result['marginals'][0]['mean_sign_reversal'])
check('aggregate reversal without pointwise reversal',not any(invariants['pixel_marginal_sign_reversals']))
values=[0.,.5,.8,.9,1.,1.25,1.5,2.]
def compose(a,c):return 0. if a==c==0. else min(a if a>0 else float('inf'),c if c>0 else float('inf'))
def hit(x):return int(x>0 and max(x,1/x)<1.25)
count=0
for a,b,c,d in itertools.product(values,repeat=4):
    first=hit(compose(b,c))-hit(compose(a,c));second=hit(compose(b,d))-hit(compose(a,d))
    assert first*second>=0
    count+=1
check('4096 scalar no-pointwise-reversal cases',count==4096)
r=dict(status='PASS',completed_utc=v.utc(),artificial_checks=checks,check_count=len(checks),exhaustive_scalar_cases=4096,
    real_array_decodes=0,real_png_decodes=0,model_calls=0,script_sha256=hashlib.sha256(Path(v.__file__).read_bytes()).hexdigest(),helper_sha256=v.HELPER_SHA)
p=Path(__file__).resolve().parent/'receipt_v2.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['status','check_count','script_sha256']}))
