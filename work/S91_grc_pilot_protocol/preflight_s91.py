from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'SELECTION_CONTRACT.json').read_text())
assert p['status']=='BLOCKED_ON_GATE0'
assert p['fairness']=={'same_candidate_pool':True,'same_k':True,'same_consumer':True,'same_randomness':True,'same_total_cost_accounting':True}
assert len(p['selectors'])>=8
assert set(p['selection_input_allowed']).isdisjoint(p['selection_input_forbidden'])
assert p['minimum_gate0']=={'independent_scenes':3,'history_candidates':6,'future_queries':3}
print('S91_PREFLIGHT_PASS_PROTOCOL_ONLY')
print('S91_STATUS',p['status'])
