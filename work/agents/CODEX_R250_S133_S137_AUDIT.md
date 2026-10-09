# R250 hostile audit: S133–S137

Audit scope: the checked-out files and receipts named in Brief R250. I did not run a GPU, training, download, Slurm job, or external write. Existing unrelated working-tree modifications were left untouched. `new_method_validated=false` and `novelty_authorization=NONE` are unchanged.

## Verdict table

| Claim | Verdict | Evidence |
|---|---|---|
| S133 `minimum_spanning_tree` silently uses identity after failed PnP | **Verified** | Pinned code calls `fast_pnp` for a missing pose, stores the result only on success, then assigns `torch.eye(4)` if still missing: `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py:239-249`. `fast_pnp` returns `None` for fewer than four masked points or no successful RANSAC: `:297-301`, `:321-341`. |
| S133 “PnP success count separates the failure classes 14/14” | **Partially supported / overclaimed** | The receipts support 0/4→large blow-up and 2/4→collapse associations, but the 4/4 group includes scene_13 w50 at ratio 0.445, outside the stated [0.5,2] normal-range gate: `work/S133_scale_debug/RESULT.md:21-36`, especially `:23` and `:41-42`. The valid statement is “the counts separate catastrophic blow-up/collapse groups on this panel”; it is not a 14/14 protocol-normality classification. |
| S133 fix removes blow-ups and meets its pre-registered 12/14 scale gate | **Verified as a panel gate, not scale certification** | The saved native-fix map evaluation is 11/14, so S134 correctly records native failure; the S133 CPU table claims 12/14, but its median is misstated below. The gate is a local diagnostic threshold, not proof of metric correctness: `work/S133_scale_debug/RESULT.md:49-54`; S134 saved gate `MAP_EVAL_native_fix1.json` is 11/14. |
| S133 fixed median scale ratio is 0.70 | **Refuted numerically** | Recomputing the listed stage-1 panel gives median ratios about 0.6683 (native) and 0.6681 (gl), not 0.70. The sentence is at `work/S133_scale_debug/RESULT.md:53-54`. |
| S134 native fix failed and therefore did not generate step B | **Verified** | Saved map gate: 14 windows, 11 in [0.5,2], 0 >10, 0 <0.1, median correlation 0.121688; `work/S134_tacc_fixed_map/RESULT.md:13-23` and `results/stepA_superpod/MAP_EVAL_native_fix1.json`. |
| S134 gl+fix passed its amended gate | **Verified for the recorded H800 receipt, with a harness caveat** | Saved gate is 12/14, 0 extreme, median corr 0.632573, 14 windows: `results/stepA_superpod/MAP_EVAL_gl_fix1.json`; result `work/S134_tacc_fixed_map/RESULT.md:35-44`. The evaluator does not enforce all protocol conditions; see details. |
| S134 H800/TACC context agreement was 8/14 original and 9/14 fixed | **Verified** | Direct receipt comparison gives 8/14 and 9/14; one original TACC scene_13 w200 receipt is blocked with `IndexError`: `work/S134_tacc_fixed_map/RESULT.md:29-33`, `results/stepA_tacc/*/RETRIEVAL_RECEIPT.json`. |
| S134 flag proves H800 geodesics were computed in TF32 | **Unverifiable as stated** | `croco.py` sets `torch.backends.cuda.matmul.allow_tf32=True` at `data/S134_tacc/vmem_src/extern/CUT3R/src/croco/models/croco.py:10-14`, and PyTorch documents that the flag permits TF32 for float32 matmul, but a permission flag does not prove a particular matmul used tensor cores. The CPU TF32 emulation reproduces the selection, which supports sensitivity, not the hardware causal attribution. |
| KPS equation `x_j ∝ R_j0 P + σ t_j0` is correct for this star-graph construction | **Verified with scope** | MST propagates each edge pointmap into the root coordinate system (`pts3d[j]` is transformed before returned): `init_im_poses.py:199-218`, with view 0 fixed and missing poses recovered at `:239-249`. KPS uses `Tj0 = inv(T[j]) @ T[0]` and row-vector `P @ R.T + σt`, algebraically the stated column-vector equation: `work/S135_scale_init/kps.py:7-10`, `:82-99`. This is valid only for all-known poses and the root-0 star graph; the code explicitly falls back otherwise at `:64-77`. |
| KPS synthetic test is 9/9 | **Unverifiable as a test run; test design verified** | Four sigma values × two baselines plus the pure-rotation flat-curve test are the nine parametrized cases: `work/S135_scale_init/test_kps.py:30-45`. The requested command `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python -m pytest work/S135_scale_init/test_kps.py -q` fails before collection with `No module named pytest`; therefore this audit does not claim a fresh 9/9 execution. |
| S135 “KPS cuts median scale error from 41% to 5.5%” | **Refuted wording** | The recorded values are median absolute log ratios 0.410 and 0.055, while relative-error medians are about 0.335 and 0.0536. `work/S135_scale_init/RESULT.md:17-29` does not label 41% as a relative error; the prose does. Report the metric explicitly. |
| S135 pixel-aligned depth metric exactly matches VMem RGB and CUT3R preprocessing | **Partially supported** | `repro_kps.py:111-116` maps depth through 768×576, crop 96:672, 512×512, crop rows 64:448; `:119-123` maps K. This matches the geometry of the crop/resize chain, but depth uses PIL nearest-neighbour while VMem RGB uses torch area interpolation (`repro_kps.py:84-88`); it is not “the same interpolation” as RGB. Pixel correspondence also needs an explicit half-pixel convention. |
| S135 niter 0 and 400 prove global alignment never moves scale | **Overclaimed** | The saved niter-zero comparison covers only the listed smoke subset (four windows per arm), not all 14 windows. Moreover CUT3R’s `get_depthmaps` creates a detached `ParameterStack` (`optimizer.py:245-249`, `:303-317`), so unchanged depth can reflect an optimizer-gradient disconnection. The claim needs this limitation. |
| VMem retrieval equals pose-NMS over memory frames 14/14 and TF32 emulation is 14/14 | **Mixed** | The exact CPU rerun on `results/stepA_superpod/native_fix1` gives pose-memset exact 9/14 in ordinary FP32 and 14/14 under round-to-nearest TF32 emulation. The original `POSE_ONLY_native_fix1.json` itself records `pose_memset_exact=9` and `pose_only_exact=3`. Thus 14/14 is reproducible only for the emulation, not independently demonstrated as an actual 3090/H800 execution. “Every memory frame is a candidate in 13/14” is supported by the repaired receipts. |
| S135 broken-map candidate sets shrink in the affected windows | **Verified on the saved panel** | CPU candidate counts are 4–5 in the four windows whose NMS-on contexts change, versus nine in the repaired map; this follows `pose_only_retrieval.py:95-103` and the saved receipts. It explains selection stability on this panel, not all VMem regimes. |
| S136 32/32 harness outputs are byte-identical | **Receipt-level verified; byte-level locally unverifiable** | `plan_v2.json`/manifest comparison has 32 expected pairs, 0 missing, 0 mismatches. The checkout contains no S136 `.npy` output bytes to rehash; only manifest hashes are present. S136 result line 8 must say “manifest hashes match,” not independently rehashed bytes. |
| S136 plan uses static offsets 0,15,30,45 and correct consumer contexts | **Verified** | `build_plan_s136.py:15`, `:18-25`, and `:38-48` construct static contexts and read `memory_nms_on_clean`; context keys deduplicate identical ordered `(scene,window,convention,ids)` tuples. Reconstructed `plan_v2.json` equals the receipt-derived plan. |
| S136 Q1–Q4 values are reproducible | **Verified numerically** | Independent CPU recomputation from both `S136_SCORES_*.json` files gives the exact means/CIs below. Interpretation caveats follow. |
| S136 “repairing memory completely changes nothing measurable” | **Refuted / overbroad** | Repair measurably changes map scale, coverage, and gate outcomes. Only selected PSNR contrasts are near zero. Q2 has a wide CI and strong scene cancellation; `RESULT.md:32-35` treats a threshold label as equivalence. |
| S136 “memory still ties static” and “repair ties broken memory” | **Overclaimed** | Q2 is −0.059 dB with CI [−1.153,+0.942], not an equivalence test; Q3 is on 13 windows because original-gl w200 is blocked (`PROTOCOL.md:60`). “Ties” is descriptive shorthand, not a supported no-effect conclusion. |
| S136 “same size on both GPUs” for Q1 | **Refuted literally** | Q1 is +0.827 dB on H800 and +0.953 dB on 3090 (`RESULT.md:16`); same direction and roughly similar magnitude would be accurate. Q3/Q4 hardware differences are larger. |
| S137 B0/B1 have no target-depth leakage | **Verified for predictor inputs** | `geometry_baselines.py:83-94` loads context RGB/depth and target pose; target RGB is loaded as the scorer reference at `:90`, not as a predictor input. The script documents this at `:8-9`. B1 is explicitly an RGB-D upper bound, not RGB-only: `PROTOCOL.md:5-11`. |
| S137 B2 has no target depth/RGB leakage into inference | **Verified by execution order, with process-isolation caveat** | B2 runs CUT3R and creates depths before loading target RGB for scoring (`geometry_b2.py:73-93`); it reads no target depth. The same process nevertheless has target RGB available to the scorer, so the claim should be “not consumed by inference,” not a sealed-process isolation claim. |
| S137 scorer is identical to C9 | **Verified for transform/PSNR implementation** | `geometry_baselines.py:26-35` matches `work/S132_C9_convention/score_c9.py:18-42` (area resize, crop, integer RGB error, pooled PSNR). This does not make the predictor or reference panel identical to every C9 run. |
| S137 headline PSNR contrasts are arithmetically reproducible | **Verified** | Saved summaries recompute exactly; see transcript. They remain conditional on the B2 mapping defect below and on a 16-window, two-scene panel. |
| S137 CUT3R-grid→640×480 inverse mapping is correct | **Refuted** | `geometry_b2.py:62-67` omits the source-pixel-centre `+0.5` before the resize inverse. The corresponding x coordinate should include `((u+0.5)*1.2-96)*512/576-0.5` (and analogously y), before rounding. The current map shifts lookup by about 0.533 CUT3R pixels in both axes. |
| S137 “geometry alone beats the frozen generator” proves a generator-consumption failure | **Overclaimed** | B2 is a direct RGB+pose geometric warp and B1 is an RGB-D upper bound; neither is a capacity-matched generator control. The result establishes a strong diagnostic PSNR contrast for this panel, not a causal claim about VMem’s internal consumption. |

