# R261 — S143 Amendment 1 rejection review

Workspace: local Mac checkout. Review date: 2026-10-10. This review concerns protocol and implementation, not an S143 outcome. No S143 discovery/confirmation score payload, image, weight, or remote state was inspected. Remote execution status and the claimed pre-score timing remain **UNVERIFIED**. Source snapshot and exact CPU checks are below.

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| **The window interval does not establish seed-generalization confidence.** | **MAJOR — reject the formal confirmation claim** | `PROTOCOL.md:69–74` names seed-level replication. `analyze_s143_confirm.py:26–41` first averages fresh seeds within windows, then resamples windows; `gen_s141.py:134–135` resets the same seed for every cell. R260 explicitly requires seed-panel uncertainty (`CODEX_R260_S143_DRAFT_REJECTION.md:358`). **DERIVED, synthetic check A:** with independent symmetric ±1 dB seed-panel contrasts identical across windows, the entire gate passes **5/16 = 0.3125** zero-mean null realizations. One passing realization has C = 0.5 and window interval [0.5, 0.5]. This is a counterexample, **not an estimated S143 false-positive rate**. | Define D_s = mean_w[Q_G(w,c_G_disc,s) − Q_G(w,c_W,s)] and use whole seed panels as replication units. Keep the current window interval and pair signs descriptive. Smallest repair: rename `CONFIRMED` to an explicitly exploratory/descriptive fresh-seed gate. If formal mean inference is required, freeze its seed-panel confidence procedure, assumptions, and adequate fixed seed budget before scores; simply bootstrapping four panels is not a calibration guarantee. |
| **The promised local-versus-global confirmation gate is absent.** | **MAJOR — implementation/protocol mismatch** | “Same for window-specific structure” at `PROTOCOL.md:71–72`; `analyze_s143_confirm.py:30–39` computes the frozen global-rule contrast, but emits only rule, mean and window interval. Line 41 gates C alone. Check A confirms those are its only fields. | Compute the local-minus-global per-seed panel means and per-pair means, then apply the same explicitly chosen inference/decision policy. Emit a separate status. A positive C alone cannot establish window-specific preference structure. If this secondary remains descriptive, say so before unblinding rather than claiming it was confirmed. |
| **Invalid score tables can be accepted as valid positive or negative assays.** | **MAJOR — fail-closed validation missing** | `analyze_s143_confirm.py:9–20` checks required cells and duplicates among retained seeds, but filters other seeds and accepts extra contexts; there is no finiteness assertion. In contrast, discovery checks exact cell count and finite primary arrays at `analyze_s143.py:26–32`. **DERIVED, check A:** extra seed/context and an unselected NaN are accepted with `CONFIRMED=True`; a selected NaN produces C=NaN and ordinary `CONFIRMED=False`. Missing and duplicate required cells correctly raise. Invalid ≠ negative under `PROTOCOL.md:55–56`. | Require exact expected (window, unique set, seed) keys separately for discovery and fresh scores, finite Q_W/Q_G, unique pool/window IDs, and complete unambiguous pair/rule mappings. Reject malformed input as `INVALID_ASSAY` before selecting or emitting a scientific decision; do not silently discard contamination. |
| **C is valid, but it evaluates a different selection budget from the discovery primary.** | **CLARIFICATION — no inherent selection inconsistency** | Discovery fits two-seed selectors and evaluates the opposite fold (`PROTOCOL.md:34–36`; `analyze_s143.py:44–57`). Confirmation fits on all four discovery seeds and evaluates only the disjoint fresh seeds (`PROTOCOL.md:67–69`; `analyze_s143_confirm.py:21–32`). | Name it `C_frozen4_discovery`: conditional on the frozen discovery choices and independent fresh panels, it estimates their expected paired PSNR advantage over c_W on these fixed windows. Four-seed fitting introduces no fresh-score maximization bias. Report it separately; it cannot retroactively confirm the exact two-seed R estimand or erase a failed R. If that exact procedure is the target, predeclare a separate equal-weight fresh evaluation of the two frozen fold winners; do not choose after seeing outcomes. |
| **Selection ties, rule aliases and filename parsing are not the alleged bug.** | **PASS, subject to valid inputs** | Lowest-rule tie breaking is explicit at `analyze_s143_confirm.py:19–24,29–30` and `analyze_s143.py:37–38,52–54`. Pool construction merges identical ordered sets (`build_pool_s143.py:80–87`), so aliased rules share one score. Scorer `score_s140.py:26–29,44` splits at the **last** `__s`, then parses its suffix as the seed; confirmation splits the remaining context key once (`analyze_s143_confirm.py:12`). **DERIVED, checks A/B:** all-score ties select rule 1; all 576 planned fresh filename round trips pass, including set s1/s2 with seeds 1/2. Current pool has no rule-4/5 alias. Delegated synthetic check C makes a merged [4,5] candidate best: r_disc=4 and identities stay fixed despite input reordering and changed fresh outcomes. | Preserve this logic. Do not replace `rsplit('__s',1)` with a first split. Validate that each rule maps to exactly one unique set per window. Aliases are labels, not extra independent candidates or observations. |
| **Discovery's descriptive Spearman mishandles tied scores.** | **MINOR — existing descriptive bug** | `analyze_s143.py:103–107` uses double `argsort`, assigning distinct ranks to ties. **DERIVED, check B:** two constant six-entry inputs return 1.0, although their correlation is undefined. This does not alter c_W, c_G, R, or C. | Use average ranks for ties and return null for constant ranks. Freeze this correction before opening results; label it a descriptive-statistic correction, not a revised primary. |
| **The launcher records some live hashes but does not enforce the same frozen scorer/environment.** | **MEDIUM — provenance gap, not observed drift** | `s143_confirm_chain.sh:6–18` waits for a DONE marker, records `$S/*.py` and the plan, then invokes the separate `$R/src/s140/score_s140.py`; it does not compare against a discovery manifest. Counts at lines 15–18 do not establish exact cell identities. The script does specify the intended fresh seeds and uses the same part plan. | Before confirmation execution, compare the actual generator, external scorer, model/config/weight/environment identities and plan against discovery receipts. Fail on drift. Save c_W, c_G_disc and r_disc with input hashes before inspecting fresh contrasts. Generating all candidates before that save is not itself leakage: the selection algorithm already excludes fresh scores. No remote drift is established by this review. |
| **“New on this hardware” is narrower than historically unseen randomization.** | **INTERPRETATION CAVEAT** | `PROTOCOL.md:65–66` acknowledges these seed IDs were used in S139 on H800. Seed initialization is controlled by the seed value (`gen_s141.py:134–135`), so changing hardware is not evidence that prior seed-related information disappeared. | Say “disjoint from S143 discovery; previously used in S139.” Do not claim historical blinding or independence merely from the hardware change. This is not evidence that fresh outcomes influenced the frozen S143 selector; that influence was not established here. |

