from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, urllib.request, urllib.error, os
from unittest.mock import patch
import numpy as np
from PIL import Image, ImageOps
import PIL
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
CUT=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local')
OUT=ROOT/'work/S14E_calibration_audit'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
r={'started_utc':now(),'role':'independent source/coordinate audit; no real data decoding','real_depth_decodes':0,'real_trajectory_decodes':0,'real_npz_decodes':0,'real_rgb_decodes':0,'model_calls':0,'web_search_queries':0,'evidence':[],'checks':[],'network':[]}
files=[CUT/'src/dust3r/utils/image.py',CUT/'viser_utils.py',CUT/'src/dust3r/datasets/base/base_multiview_dataset.py',CUT/'src/dust3r/heads/linear_head.py',CUT/'src/dust3r/losses.py',CUT/'src/dust3r/utils/camera.py',CUT/'src/dust3r/model.py',CUT/'src/dust3r/utils/geometry.py',CUT/'src/dust3r/datasets/utils/cropping.py',CUT/'demo.py',ROOT/'src/s6_memory_bridge.py',ROOT/'src/learned_pair_metrics.py',ROOT/'src/tum_rgbd.py',ROOT/'scripts/prepare_s8_inputs.py',ROOT/'scripts/run_s8_replay.py',ROOT/'scripts/run_s8_sequence.py',ROOT/'docs/S14D_RAY_ONLY_RESULTS.md',ROOT/'AGENTS.md',ROOT/'RESEARCH_MEMORY.md',ROOT/'docs/RESEARCH_WORKFLOW_CHECKLIST.md',Path('/Users/rocket/.codex/skills/idea-evaluator/SKILL.md'),Path('/Users/rocket/.codex/skills/idea-evaluator/references/fatal-flaws.md'),Path('/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md')]
for p in files:
    r['evidence'].append({'path':str(p),'sha256':sha(p)})
head=(CUT/'.git/HEAD').read_text().strip()
r['git_head_text']=head
if head.startswith('ref: '):
    ref=CUT/'.git'/head[5:]
    if ref.exists(): r['commit']=ref.read_text().strip()
    else:
        packed=CUT/'.git/packed-refs'
        r['commit']=next((line.split()[0] for line in packed.read_text().splitlines() if line.endswith(' '+head[5:])),None) if packed.exists() else None
else: r['commit']=head
r['tool_failures']=[{'action':'system git rev-parse HEAD','outcome':'unknown repository extension worktreeconfig; no mutation; resolved by reading bounded .git HEAD/ref metadata'},{'action':'web.run find/open official TUM tools page','outcome':'No matching timestamps / later timeout; retrieved file-formats and Pillow pages successfully; direct archival retry below'}]
for label,url in [('tum_file_formats','https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats'),('tum_tools','https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools'),('pillow_coordinates','https://pillow.readthedocs.io/en/stable/handbook/concepts.html')]:
    row={'label':label,'url':url,'requested_utc':now()}
    cached=OUT/(label+'.html')
    if cached.exists():
        row.update(status='CACHED_OFFICIAL_RESPONSE_FROM_INITIAL_ATTEMPT',bytes=cached.stat().st_size,sha256=sha(cached),path=str(cached),archive_mtime_utc=datetime.fromtimestamp(cached.stat().st_mtime,timezone.utc).isoformat(),note='Retrieved before artificial v1 failure; reuse saved source, no repeated HTTP')
        r['network'].append(row)
        continue
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Research coordinate audit'}),timeout=15) as q:
            data=q.read(2000001)
            if len(data)>2000000: raise ValueError('2 MB source cap exceeded')
            p=OUT/(label+'.html');p.write_bytes(data)
            row.update(status=q.status,final_url=q.url,bytes=len(data),sha256=sha(p),path=str(p),finished_utc=now())
    except Exception as e: row.update(error=type(e).__name__+': '+str(e),finished_utc=now())
    r['network'].append(row)