## Details and independent recomputation

### Source identity and transport

The three pinned isolated copies hash identically at `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`. The transport source used by sealed runs is not byte-identical to the isolated copy: the audited hashes are `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255` for `data/S134_tacc/vmem_src/modeling/pipeline.py` and `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65` for `utils/util.py`. The diff is device handling only: `pipeline.py:959-976` defaults construction to `self.device`; `utils/util.py:694-705` selects CPU/CUDA autocast and device transfers. This is a material reproducibility caveat for CPU checks.

VMem’s actual retrieval source is auditable: geodesic distance is rotation angle plus weighted translation (`data/S134_tacc/vmem_src/modeling/pipeline.py:191-226`); visible surfels become weighted frame counts (`:462-502`); candidates are sorted by geodesic distance and NMS selects up to four (`:655-750`). `get_frame_distribution` has the unusual `result[idx] = 1` remainder assignment at `:452-458`; the reimplementation copies it at `work/S135_scale_init/pose_only_retrieval.py:37-50`.

### Exact CPU TF32-emulation rerun

Command:

```text
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python - <<'PY'
from pathlib import Path
import sys,json,io,contextlib,numpy as np,torch
p=Path('work/S135_scale_init/pose_only_retrieval.py'); source=p.read_text(); prefix,body=source.split('rows = []',1)
sys.argv=[str(p),'work/S134_tacc_fixed_map/results/stepA_superpod/native_fix1','data/S134_tacc/datasets','AUDIT_IN_MEMORY_ONLY']
ns={}; exec(compile(prefix,str(p),'exec'),ns); original_geo=ns['geo']; old=Path.write_text
Path.write_text=lambda self,data,*a,**k: len(data) if str(self)=='AUDIT_IN_MEMORY_ONLY' else (_ for _ in ()).throw(RuntimeError('unexpected write'))
for mode in ('fp32','tf32_rne','tf32_truncate'):
    def quant(x):
        a=x.contiguous().numpy().copy(); bits=a.view(np.uint32)
        if mode=='tf32_rne': bits[:]=(bits+np.uint32(4095)+((bits>>13)&1))&np.uint32(0xffffe000)
        else: bits[:]=bits&np.uint32(0xffffe000)
        return torch.from_numpy(a)
    def geo(a,b):
        a=torch.as_tensor(np.asarray(a,dtype=np.float32)); b=torch.as_tensor(np.asarray(b,dtype=np.float32))
        t=torch.norm(a[:3,3]-b[:3,3]); product=quant(a[:3,:3]).T @ quant(b[:3,:3]); tr=torch.clamp(torch.trace(product),-1.,3.)
        return float(t*0.1+torch.acos((tr-1)/2))
    ns['geo']=original_geo if mode=='fp32' else geo
    print('MODE',mode); exec(compile('rows = []'+body,str(p),'exec'),ns)
Path.write_text=old
PY
```

