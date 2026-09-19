"""Exact rational checks of Euler fusion identities; artificial inputs only."""
from fractions import Fraction as F
from datetime import datetime, timezone
import json
from pathlib import Path

def step(x, d, sigma_hat, next_sigma):
    return x + (next_sigma-sigma_hat)*(x-d)/sigma_hat

def blend(d, g, w):
    return (1-w)*d+w*g

started=datetime.now(timezone.utc).isoformat()
x,d,g,w,sh=map(F,[10,4,8,"1/4",2])
a=[]
for sn,expected_delta in [(F(1),F("1/2")),(F(0),F(1))]:
    base=step(x,d,sh,sn);guided=step(x,blend(d,g,w),sh,sn)
    derived=(1-sn/sh)*w*(g-d)
    assert guided-base==derived==expected_delta
    if sn==0:assert guided==blend(d,g,w)==5
    assert step(x,blend(d,g,F(0)),sh,sn)==base
    a.append(dict(next_sigma=str(sn),base=str(base),guided=str(guided),delta=str(derived)))
# An artificial two-step denoiser d(x)=x/2 shows why entire trajectories differ.
x=F(8);g=F(0);w=F("1/2")
base_1=step(x,x/2,F(2),F(1));base_d2=base_1/2
terminal_only=blend(base_d2,g,w)
guide_1=step(x,blend(x/2,g,w),F(2),F(1))
guide_2=step(guide_1,blend(guide_1/2,g,w),F(1),F(0))
assert base_1==6 and base_d2==3 and terminal_only==F("3/2")
assert guide_1==5 and guide_2==F("5/4") and guide_2!=terminal_only
out=dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
         status="PASS_EXACT_RATIONAL_ARTIFICIAL_CHECKS",same_step=a,
         two_step=dict(base_final=str(base_d2),terminal_only=str(terminal_only),all_steps=str(guide_2)),
         scientific_model_calls=0,real_arrays_read=0,
         limitation="Artificial exact rationals with x already noise-perturbed; not a floating-point sampler integration or a real denoiser experiment.")
p=Path(__file__).with_name("TERMINAL_BLEND_MATH_CHECK.json")
with p.open("x") as f:json.dump(out,f,indent=2);f.write("\n")
print(json.dumps(out))
