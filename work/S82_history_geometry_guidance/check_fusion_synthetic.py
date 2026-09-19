"""Bounded artificial tensor checks; no production sampler/model/data runs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import torch
from latent_geometry_guidance import fuse_clean_prediction


def main():
    directory = Path(__file__).resolve().parent
    destination = directory/'SYNTHETIC_FUSION_CHECK.json'
    if destination.exists():
        raise FileExistsError('Preserve the previous check; no automatic repeat')
    start = time.monotonic();started = datetime.now(timezone.utc).isoformat()
    x = torch.arange(64, dtype=torch.float32).reshape(4,2,2,4)
    x[0,0,0,0] = -0.0
    warp = torch.full_like(x, -2)
    mask = torch.ones((4,1,2,4), dtype=torch.float32)
    mask[2,0,0,0] = 0
    mask[3,0,1,2] = .5
    history = torch.tensor([True,True,False,False])
    original = x.numpy().tobytes()
    rng_before = torch.get_rng_state().numpy().tobytes()
    checks = []

    def check(name, passed):
        checks.append(dict(name=name,passed=bool(passed)))
        assert passed, name

    check('zero_strength_same_object', fuse_clean_prediction(x,warp,mask,history,0) is x)
    check('zero_mask_same_object', fuse_clean_prediction(x,warp,torch.zeros_like(mask),history,.5) is x)
    check('all_history_same_object', fuse_clean_prediction(x,warp,mask,torch.ones_like(history),1) is x)
    out = fuse_clean_prediction(x,warp,mask,history,.5)
    check('input_bytes_unchanged', x.numpy().tobytes()==original)
    check('history_bytes_exact', out[:2].numpy().tobytes()==x[:2].numpy().tobytes())
    check('zero_support_exact', out[2,0,0,0].item()==x[2,0,0,0].item())
    check('full_support_half_blend', out[2,0,0,1].item()==(x[2,0,0,1].item()-2)/2)
    check('soft_support_quarter_blend', out[3,1,1,2].item()==.75*x[3,1,1,2].item()-.5)
    check('full_strength_target_equals_warp', fuse_clean_prediction(x,warp,mask,history,1)[2,0,0,1].item()==-2)
    bad = [('negative_strength',(x,warp,mask,history,-.1)),
           ('nan_strength',(x,warp,mask,history,float('nan'))),
           ('wrong_shape',(x,warp[:1],mask,history,.5)),
           ('wrong_dtype',(x,warp.double(),mask,history,.5)),
           ('wrong_history_dtype',(x,warp,mask,history.float(),.5)),
           ('mask_out_of_range',(x,warp,mask+1,history,.5)),
           ('nonfinite_warp',(x,warp*float('nan'),mask,history,.5))]
    for name, args in bad:
        rejected = False
        try:
            fuse_clean_prediction(*args)
        except (ValueError,TypeError):
            rejected=True
        check(name+'_rejected', rejected)
    check('rng_bytes_unchanged', torch.get_rng_state().numpy().tobytes()==rng_before)
    result = dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
                  wall_seconds=time.monotonic()-start,checks=checks,status='PASS_ARTIFICIAL_TENSOR_ONLY',
                  source_sha256=hashlib.sha256((directory/'latent_geometry_guidance.py').read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  torch_version=torch.__version__,dtype='float32',device='cpu',
                  provenance='Author tests of isolated pure function; no real RGB/depth/NPZ/weights or model forward. No sampler integration or actual generation.',
                  new_method_validated=False)
    with destination.open('x') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','wall_seconds','source_sha256']}))


if __name__=='__main__':
    main()