Audit-relevant output (the script also prints deterministic per-window status echoes):

```text
MODE fp32
{"recon_exact": 9, "pose_only_exact": 3, "pose_only_same_set": 3, "pose_memset_exact": 9, "mean_memset_overlap_of_4": 3.5714285714285716, "n": 14, "mean_overlap_of_4": 2.7142857142857144}
MODE tf32_rne
{"recon_exact": 14, "pose_only_exact": 5, "pose_only_same_set": 5, "pose_memset_exact": 14, "mean_memset_overlap_of_4": 4.0, "n": 14, "mean_overlap_of_4": 2.857142857142857}
MODE tf32_truncate
{"recon_exact": 7, "pose_only_exact": 2, "pose_only_same_set": 2, "pose_memset_exact": 7, "mean_memset_overlap_of_4": 3.357142857142857, "n": 14, "mean_overlap_of_4": 2.4285714285714284}
torch 2.7.0 numpy 1.26.4 device=cpu; output writes intercepted
```

The wrapper captured the summary objects while suppressing the script’s repetitive per-window status lines. This is a numerical sensitivity reproduction, not proof that a given GPU kernel executed TF32. PyTorch’s versioned documentation says `allow_tf32` controls whether TF32 tensor cores may be used for float32 matmul and rounds inputs to a 10-bit mantissa: <https://docs.pytorch.org/docs/2.7/notes/cuda.html#tensorfloat-32-tf32-on-ampere-and-later-devices>.

