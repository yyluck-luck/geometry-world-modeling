#!/usr/bin/env python3
"""Artificial official-state-method check. No checkpoint/model/image/GT reads."""
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch

root=Path(__file__).resolve().parents[2]
started=datetime.now(timezone.utc).isoformat()
source=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/model.py')
vp=root/'scripts/verify_s17b_dpt_history_v2.py'
spec=importlib.util.spec_from_file_location('corrected_verifier',vp);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='_encode_state')
ns={'torch':torch};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
checks=[]
torch.set_num_threads(1)
for size,width in [(768,28),(324,18),(25,6),(16,4)]:
    fake=SimpleNamespace(state_size=size,state_pe='2d',register_tokens=lambda x:torch.zeros((len(x),1)))
    _,actual,_=ns['_encode_state'](fake,torch.zeros((1,1,1)),torch.zeros((1,1,2),dtype=torch.int64))
    independent,w=v.state_positions_even_width(size)
    assert w==width and np.array_equal(independent,actual.numpy())
    checks.append(dict(state_size=size,expected_width=width,last=independent[0,-1].tolist(),passed=True))
wrong=np.array([[i//27,i%27] for i in range(768)],dtype=np.int64)[None]
assert not np.array_equal(wrong,v.state_positions_even_width(768)[0])
constructed="instantiating : ARCroco3DStereo(ARCroco3DStereoConfig(state_size=768,state_pe='2d'))"
assert v.state_configuration_from_load_text(constructed)==dict(state_size=768,state_pe='2d')
try:v.state_configuration_from_load_text("instantiating : ARCroco3DStereo(ARCroco3DStereoConfig(state_size=768))")
except ValueError:pass
else:raise AssertionError('missing state_pe accepted')
receipt=dict(schema='s17b-even-grid-artificial-correction-v1',status='PASS_ARTIFICIAL_ONLY',started_utc=started,
             completed_utc=datetime.now(timezone.utc).isoformat(),checks=checks,old27_rule_rejected=True,
             missing_explicit_configuration_rejected=True,verifier_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
             official_model_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             checkpoint_reads=0,real_image_reads=0,gt_reads=0,model_instances=0,model_forward_calls=0,
             note='Extracted only official _encode_state with a one-feature zero callback; four tiny artificial state sizes.')
out=Path(__file__).with_name('artificial_receipt.json');assert not out.exists();out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'verifier_sha256':receipt['verifier_sha256'],'receipt':str(out)}))
