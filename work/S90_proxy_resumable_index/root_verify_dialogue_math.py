#!/usr/bin/env python3
"""Independent exact arithmetic on saved artificial examples, never model inference."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys

ROOT = Path(__file__).resolve().parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def exact(v):
    return F(str(v))

def contrast(t):
    return exact(t[1][1])-exact(t[1][0])-exact(t[0][1])+exact(t[0][0])

def mean(t):
    return sum((exact(x) for row in t for x in row), F(0))/4

def main():
    started = datetime.now(timezone.utc)
    paths = [ROOT/'agents/two_by_two_logic_results.json',
             ROOT/'agents/threshold_consumer_loss_counterexample_results.json',
             ROOT/'innovation_agent/GRC_MATH_SANITY_RESULTS.json',
             ROOT/'innovation_agent/agents/math_repro_20260911_1814/GRC_MATH_SANITY_RESULTS.json']
    two, threshold, latest, prior = [json.loads(p.read_text()) for p in paths]
    checks = []
    scenarios = {}
    for name in ('scenario_A','scenario_B'):
        tables = two[name]['tables']
        scenarios[name] = {k: dict(interaction=str(contrast(t)), mean=str(mean(t))) for k,t in tables.items()}
        for k,t in tables.items():
            assert abs(float(contrast(t))-two[name]['interactions'][k])<1e-12
            assert abs(float(mean(t))-two[name]['mean_loss'][k])<1e-12
    a,b = two['scenario_A']['tables'], two['scenario_B']['tables']
    assert all(contrast(t)==0 for t in a.values())
    assert mean(a['high_risk_memory'])-mean(a['low_risk_memory'])==F(2,5)
    assert contrast(b['memory_B'])==F(-4,5)
    assert mean(b['memory_A'])==mean(b['memory_B'])==F(3,10)
    checks.append('two_by_two_exact_rational_counterexamples')
    cand=threshold['candidates']
    choices=[]
    for key in ('loose_threshold','tight_threshold'):
        admissible=[k for k,v in cand.items() if exact(v['estimated_risk'])<=exact(threshold[key])]
        choices.append(max(admissible,key=lambda k:exact(cand[k]['utility'])))
    assert choices==['A','B']
    assert exact(cand['B']['future_loss'])-exact(cand['A']['future_loss'])==F(1,2)
    assert digest(ROOT/'agents/threshold_consumer_loss_counterexample.py')==threshold['script_sha256']
    checks.append('threshold_choice_exact_rational_and_source_hash')
    assert latest['test_count']==prior['test_count']==7
    oldtests=prior['tests']; newtests=json.loads(json.dumps(latest['tests']))
    assert newtests['non_submodularity_and_greedy_failure'].pop('exhaustive_monotonicity_checks')==32
    assert newtests==oldtests
    assert digest(ROOT/'innovation_agent/grc_math_sanity.py')==latest['source']['script_sha256_before_result_write']
    assert digest(Path(latest['source']['official_crc_file']))==latest['source']['official_crc_file_sha256']
    checks.append('latest_seven_core_fields_equal_prior_independent_run_and_source_hash')
    out=ROOT/'ROOT_DIALOGUE_AUDIT_RECEIPT.json'
    result=dict(status='PASS',evidence_type='saved_synthetic_data_exact_recomputation_and_source_identity_only',
        started_utc=started.isoformat(),completed_utc=datetime.now(timezone.utc).isoformat(),
        python=sys.version,platform=platform.platform(),script_sha256=digest(Path(__file__)),
        inputs=[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in paths],
        checks=checks,two_by_two_exact=scenarios,threshold_exact_future_loss_increase='1/2',
        boundaries=['No new model, video, RGB-D, future geometry metric or GRC validation.',
                    'Recomputed saved artificial numbers; did not rerun either author script.',
                    'The old independent run covers the older script. Current core values match; added monotonicity-check count is new.',
                    'Non-additive risk example is generic set-conditioned loss, not a counterexample to the probability union bound.',
                    'Two-by-two absence of mean benefit refers to the declared uniform four-cell estimand.'])
    with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(status=result['status'],output=str(out),checks=checks),ensure_ascii=False))

if __name__=='__main__':
    main()