### S134 receipt and map checks

Command:

```text
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python - <<'PY'
from pathlib import Path
import sys,json,io,contextlib,numpy as np
base=Path('work/S134_tacc_fixed_map/results')
def records(p): return {(r['scene'],int(r['window_start'])):r for r in json.loads(p.read_text())['records']}
h=[records(base/f'stepA_superpod/native_fix{i}/RETRIEVAL_RECEIPT.json') for i in (0,1)]
t=[records(base/f'stepA_tacc/native_fix{i}/RETRIEVAL_RECEIPT.json') for i in (0,1)]
sealed={}
for p in Path('work/S130_C8_diagnostics/remote_support_609623').glob('scene_*/WINDOW_RECEIPT.json'):
 r=json.loads(p.read_text()); sealed[(r['scene'],int(r['window_start']))]=r
for arm in ['memory_nms_on_clean','memory_nms_off']:
 print('SEALED_MATCH',arm,sum(r.get('raw_contexts',{}).get(arm)==sealed[k].get('raw_contexts',{}).get(arm) for k,r in h[0].items()))
 print('FIX_CHANGED',arm,[f'{k[0]}_w{k[1]}' for k in h[0] if h[0][k].get('consumer_contexts',{}).get(arm)!=h[1][k].get('consumer_contexts',{}).get(arm)])
for i in (0,1): print('CROSS_HARDWARE_FIX',i,'matches',sum(r.get('consumer_contexts',{}).get('memory_nms_on_clean')==t[i][k].get('consumer_contexts',{}).get('memory_nms_on_clean') for k,r in h[i].items()),'TACC_BLOCKED',[(k,r.get('error')) for k,r in t[i].items() if r['status']!='OK'])
p=Path('work/S135_scale_init/pose_only_retrieval.py'); prefix,body=p.read_text().split('rows = []',1); old=Path.write_text
Path.write_text=lambda self,data,*a,**kw:len(data) if str(self)=='AUDIT_IN_MEMORY_ONLY' else (_ for _ in ()).throw(RuntimeError('Unexpected write'))
for i in (0,1):
 sys.argv=[str(p),str(base/f'stepA_superpod/native_fix{i}'),'data/S134_tacc/datasets','AUDIT_IN_MEMORY_ONLY']; ns={}
 with contextlib.redirect_stdout(io.StringIO()): exec(compile(prefix+'rows = []'+body,str(p),'exec'),ns)
 rows=ns['rows']; print('FIX',i,'candidate_counts',[(r['scene'],r['window_start'],r['n_candidate_frames']) for r in rows])
 if i==1: print('CPU_FP32_POSE_MEMSET_MATCH_TACC',sum(r['pose_memset']==t[1][(r['scene'],r['window_start'])]['raw_contexts']['memory_nms_on_clean'] for r in rows),'/',len(rows))
Path.write_text=old
PY
```