Path key for the table: unqualified S143 filenames are under `work/S143_context_ranking/`; `gen_s141.py` is `work/S141_finetune/gen_s141.py`; `score_s140.py` is `work/S140_warp_guided/score_s140.py`; R260 is `work/agents/CODEX_R260_S143_DRAFT_REJECTION.md`. All numerical test findings above are synthetic or metadata-derived; complete command output is reproduced below.

## Verdict

**REJECT Amendment 1 as written as a formal confirmation procedure. Keep its contrast and four-seed discovery fitting.** Conditional on frozen choices, C answers the right narrow question: does the four-discovery-seed selector beat the warp selector in expected generated PSNR on the same exposed panel? It does not measure scene generalization, a deployable target-blind selector, or the exact two-seed discovery primary.

Before discovery scores are opened, freeze the interpretation/inference amendment, implement the missing global-rule policy and invalid-input handling, and correct descriptive Spearman. The existing +0.20 dB practical bar, three-positive-panel guard and pair signs can remain **descriptive robustness requirements**; their combination has no supplied confidence guarantee. Preserve unconditional fresh evaluation and the original discovery analysis. Do not recycle the discovery null cutoff for this different estimand or tune a replacement inference rule after seeing scores.

This review changes no protocol, code, ledger, compute allocation, or authorization: `new_method_validated=false`, `novelty_authorization=NONE`. Only the requested R261 report is authored. The follow-up is the concrete pre-score amendment and code corrections above, not another open-ended review round.

## Reproducible CPU evidence

