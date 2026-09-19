#!/usr/bin/env python3
"""Artificial S17B verifier checks; no real image, checkpoint or prediction reads."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json
import numpy as np

root=Path(__file__).resolve().parents[2]
source=root/'scripts/verify_s17b_dpt_history.py'
out=root/'work/S17B_review/artificial_verifier_v1';out.mkdir(exist_ok=False)
started=datetime.now(timezone.utc).isoformat()
spec=importlib.util.spec_from_file_location('audit_under_test',source)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
checks=[]
def expect_failure(fn):
 try:fn()
 except (ValueError,AssertionError):return
 raise AssertionError('Expected invalid schema to fail')
head=np.zeros((1,384,512,3),np.float32)
mod.validate_array(head,mod.HEADS['rgb'],'float32','artificial RGB output')
expect_failure(lambda:mod.validate_array(head.transpose(0,2,1,3),mod.HEADS['rgb'],'float32','transposed wrong H/W'))
expect_failure(lambda:mod.validate_array(np.zeros((1,224,224,3),np.float32),mod.HEADS['rgb'],'float32','wrong legacy224'))
checks.append('384x512 BHWC accepted; transposed H/W and 224 square rejected')
enc=np.array([[1,2,3,1,0,0,0],[-1,.5,4,2,0,0,2]],np.float32)
got=mod.decode_poses_scipy(enc)
expected=np.repeat(np.eye(4)[None],2,axis=0)
expected[:,:3,3]=enc[:,:3];expected[1,:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]]
assert np.allclose(got,expected,rtol=0,atol=1e-14)
bad=enc.copy();bad[0,3:]=0
expect_failure(lambda:mod.decode_poses_scipy(bad))
bad=enc.copy();bad[0,0]=np.nan
expect_failure(lambda:mod.decode_poses_scipy(bad))
checks.append('Known identity and nonunit wxyz 90-degree-Z poses match; zero quaternion and nonfinite encoding rejected')
path=out/'artificial_two_members.npz'
values={'rgb':head,'pose':enc}
np.savez_compressed(path,**values)
schema={'rgb':((1,384,512,3),'float32'),'pose':((2,7),'float32')}
ids={k:mod.aid(v) for k,v in values.items()}
def check(ok,label):
 if not ok:raise AssertionError(label)
decoded=mod.inspect_npz(path,schema,ids,check)
assert all(np.array_equal(values[k],decoded[k]) for k in values)
badids={k:dict(v) for k,v in ids.items()};badids['rgb']['sha256']='0'*64
expect_failure(lambda:mod.inspect_npz(path,schema,badids,check))
checks.append('Bounded NPZ declarations, exact membership and contiguous-array hashes checked; changed identity rejected')
receipt=dict(status='PASS',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
             scope='Artificial verifier schema/pose checks only; not producer/model validation',
             checks=checks,real_image_reads=0,checkpoint_reads=0,real_npz_reads=0,
             verifier_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