Complete output of the in-memory receipt comparison:

```text
SEALED_MATCH memory_nms_on_clean 14
FIX_CHANGED memory_nms_on_clean ['scene_13_w150', 'scene_13_w200', 'scene_14_w100', 'scene_14_w150']
SEALED_MATCH memory_nms_off 14
FIX_CHANGED memory_nms_off ['scene_13_w150', 'scene_14_w150']
CROSS_HARDWARE_FIX 0 matches 8 TACC_BLOCKED [(('scene_13', 200), 'IndexError: list index out of range')]
CROSS_HARDWARE_FIX 1 matches 9 TACC_BLOCKED []
FIX 0 candidate_counts [('scene_13', 50, 9), ('scene_13', 100, 9), ('scene_13', 150, 5), ('scene_13', 200, 4), ('scene_13', 250, 9), ('scene_13', 300, 9), ('scene_13', 350, 9), ('scene_14', 50, 9), ('scene_14', 100, 4), ('scene_14', 150, 5), ('scene_14', 200, 9), ('scene_14', 250, 9), ('scene_14', 300, 9), ('scene_14', 350, 9)]
FIX 1 candidate_counts [('scene_13', 50, 9), ('scene_13', 100, 9), ('scene_13', 150, 9), ('scene_13', 200, 9), ('scene_13', 250, 9), ('scene_13', 300, 9), ('scene_13', 350, 9), ('scene_14', 50, 9), ('scene_14', 100, 9), ('scene_14', 150, 8), ('scene_14', 200, 9), ('scene_14', 250, 9), ('scene_14', 300, 9), ('scene_14', 350, 9)]
CPU_FP32_POSE_MEMSET_MATCH_TACC 14 / 14
```