Root checks A/B below ran from the repository root with exit code 0. They use the existing CPU environment and create no test files. Check A executes the actual confirmation analyzer with all its reads/writes redirected to in-memory JSON. Check B reads only pool/plan metadata and source, and extracts the actual parser and Spearman code. No repository-wide suite was run: this is a read-only review, and the targeted synthetic checks exercise the disputed behavior.

<details>
<summary>Check A: exact command and complete output</summary>

```bash
.venv/bin/python -B - <<'PY'
import contextlib, copy, io, itertools, json, pathlib, sys
from unittest.mock import patch
import numpy as np
src = pathlib.Path('work/S143_context_ranking/analyze_s143_confirm.py').read_text()
code = compile(src, 'work/S143_context_ranking/analyze_s143_confirm.py', 'exec')
D, F = (3,4,5,6), (42,7,1,2)
sets = [{'set_id': 's'+str(i), 'rules': [i]} for i in range(1,7)]
sets[3] = {'set_id':'s4-5','rules':[4,5]}; del sets[4]
P = {'windows':[{'window_id':f'w{i:02}', 'sets':sets} for i in range(24)]}
PA = {'rows':[{'window_id':f'w{i:02}', 'pair':f'p{i//8}'} for i in range(24)]}
W = {'windows':{w['window_id']:{'sets':{s['set_id']:{'warp_psnr':21. if s['set_id']=='s1' else 20.} for s in sets}} for w in P['windows']}}
def scores(seeds, delta):
    return {'runs':{f"{w['window_id']}__{s['set_id']}__s{sd}":{'ctx_key':f"{w['window_id']}__{s['set_id']}", 'seed':sd, 'psnr_db':20.+(delta[j] if s['set_id']=='s2' else 0.)} for w in P['windows'] for s in sets for j,sd in enumerate(seeds)}}
GD = scores(D, [1.]*4)
def run(gf, gd=None, ws=None):
    data = dict(zip(('pool','warp','disc','fresh','pairs'), (P, W if ws is None else ws, GD if gd is None else gd, gf, PA)))
    outputs = {}
    class MemPath:
        def __init__(self, p): self.p = p
        def read_text(self): return json.dumps(data[self.p])
        def write_text(self, value): outputs[self.p] = value; return len(value)
    with patch('pathlib.Path', MemPath), patch.object(sys,'argv',['analyze','pool','warp','disc','fresh','pairs','out']), contextlib.redirect_stdout(io.StringIO()):
        exec(code, {'__name__':'__main__'})
    return json.loads(outputs['out'])
r = run(scores(F, [1.,1.,1.,-1.]))
print('shared_panel_example',json.dumps({'mean':r['C']['mean'],'ci95':r['C']['ci95'],'seed_means':r['C']['fresh_seed_panel_means'],'pair_means':r['C']['pair_means'],'CONFIRMED':r['CONFIRMED']},sort_keys=True))
print('global_gap_fields',sorted(r['window_specific_vs_disc_rule']))
passed = sum(run(scores(F,x))['CONFIRMED'] for x in itertools.product((-1.,1.),repeat=4))
print('symmetric_zero_mean_null_passes',passed,'/ 16 =',passed/16)
wt = copy.deepcopy(W)
for row in wt['windows'].values():
    for s in row['sets'].values(): s['warp_psnr']=20.
t = run(scores(F,[0.]*4), scores(D,[0.]*4), wt)
print('all_ties', 'cW='+str(sorted({x['c_W'] for x in t['rows']})), 'cG='+str(sorted({x['c_G_disc'] for x in t['rows']})), 'r_disc='+str(t['window_specific_vs_disc_rule']['rule']), 'C='+str(t['C']['mean']))
for name in ('missing','duplicate','extra_seed','extra_context','nonfinite_unselected','nonfinite_selected'):
    gf = scores(F,[1.]*4)
    key = 'w00__s2__s42'
    if name=='missing': del gf['runs'][key]
    elif name=='duplicate': gf['runs']['duplicate']=dict(gf['runs'][key])
    elif name=='extra_seed': gf['runs']['extra']={'ctx_key':'w00__s2','seed':99,'psnr_db':20.}
    elif name=='extra_context': gf['runs']['extra']={'ctx_key':'outside__s1','seed':42,'psnr_db':20.}
    elif name=='nonfinite_unselected': gf['runs']['w00__s6__s42']['psnr_db']=float('nan')
    else: gf['runs'][key]['psnr_db']=float('nan')
    try:
        a=run(gf); print(name,'ACCEPTED', 'CONFIRMED='+str(a['CONFIRMED']), 'C='+str(a['C']['mean']))
    except Exception as e: print(name,'REJECTED',type(e).__name__)
print('synthetic_only: no discovery/confirmation score files read; all analyzer writes captured in memory')
PY
```

