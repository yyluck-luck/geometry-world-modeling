"""Read only five already recorded geometry-output depth blobs, never colors."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import numpy as np

R = Path(__file__).resolve().parents[2]
A = R / 'results/S47B_C2_confirmation_generation_v9/archive'
D = Path(__file__).resolve().parent
OUT = D / 'ALL_FIVE_SAVED_DEPTHS.json'
assert not OUT.exists()
start = datetime.now(timezone.utc).isoformat()
body = (A / 'events.jsonl').read_bytes()
assert hashlib.sha256(body).hexdigest() == 'b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7'
events = {v['seq']: v for v in map(json.loads, body.splitlines())}
assert events[48]['payload']['name'] == 'geometry_output'

def field(node, name):
    assert node['kind'] == 'dict'
    matches = [v['value'] for v in node['items'] if v['key']['value'] == name]
    assert len(matches) == 1
    return matches[0]

depths = field(field(events[48]['payload']['tree'], 'scene'), 'depths')
assert depths['kind'] == 'list' and len(depths['items']) == 5
rows = []
prior = json.loads((R / 'work/S60_renderer_unit_replay/execution_01/receipt.json').read_text())['read_numeric_blobs']
for i, desc in enumerate(depths['items']):
    assert desc['kind'] == 'tensor' and desc['dtype'] == 'float32'
    assert desc['shape'] == [1, 384, 512] and desc['nbytes'] == 786432
    p = (A / desc['blob']).resolve()
    assert p.parent == (A / 'tensors').resolve() and p.suffix == '.bin'
    b = p.read_bytes()
    assert len(b) == desc['nbytes'] and hashlib.sha256(b).hexdigest() == desc['bytes_sha256']
    values = np.frombuffer(b, dtype='<f4').reshape(desc['shape'])
    finite = values[np.isfinite(values)]
    rows.append({'frame_index': i, 'shape': desc['shape'], 'blob': str(p.relative_to(R)),
                 'sha256': desc['bytes_sha256'], 'nbytes': len(b),
                 'already_read_in_unit_replay': str(p.relative_to(R)) in prior,
                 'total': int(values.size), 'finite': int(finite.size),
                 'positive': int((values > 0).sum()), 'nonpositive': int((values <= 0).sum()),
                 'nonfinite': int((~np.isfinite(values)).sum()),
                 'min_finite': float(finite.min()) if finite.size else None,
                 'median_finite': float(np.median(finite)) if finite.size else None,
                 'max_finite': float(finite.max()) if finite.size else None,
                 'finite_below_original_near': int((finite < .1).sum())})
receipt = {'started_utc': start, 'ended_utc': datetime.now(timezone.utc).isoformat(),
           'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'rows': rows, 'total_bytes': sum(v['nbytes'] for v in rows),
           'model_calls': 0, 'RGB_or_colors_read': False, 'optimizer_replayed': False,
           'interpretation': 'Final geometry depths precede surfel construction. They do not reveal raw CUT3R prediction, MST initializer scale or a per-iteration depth trajectory.'}
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
OUT.chmod(0o444)
print(json.dumps(receipt, ensure_ascii=False))