Saved map-gate outputs are: native orig 7/14 in range, 5 >10, corr 0.219539; native fix 11/14, 0 >10, corr 0.121688; gl orig 6/13, 5 >10, corr 0.605528 with one blocked record; gl fix 12/14, 0 >10, corr 0.632573. `eval_map_s134.py:69-73` records correlation but does not test the protocol’s correlation threshold or blocked-window condition (`PROTOCOL.md:23-28`); current gl-fix data happens to satisfy both, so the current PASS is numerically true but the gate implementation is weaker than the protocol.

The requested KPS test command was also run exactly as follows:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python -m pytest work/S135_scale_init/test_kps.py -q
```

Complete output:

```text
/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python: No module named pytest
```

### S136 independent Q1–Q4 recomputation

Command:

```text
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv-cut3r/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np
plan=json.loads(Path('work/S136_repaired_memory/plan_v2.json').read_text()); runs={}
for p in Path('work/S136_repaired_memory/results').glob('stepB_*/S136_SCORES_*.json'): runs.update(json.loads(p.read_text())['runs'])
by={(r['ctx_key'],int(r['seed'])):r['aggregate']['psnr_db'] for r in runs.values()}; arm={}
for c in plan['contexts']:
 for a in c['arms']: arm.setdefault(a,[]).append((c['scene'],int(c['window_start']),c['ctx_key']))
def con(a,b):
 ks=sorted(set((s,w) for s,w,k in arm[a])&set((s,w) for s,w,k in arm[b])); v=[]
 for s,w in ks:
  ka=next(k for ss,ww,k in arm[a] if (ss,ww)==(s,w)); kb=next(k for ss,ww,k in arm[b] if (ss,ww)==(s,w)); seeds=sorted(set(sd for k,sd in by if k==ka)&set(sd for k,sd in by if k==kb)); v.append(np.mean([by[(ka,sd)]-by[(kb,sd)] for sd in seeds]))
 v=np.array(v); rng=np.random.default_rng(0); boot=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(10000)])
 return len(v),v.mean(),np.percentile(boot,[2.5,97.5]),int((v>0).sum())
print('contexts',len(plan['contexts']),'runs',len(runs),'arm_counts',{a:len(v) for a,v in arm.items()})
for n,a,b in [('Q1','static_gl','static_native'),('Q2','mem_rep_gl','static_gl'),('Q3','mem_rep_gl','mem_orig_gl'),('Q4','mem_orig_native','static_native')]: print(n,con(a,b))
PY
```

Complete output:

```text
contexts 71 runs 568 arm_counts {'static_gl': 16, 'static_native': 16, 'mem_rep_gl': 14, 'mem_fix_gl': 14, 'mem_orig_gl': 13, 'mem_orig_native': 14}
Q1 (16, 0.8900441113288214, array([0.2484091 , 1.46873065]), 12)
Q2 (14, -0.05923314117743623, array([-1.15250844,  0.94158023]), 8)
Q3 (13, -0.14512008762361944, array([-0.5797134 ,  0.15330777]), 4)
Q4 (14, -0.2190008538794215, array([-0.82035089,  0.39060465]), 6)
```

The 568 files are 71 unique contexts × 8 seeds, not 568 independent context-arm cells. Twelve context keys are shared by two or three arms; the plan intentionally reuses identical ordered inputs. Hardware is confounded with seed assignment (H800 seeds 42,7,1,2; 3090 seeds 3,4,5,6), so per-site differences are not hardware-only estimates. Q2 also cancels strongly by scene (scene 13 about −1.109 dB, scene 14 about +0.990 dB).

### S137 arithmetic recomputation

Command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
import json
from pathlib import Path
for p in ['SUMMARY_c9ref.json','SUMMARY_s136ref.json']:
 d=json.loads((Path('work/S137_geometry_baselines')/p).read_text()); print(p); print('means',json.dumps(d['means'],sort_keys=True))
 for c in d['contrasts']: print(c['a'],'-',c['b'],c['n'],c['mean_db'],c['ci95'],c['a_wins'])
PY
```