```text
shared_panel_example {"CONFIRMED": true, "ci95": [0.5, 0.5], "mean": 0.5, "pair_means": {"p0": 0.5, "p1": 0.5, "p2": 0.5}, "seed_means": {"1": 1.0, "2": -1.0, "42": 1.0, "7": 1.0}}
global_gap_fields ['ci95', 'mean', 'rule']
symmetric_zero_mean_null_passes 5 / 16 = 0.3125
all_ties cW=['s1'] cG=['s1'] r_disc=1 C=0.0
missing REJECTED AssertionError
duplicate REJECTED AssertionError
extra_seed ACCEPTED CONFIRMED=True C=1.0
extra_context ACCEPTED CONFIRMED=True C=1.0
nonfinite_unselected ACCEPTED CONFIRMED=True C=1.0
nonfinite_selected ACCEPTED CONFIRMED=False C=nan
synthetic_only: no discovery/confirmation score files read; all analyzer writes captured in memory
```

</details>

<details>
<summary>Check B: exact command, complete output, and reviewed source hashes</summary>

```bash
.venv/bin/python -B - <<'PY'
import ast, hashlib, itertools, json, subprocess
from pathlib import Path
import numpy as np
base=Path('work/S143_context_ranking')
pool=json.loads((base/'POOL.json').read_text())
plans=[json.loads((base/f'plan_s143_part{i}.json').read_text()) for i in (0,1)]
contexts=[c for p in plans for c in p['contexts']]
assert len({c['ctx_key'] for c in contexts})==len(contexts)
keys={c['ctx_key'] for c in contexts}
node=next(n for n in ast.walk(ast.parse(Path('work/S140_warp_guided/score_s140.py').read_text())) if isinstance(n,ast.Assign) and getattr(n,'lineno',0)==28)
parser=compile(ast.Module(body=[node],type_ignores=[]),'<actual score_s140 line 28>','exec')
n=0
for c in contexts:
    for seed in (42,7,1,2):
        name=f"{c['ctx_key']}__s{seed}.npy"; ns={'npy':Path(name)}; exec(parser,ns)
        assert ns['key']==c['ctx_key'] and int(ns['s'])==seed
        assert ns['key'].split('__',1)==[c['window_id'],c['mode']]
        n+=1
alias=sum(any(4 in s['rules'] and 5 in s['rules'] for s in w['sets']) for w in pool['windows'])
print('metadata_only', 'windows',len(pool['windows']), 'contexts',len(contexts), 'rule4_rule5_alias_windows',alias)
print('actual_parser_roundtrips_PASS',n,'includes_set_s1_s2_and_seed_1_2')
source=ast.parse((base/'analyze_s143.py').read_text())
fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='spearman')
ns={'np':np}; exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual discovery spearman>','exec'),ns)
print('actual_spearman_constant_inputs',ns['spearman'](np.ones(6),np.ones(6)))
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
for name in ('PROTOCOL.md','analyze_s143_confirm.py','s143_confirm_chain.sh','analyze_s143.py'):
    p=base/name; print('sha256',hashlib.sha256(p.read_bytes()).hexdigest(),str(p))
print('sha256',hashlib.sha256(Path('work/S140_warp_guided/score_s140.py').read_bytes()).hexdigest(),'work/S140_warp_guided/score_s140.py')
PY
```

