from pathlib import Path
import datetime,difflib,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
BASE=ROOT/'work/S17C_interface_preparation/isolated_vmem_source';DEST=HERE/'isolated_vmem_source';assert not DEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((ROOT/'work/S17C_interface_preparation/source_plan.json').read_text())
files=[]
for p in sorted(BASE.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
 q=DEST/p.relative_to(BASE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);files.append({'path':str(p.relative_to(BASE)),'base_sha256':sha(p)})
patches=[]
for rel in ['utils/util.py','modeling/pipeline.py']:
 p=DEST/rel; source=Path(plan['vmem_root'])/rel
 assert sha(p)==sha(source),'S17C parent differs unexpectedly: '+rel
 candidate=ROOT/'work/S17_cpu_preflight/patched'/rel
 old=p.read_text();new=candidate.read_text();p.write_text(new)
 patches.append({'path':rel,'old_sha256':sha(source),'new_sha256':sha(p),'candidate_source':str(candidate),'reason':'reuse S17 tested CPU device dispatch; no transformer/math/NMS change'})
 (HERE/(rel.replace('/','_')+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original/'+rel,tofile='S20/'+rel)))
for r in files:r['final_sha256']=sha(DEST/r['path'])
j={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_source':str(BASE),'base_source_plan_sha256':sha(ROOT/'work/S17C_interface_preparation/source_plan.json'),'original_checkout':plan['vmem_root'],'original_commit':plan['vmem_commit'],'source_files':files,'additional_patches':patches,'inherited_adaptations':'S17C RoPE CPU dispatch/new rope_cpu and weights_only=True embedded load preserved','scope':'source preparation only, no model or data call'}
(HERE/'source_manifest.json').write_text(json.dumps(j,indent=2));print('prepared',len(files),'files with',len(patches),'additional device patches')