Complete output:

```text
SUMMARY_c9ref.json
means {"b2_fix": 18.35026646761377, "b2_kps": 20.075919060536968, "b2_orig": 15.68136267515835, "copy": 15.522187124314948, "vmem_static_gl_c9": 15.246808228606259, "vmem_static_native_c9": 14.559865258294915, "warp_gtdepth": 22.05430882814177}
b2_kps - b2_fix 16 1.7256525929231945 [0.8321229855278791, 2.7882675464278948] 14
b2_fix - b2_orig 16 2.6689037924554215 [1.0140422078921194, 4.505740635535944] 8
b2_kps - b2_orig 16 4.394556385378616 [2.734587129944418, 6.323600893228041] 16
copy - vmem_static_native_c9 16 0.9623218660200332 [0.3317771168273763, 1.5744611466329061] 13
copy - vmem_static_gl_c9 16 0.27537889570868956 [-0.4263488737315871, 1.09272373003222] 9
b2_kps - vmem_static_native_c9 16 5.516053802242052 [4.398666722232839, 6.500233108665557] 16
b2_kps - vmem_static_gl_c9 16 4.8291108319307074 [3.5909435062083204, 6.082654806401815] 16
warp_gtdepth - vmem_static_native_c9 16 7.4944435698468554 [6.4196719627650145, 8.507928265598729] 16
warp_gtdepth - vmem_static_gl_c9 16 6.807500599535512 [5.7329734526794915, 7.821475811428608] 16
SUMMARY_s136ref.json
means {"b2_fix": 18.35026646761377, "b2_kps": 20.075919060536968, "b2_orig": 15.68136267515835, "copy": 15.522187124314948, "vmem_static_gl_c9": 15.246808228606259, "vmem_static_gl_s136": 15.24739911687914, "vmem_static_native_c9": 14.559865258294915, "vmem_static_native_s136": 14.35735500555032, "warp_gtdepth": 22.05430882814177}
b2_kps - b2_fix 16 1.7256525929231945 [0.8321229855278791, 2.7882675464278948] 14
b2_fix - b2_orig 16 2.6689037924554215 [1.0140422078921194, 4.505740635535944] 8
b2_kps - b2_orig 16 4.394556385378616 [2.734587129944418, 6.323600893228041] 16
copy - vmem_static_native_s136 16 1.1648321187646284 [0.5603081374911512, 1.7856255651791275] 14
copy - vmem_static_gl_s136 16 0.2747880074358068 [-0.2897913018196402, 0.9233373447524925] 9
b2_kps - vmem_static_native_s136 16 5.718564054986647 [4.690316112937709, 6.663182114392802] 16
b2_kps - vmem_static_gl_s136 16 4.828519943657825 [3.807940303909378, 5.868230567940064] 16
warp_gtdepth - vmem_static_native_s136 16 7.69695382259145 [6.740168959512631, 8.616997162008918] 16
warp_gtdepth - vmem_static_gl_s136 16 6.8069097112626284 [5.882690358185428, 7.723196106836216] 16
```

## Sentence-level overclaim inventory

### S133 `RESULT.md`

- `:41-42` calls the three-way classes “separated 14/14”; this needs the narrower catastrophic-class wording because the 0.445 window is outside the normal gate.
- `:53-54` reports the fixed median as 0.70; the full-panel median is about 0.668.
- `:60-62` says the old contrasts “measure a malfunctioning memory” without saying that S135 finds selection often unchanged because pose-NMS remains stable. The map is broken, but downstream causal effect is not established by the map diagnosis alone.