```text
metadata_only windows 24 contexts 144 rule4_rule5_alias_windows 0
actual_parser_roundtrips_PASS 576 includes_set_s1_s2_and_seed_1_2
actual_spearman_constant_inputs 1.0
HEAD 87bdbaeb93cb66fba09886b35e81fa2fdffdd71d
sha256 b8ade72cc5cab9c8784d4088a8ce945661896a1b44348aa3804e89ec6f2537da work/S143_context_ranking/PROTOCOL.md
sha256 c4b489b8d81084dfe14eeb0a72e8efe18119ab52f58c57c2dd424a94c4731052 work/S143_context_ranking/analyze_s143_confirm.py
sha256 fde654672f652752b5e8ea558787cba883803b0d75c80464adf45b06f01a85cf work/S143_context_ranking/s143_confirm_chain.sh
sha256 d70dadcfd68fb187df0e5d416768e236209daca1e47f20f898c9ac4f44bb8125 work/S143_context_ranking/analyze_s143.py
sha256 61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79 work/S140_warp_guided/score_s140.py
```

</details>

<details>
<summary>Check C: delegated read-only alias check, exact successful command and complete output</summary>

This check ran in the existing CUT3R environment with exit code 0; reads and writes were mocked in memory.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B - <<'PY'
import contextlib, copy, io, json, sys
from pathlib import Path
from unittest.mock import patch
source = Path('work/S143_context_ranking/analyze_s143_confirm.py').read_text()
sets = [{'set_id': f's{r}', 'rules': [r]} for r in (1, 2, 3)] + [{'set_id': 's4-5', 'rules': [4, 5]}, {'set_id': 's6', 'rules': [6]}]
pool = {'windows': [{'window_id': f'w{i}', 'sets': copy.deepcopy(sets)} for i in range(3)]}
warp = {'windows': {w['window_id']: {'sets': {s['set_id']: {'warp_psnr': 10.0 if 4 in s['rules'] else 0.0} for s in sets}} for w in pool['windows']}}
pa = {'rows': [{'window_id': f'w{i}', 'pair': f'p{i}'} for i in range(3)]}
def scores(seeds, fresh=False):
    return {'runs': {f"{w['window_id']}__{s['set_id']}__s{sd}": {'ctx_key': f"{w['window_id']}__{s['set_id']}", 'seed': sd, 'psnr_db': (100.0 if fresh and s['set_id'] == 's1' else 10.0 if 4 in s['rules'] else 0.0)} for w in pool['windows'] for s in sets for sd in seeds}}
gd, gf = scores((3, 4, 5, 6)), scores((42, 7, 1, 2))
def run(p, d, f):
    inputs = dict(zip(('POOL', 'WS', 'GD', 'GF', 'PA'), (p, warp, d, f, pa))); out = {}
    def read(path, *a, **k): return json.dumps(inputs[str(path)])
    def write(path, txt, *a, **k): out[str(path)] = json.loads(txt); return len(txt)
    with patch.object(Path, 'read_text', read), patch.object(Path, 'write_text', write), patch.object(sys, 'argv', ['analyze_s143_confirm.py', 'POOL', 'WS', 'GD', 'GF', 'PA', 'OUT']), contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, 'work/S143_context_ranking/analyze_s143_confirm.py', 'exec'), {})
    r = out['OUT']; return r['window_specific_vs_disc_rule']['rule'], [(x['window_id'], x['c_W'], x['c_G_disc']) for x in r['rows']]
a = run(pool, gd, gf)
rev = copy.deepcopy(pool)
for w in rev['windows']: w['sets'].reverse()
b = run(rev, {'runs': dict(reversed(list(gd['runs'].items())))}, scores((42, 7, 1, 2), fresh=True))
expected = (4, [(f'w{i}', 's4-5', 's4-5') for i in range(3)])
print('SYNTHETIC_ONLY; original confirmation analyzer; reads/writes mocked in memory')
print('alias_4_5_best=', a)
print('reordered_inputs_and_changed_fresh_scores=', b)
print('stable_expected_selections=', a == b == expected)
assert a == b == expected
PY
```

```text
SYNTHETIC_ONLY; original confirmation analyzer; reads/writes mocked in memory
alias_4_5_best= (4, [('w0', 's4-5', 's4-5'), ('w1', 's4-5', 's4-5'), ('w2', 's4-5', 's4-5')])
reordered_inputs_and_changed_fresh_scores= (4, [('w0', 's4-5', 's4-5'), ('w1', 's4-5', 's4-5'), ('w2', 's4-5', 's4-5')])
stable_expected_selections= True
```

</details>

