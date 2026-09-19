"""Pre-Gate schema check for counterfactual/tail-risk novelty controls.
No model inference, no future GT read; inspects field names only.
"""
import json
from pathlib import Path
p = Path(__file__).parents[1] / 'S100_context_matched_swap/score_01/SCORES.json'
d = json.loads(p.read_text())
rows = d.get('rows', [])
fields = sorted({k for row in rows for k in row})
required = ['surprise','uncertainty','pose_distance','ray_relevance','future_loss']
receipt = {
 'schema':'innovation-round3-pre-gate-schema-v1',
 'input': str(p.resolve()), 'rows':len(rows), 'fields':fields,
 'required_controls_present':{k:any(k in row for row in rows) for k in required},
 'status':'NOT_IDENTIFIABLE_FROM_S100_SCHEMA',
 'scientific_boundary':'No inference or future-GT read; this is a data qualification check only.'
}
out = Path(__file__).with_name('innovation_round3_counterfactual_data_check.json')
out.write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
