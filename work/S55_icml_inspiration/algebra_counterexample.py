"""Exact scalar illustrations; no model, array or image access."""
from datetime import datetime, timezone
from pathlib import Path
import json
import platform

started = datetime.now(timezone.utc).isoformat()
arms = [(0, 0), (1, 0), (0, 1), (1, 1)]
rows = [dict(a=a, b=b, additive=a+b, nonlinear_output=(a+b)**2,
             cancellation=a-b) for a,b in arms]
def contrast(key):
    v = {(r['a'],r['b']):r[key] for r in rows}
    return v[(1,1)]-v[(1,0)]-v[(0,1)]+v[(0,0)]
result = dict(
    kind='EXACT_SCALAR_ALGEBRA_NOT_MODEL_EXPERIMENT',
    started_at=started, completed_at=datetime.now(timezone.utc).isoformat(),
    python=platform.python_version(), rows=rows,
    contrasts={k:contrast(k) for k in ('additive','nonlinear_output','cancellation')},
    model_runs=0, real_data_bodies_read=0, new_theorem=False,
    conclusion='A nonzero final-output factorial contrast need not localize interaction to the additive intermediate; zero factorial contrast does not rule out linear cancellation.')
assert result['contrasts'] == dict(additive=0, nonlinear_output=2, cancellation=0)
Path(__file__).with_name('ALGEBRA_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
