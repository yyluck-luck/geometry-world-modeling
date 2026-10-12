"""Apply explicit, guarded edits to the byte-pinned S141 generator copy."""
import hashlib
import os
from pathlib import Path

here = Path(__file__).resolve().parent
path = here / 'upstream_gen_s141.py'
assert hashlib.sha256(path.read_bytes()).hexdigest() == 'c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121'
arm = os.environ['P2_ARM']
assert arm in ('native', 'real', 'zero', 'permuted', 'low_cfg')
assert os.environ['VARIANT'] == 'A'
source = path.read_text()

def replace(old, new, count):
    global source
    assert source.count(old) == count, (old, source.count(old))
    source = source.replace(old, new)

replace('from PIL import Image', 'from PIL import Image\nfrom p2_intervention import P2Denoiser, capture_initial_noise', 1)
replace("CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)",
        "CFG_MIN = float(cfg.model.cfg_min); GUIDER = int(cfg.model.guider_types)\nif os.environ['P2_ARM'] == 'low_cfg': CFG = CFG_MIN = 1.2", 1)
old = 'den = DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device)'
replace(old, "den = P2Denoiser(DiscreteDenoiser(DDPMDiscretization(), num_idx=1000, device=device), lat, os.environ['P2_ARM'], P2_TRACE_FILE)", 2)
replace("cfg_min=CFG_MIN, device=device)[0]", "cfg_min=CFG_MIN, device=device)[0]\n        capture_initial_noise(sampler, den)", 2)
replace("return outs[0][4:].detach().float().cpu().numpy()", "den.save()\n    return outs[0][4:].detach().float().cpu().numpy()", 2)
replace("ts = time.time()", "P2_TRACE_FILE = OUT / f\"{c['ctx_key']}__s{seed}.trace.json\"\n    ts = time.time()", 1)
exec(compile(source, str(path), 'exec'), {'__name__': '__main__', '__file__': str(path)})