source=(CUT/'src/dust3r/utils/image.py').read_text();tree=ast.parse(source)
parts=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name in ('_resize_pil_image','load_images')]
ns={'PIL':PIL,'Image':Image,'os':os,'np':np,'heif_support_enabled':False,'exif_transpose':ImageOps.exif_transpose,'ImgNorm':lambda x:np.asarray(x)}
exec(compile(ast.Module(body=parts,type_ignores=[]),'official_source_ast','exec'),ns)
with patch.object(PIL.Image,'open',return_value=Image.new('RGB',(640,480))) as fake:
    out=ns['load_images'](['artificial.png'],224,verbose=False)
    assert fake.call_count==1 and out[0]['true_shape'].tolist()==[[224,224]]
r['checks'].append({'name':'official_AST_load_images_artificial_640x480','pass':True,'output_hw':[224,224],'real_input_read':False})
sx,sy=299/640,224/480
K=np.array([[525.,0,319.5],[0,525.,239.5],[0,0,1]])
A=np.array([[sx,0,sx*.5-.5-37],[0,sy,sy*.5-.5],[0,0,1.]])
K2=A@K
assert np.allclose(K2,[[245.2734375,0,112],[0,245,111.5],[0,0,1]],atol=5e-14,rtol=0)
p=np.array([[0,0,1],[223,223,1],[112,111.5,1.],[37,199,1.]]).T
assert np.allclose(np.linalg.solve(K2,p),np.linalg.solve(K,np.linalg.solve(A,p)),atol=1e-15,rtol=0)
r['checks'].append({'name':'pixel_center_resize_crop_inverse_intrinsic_identity','pass':True,'resized_wh':[299,224],'crop_xyxy':[37,0,261,224],'K224':K2.tolist(),'pixel_points':4})
# Artificial translation demonstrates failure of same-pose pinhole direction equivalence.
i,j=np.meshgrid(np.arange(224),np.arange(224));pix=np.stack([i,j,np.ones_like(i)],axis=-1)
d=np.linalg.solve(K2,pix.reshape(-1,3).T).T;t=np.array([.4,0,0])
pinhole=d/np.linalg.norm(d,axis=1,keepdims=True);encoded=(d+t)/np.linalg.norm(d+t,axis=1,keepdims=True)
maxdiff=float(np.max(np.abs(encoded-pinhole)));assert maxdiff>.1
r['checks'].append({'name':'translated_official_encoding_is_not_same_K_R_pinhole_direction','pass':True,'scope':'artificial mathematical counterexample, not experiment','t':[.4,0,0],'grid_points':224*224,'max_abs_difference':maxdiff})
# Synthetic known similarity; rotations must remain proper after inverse coordinate conversion.
theta=.37;R=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1.]])
s=2.3;b=np.array([1.2,-.5,.7]);cm=np.array([.3,-.7,1.]);Rm=np.eye(3);Cg=s*R@cm+b;Rg=R@Rm
recR=R.T@Rg;recC=R.T@(Cg-b)/s
assert np.allclose(recR,Rm,atol=1e-14,rtol=0) and np.allclose(recC,cm,atol=1e-14,rtol=0)
selfp=np.array([.5,-.2,3.]);modelp=Rm@selfp+cm;gtp=s*R@modelp+b;recz=Rg.T@(gtp-Cg)
assert np.allclose(recz,s*selfp,atol=1e-14,rtol=0)
r['checks'].append({'name':'Sim3_inverse_target_pose_and_self_depth_scale','pass':True,'scale':s,'det_recovered_rotation':float(np.linalg.det(recR)),'max_point_residual':float(np.max(np.abs(recz-s*selfp)))})
r['preparation_failure']='preparation_failure_v1/failure_receipt.json'
r.update(finished_utc=now(),status='PASS_SOURCE_AND_ARTIFICIAL_COORDINATE_AUDIT',source_sha256=sha(__file__))
write(OUT/'receipt.json',r)
print(json.dumps({'status':r['status'],'checks':len(r['checks']),'network':[(x['label'],x.get('status'),x.get('error')) for x in r['network']],'commit':r.get('commit'),'finished_utc':r['finished_utc']},ensure_ascii=False))
