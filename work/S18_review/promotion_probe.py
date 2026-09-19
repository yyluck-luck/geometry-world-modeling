#!/usr/bin/env python3
"""Additional scalar expressions requested by independent verifier; artificial only."""
from datetime import datetime, timezone
import hashlib,json
from pathlib import Path
import numpy as np
def utc(): return datetime.now(timezone.utc).isoformat()
start=utc(); checks=[]; observations={}
def check(name,passed):
 checks.append(dict(name=name,passed=bool(passed)))
 if not passed: raise AssertionError(name)
def scalar(v):return dict(type=type(v).__name__,value=float(v))
check('numpy126',np.__version__=='1.26.4')
a=np.array([0.,0.,1.],np.float32);b=np.array([.8,0.,.6],np.float32)
dot=np.dot(a,b)
observations['strict_dot']={'dot':scalar(dot),'python_threshold':.6,'passes':bool(dot>.6)}
check('FP32 dot .6 literal is above Python double .6',dot>.6)
radii=np.array([np.float32(.03),np.float32(.11),np.float32(.23)],dtype=np.float32)
mean=np.mean(radii);std=np.std(radii);halfstd=.5*std;threshold=mean+halfstd
observations['threshold']={k:scalar(v) for k,v in [('mean',mean),('std',std),('halfstd',halfstd),('threshold',threshold)]}
check('radius reduction FP32 then promoted addition',type(mean) is np.float32 and type(std) is np.float32 and type(threshold) is np.float64)
cos=np.float32(.7);depth=np.float32(.3);denom=1+depth;weight=cos/denom
observations['vote']={k:scalar(v) for k,v in [('cos',cos),('depth',depth),('denominator',denom),('contribution',weight)]}
check('vote denominator and contribution promote to FP64',type(denom) is np.float64 and type(weight) is np.float64)
report=dict(schema='s18-third-author-scalar-promotion-v1',status='PASS_ARTIFICIAL_ONLY',started_utc=start,completed_utc=utc(),
 source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),numpy=np.__version__,checks=checks,observations=observations,
 model_calls=0,archived_npz_reads=0,rgb_reads=0,gt_reads=0)
Path(__file__).with_name('promotion_probe_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