### S134 `RESULT.md`

- `:8-11` treats a historical transfer receipt and an asserted frozen environment as current independent verification. Call it receipt evidence unless the environment and remote hashes are freshly rechecked.
- `:32-33` turns a global TF32 permission flag into a fact about the specific geodesic matmul. Replace with “TF32 is permitted and emulation reproduces the selection.”
- `:43-44` attributes the correlation lift to the convention mismatch as a causal conclusion; it is a convention-arm association on this panel.
- The map-gate prose omits that `eval_map_s134.py` does not enforce the declared correlation and BLOCKED conditions.

### S135 `RESULT.md`

- `:25` converts log-ratio medians into “41% to 5.5%” without naming the metric; report both log and relative-error definitions.
- `:28-29` generalizes a limited niter-zero comparison to the global 14-window claim and omits the CUT3R detached-`ParameterStack` issue.
- `:42-46` presents 3090/H800 equality as established although the local saved POSE_ONLY receipt is 9/14 in FP32; only TF32 round-to-nearest emulation is 14/14.
- `:44-46` says TF32 “explains” cross-hardware divergence. It is a strong numerical explanation, not an instrumented proof of GPU kernel selection.
- `:47-48` says candidate-set shrinkage is the reason contexts remain unchanged; this is supported as a panel mechanism but should be scoped to these receipts.
- `:57-61` infers generator under-use from the map/retrieval diagnosis; that inference needs an intervention or matched consumer control.

### S136 `RESULT.md`

- `:8` must say 32/32 manifest/hash comparisons; local generated arrays are absent.
- `:16` “same size on both GPUs” is false literally; use “same direction and roughly similar magnitude.”
- `:29-30` generalizes the static convention contrast to every sealed VMem result; it is directly measured for static arms.
- `:32-35` “completely changes nothing measurable,” “memory still ties static,” and the causal “retrieval is pose-distance NMS, so…” exceed finite PSNR/map evidence. Report the near-zero threshold outcomes with CIs and scene cancellation.
- `:36-37` calls Q4 “no detectable difference,” conflicting with the protocol verdict `INCONCLUSIVE` because |mean|=0.219 exceeds the ±0.2 materiality threshold even though the CI covers zero.
- `:40-41` says hardware blocks agree; seed blocks are disjoint and Q3/Q4 differ by site. Say “Q1/Q2 have similar direction; site effects are confounded.”

### S137 `RESULT.md`

- `:25-30` is numerically supported, but “confirmed” should be restricted to the pre-registered panel rule and not called method validation.
- `:33-36` “turns C8’s consumption failure into a number” is causal overreach: B2 is a direct aligned warp, not a matched VMem consumer experiment.
- `:34` calls the predictor “deployable”; the run depends on CUT3R weights/runtime and a known pose stream, so this is an engineering judgment, not measured evidence.
- `:37-39` says warping is aligned “by construction” while `geometry_b2.py:62-67` has the half-pixel inverse-map defect. Recompute after fixing the map or qualify all B2 numbers.
- `:44-46` calls the 2×2 result “probably” caused by half-pixel shift/blur and says a better renderer “would likely” improve B2. These are hypotheses, not measured conclusions.
- `:40` is a good scope caveat, but it must also name the inverse-map defect, the direct-warp versus generator comparison, and the fact that B1 is an RGB-D upper bound.

## Bottom-line audit disposition

S133’s silent identity fallback and the existence of a scale failure are real. KPS’s algebra and the saved S136/S137 arithmetic are substantially reproducible. The strongest negative findings are that S135’s 14/14 claim is only obtained under an emulation, S136’s gate/equivalence prose exceeds its uncertainty and missing bytes, and S137’s B2 inverse coordinate map is wrong by a half-pixel-centre term. The S137 PSNR table should therefore be treated as a conditional diagnostic result pending corrected mapping, not as validation of a new method or a causal proof about VMem consumption.
