"""Finite post-attachment metadata review; never launches or reads scientific bodies."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import types

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = ROOT / 'work/S47_c2_confirmation_generation'
OUT = HERE / 'final_launch_readiness_evidence'
START = datetime.now(timezone.utc).isoformat()
READS = {}
def read(path, expected=None):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode), str(path)
        chunks=[]
        while block:=os.read(fd,1024*1024): chunks.append(block)
        data=b''.join(chunks); after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        assert identity(before)==identity(after)
        digest=hashlib.sha256(data).hexdigest()
        if expected is not None: assert digest==expected, str(path)
        READS[str(path)]={'sha256':digest,'size':len(data),'device':before.st_dev,'inode':before.st_ino}
        return data
    finally: os.close(fd)
def doc(path,expected=None): return json.loads(read(path,expected))
def core_sha(x):
    return hashlib.sha256(json.dumps({k:v for k,v in x.items() if k!='review_receipts'},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def terminal(path,names):
    assert set(os.listdir(path))==set(names),str(path)
    for name in names:
        st=os.lstat(path/name)
        assert stat.S_ISREG(st.st_mode) and not st.st_mode & 0o222,str(path/name)
    s=os.lstat(path)
    return {'device':s.st_dev,'inode':s.st_ino,'entries':sorted(names)}

manifest_path=HERE/'review_attachment_01/manifest.json'
manifest=doc(manifest_path,'3b46f3016ac3755ac96bd8c955dee0a577f6a5b83ebf039343a799a6f55e2217')
core=doc(HERE/'freeze_attempt_01/manifest_core.json')
prepare=doc(HERE/'freeze_attempt_01/receipt.json')
attach=doc(HERE/'review_attachment_01/receipt.json')
metadata=doc(HERE/'review_attachment_01/metadata_gate.json')
bindings={
 'manifest_sha256':READS[str(manifest_path)]['sha256'],
 'core_file_sha256':READS[str(HERE/'freeze_attempt_01/manifest_core.json')]['sha256'],
 'core_sha256':core_sha(core),
 'prepare_receipt_sha256':READS[str(HERE/'freeze_attempt_01/receipt.json')]['sha256'],
 'attachment_receipt_sha256':READS[str(HERE/'review_attachment_01/receipt.json')]['sha256'],
 'metadata_gate_sha256':READS[str(HERE/'review_attachment_01/metadata_gate.json')]['sha256'],
}
assert core.get('review_receipts')=={}
stripped=copy.deepcopy(manifest);stripped['review_receipts']={}
assert stripped==core and core_sha(manifest)==bindings['core_sha256']
for key in ['manifest_sha256','core_file_sha256','core_sha256','prepare_receipt_sha256','metadata_gate_sha256']:
    assert attach[key]==bindings[key],key
assert attach['status']=='S47_C2_REVIEWS_ATTACHED_METADATA_GATE_PASSED'
assert prepare['status']=='S47_C2_CORE_FROZEN_AWAITING_TWO_REVIEWS'
assert metadata['status']=='UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY'
assert metadata['execution_authorized'] is False and metadata['manifest_sha256']==bindings['manifest_sha256']
for d in [prepare,attach]:
    assert d.get('model_or_scientific_imports',d.get('scientific_imports'))==d['pixels_decoded']==d['generation_calls']==0
    assert d['retry_permitted'] is False
    read(d['attempt_sentinel']['path'],d['attempt_sentinel']['sha256'])
assert datetime.fromisoformat(prepare['completed_utc']) < datetime.fromisoformat(attach['started_utc']) < datetime.fromisoformat(attach['completed_utc']) < datetime.fromisoformat(START)
shapes={
 'prepare':terminal(HERE/'freeze_attempt_01',{'manifest_core.json','receipt.json'}),
 'attachment':terminal(HERE/'review_attachment_01',{'manifest.json','metadata_gate.json','receipt.json'}),
}
assert shapes['prepare']['device']==attach['prepare_directory_identity']['device'] and shapes['prepare']['inode']==attach['prepare_directory_identity']['inode']
assert shapes['attachment']['device']==attach['attachment_directory_identity']['device'] and shapes['attachment']['inode']==attach['attachment_directory_identity']['inode']
roles=[]
for kind,ref in manifest['review_receipts'].items():
    review=doc(ref['path'],ref['sha256'])
    for k in ['core_file_sha256','core_sha256','prepare_receipt_sha256']: assert review[k]==bindings[k]
    assert review['author_role']=='/root' and review['reviewer_role']!='/root'
    assert review['executed'] is False and review['model_or_scientific_imports']==review['pixels_decoded']==0
    assert review['blocking_findings']==[]
    roles.append(review['reviewer_role'])
assert len(set(roles))==2
for path,digest in manifest['source_identities'].items(): read(path,digest)
for ref in manifest['parent_bindings'].values(): read(ref['path'],ref['sha256'])
for key in ['tool_source','freeze_protocol']: read(manifest['freeze_preparation'][key]['path'],manifest['freeze_preparation'][key]['sha256'])
s40=doc(manifest['parent_bindings']['s40_manifest']['path'])
controls=copy.deepcopy(manifest['controls']);controls['seed']=42
assert controls==s40['controls'] and manifest['runtime']==s40['runtime'] and manifest['generation_limits']==s40['generation_limits']
config=read(manifest['config']['path'],manifest['config']['sha256'])
old_config=read(s40['config']['path'],s40['config']['sha256'])
assert old_config.count(b'seed: 42')==1 and config==old_config.replace(b'seed: 42',b'seed: 44')+b'\n'
records={k:doc(v['path'],v['sha256']) for k,v in manifest['s39_loading_evidence'].items()}
loading_review=doc(manifest['s39_loading_review']['path'],manifest['s39_loading_review']['sha256'])
loading_manifest=doc(manifest['s39_loading_manifest']['path'],manifest['s39_loading_manifest']['sha256'])
assert loading_manifest['components']==manifest['components'] and loading_manifest['variant']==manifest['variant']
components={}
for name,spec in manifest['components'].items():
    prior=records['full_resource_gate']['components'][name]
    st=os.stat(spec['path'],follow_symlinks=False)
    current={'path':spec['path'],'size':st.st_size,'mtime_ns':st.st_mtime_ns,'device':st.st_dev,'inode':st.st_ino,'sha256':spec['sha256']}
    assert stat.S_ISREG(st.st_mode) and current==prior,name
    components[name]={'current_stat_matches_prior_full_hash_record':True,'current':current,'body_read_this_review':False}
input_st=os.stat(manifest['input_image']['path'],follow_symlinks=False)
assert stat.S_ISREG(input_st.st_mode) and input_st.st_size==manifest['input_image']['size_bytes']
# Reuse the already-reviewed read-only bundle validator; neither main nor any full execution gate is called.
gate_path=HERE/'generation_gate.py'
gate_bytes=read(gate_path,'5add4e5b6170f42ff75cdede7f40a061cd1b98a253f0fb6411444990155255ec')
gate=types.ModuleType('_c2_independent_final_readiness_gate');gate.__file__=str(gate_path);sys.modules[gate.__name__]=gate
exec(compile(gate_bytes,str(gate_path),'exec'),gate.__dict__)
validated=gate.require_published_attachment(manifest_path,bindings['manifest_sha256'],manifest)
computed,attached=gate.launch_review_bindings(manifest,bindings['manifest_sha256'])
assert computed==bindings and attached==attach['completed_utc']
gate.loading_chain(manifest)
# Separate tiny runtime resource observation, only stdlib + real psutil, never a scientific package.
probe='''import sys,os,json,hashlib,shutil\nfrom pathlib import Path\nimport psutil\np=psutil.Process();v=psutil.virtual_memory()\nprint(json.dumps({'python':sys.version,'executable':sys.executable,'psutil_version':psutil.__version__,'psutil_path':psutil.__file__,'psutil_source_sha256':hashlib.sha256(Path(psutil.__file__).read_bytes()).hexdigest(),'pid':p.pid,'process_create_time':p.create_time(),'rss':p.memory_info().rss,'memory':v._asdict(),'disk_free_bytes':shutil.disk_usage(sys.argv[1]).free,'scientific_modules_present':[m for m in sys.modules if m.split('.')[0] in {'torch','numpy','PIL','cv2','diffusers','transformers','safetensors'}]}))\n'''
run=subprocess.run([manifest['runtime']['python_executable'],'-I','-B','-c',probe,str(ROOT)],capture_output=True,text=True,timeout=30)
(OUT/'resource_probe.stdout').write_text(run.stdout);(OUT/'resource_probe.stderr').write_text(run.stderr)
assert run.returncode==0,run.stderr
runtime=json.loads(run.stdout)
assert runtime['scientific_modules_present']==[]
assert runtime['psutil_version']=='7.2.2' and runtime['psutil_source_sha256']=='d138a5786b163b56ba86ea0b2d5589dfca37e1bcdf8de1057fe1e933d6ab808a'
assert runtime['disk_free_bytes']>=manifest['generation_limits']['minimum_free_bytes']
assert all(Path(p).is_dir() for p in manifest['runtime']['pythonpath'])
scientific=[m for m in sys.modules if m.split('.')[0] in {'torch','numpy','PIL','cv2','diffusers','transformers','safetensors'}]
assert scientific==[]
fresh_paths=[HERE/'launch_authorization_01.json',HERE/'launch_authorization_attempt_01',HERE/'execution_01',HERE/'.execution_01.watchdog_failure.json',HERE/'.execution_01.supervisor_failure.json',HERE/'.review_attachment_01.preflight',HERE/'.review_attachment_01.staging',HERE/'.freeze_attempt_01.staging',Path(manifest['output_root'])]
fresh={str(p):not os.path.lexists(p) for p in fresh_paths}
assert all(fresh.values()),fresh
completed=datetime.now(timezone.utc).isoformat()
result={'schema':'s47-c2-independent-final-readiness-evidence-v1','started_utc':START,'completed_utc':completed,'bindings':bindings,'attachment_completed_utc':attached,'terminal_shapes':shapes,'validated_attachment':validated,'source_identity_count':len(manifest['source_identities']),'components':components,'runtime':runtime,'resource_probe_returncode':run.returncode,'resource_probe_source':probe,'input_image_stat_only':{'size':input_st.st_size,'device':input_st.st_dev,'inode':input_st.st_ino,'body_read':False},'fresh_reserved_paths':fresh,'future_execution_must_recheck_resources':True,'read_snapshots':READS,'executed':False,'model_or_scientific_imports':0,'pixels_decoded':0,'generation_calls':0,'input_image_bodies_read':0,'component_bodies_read':0,'tests_rerun':0,'canonical_authorization_or_launcher_called':False,'scientific_modules_present':scientific,'binding_formula_independently_computed':True,'runtime_and_all_controls_except_seed_equal_s40':True,'config_exact_declared_derivation':True}
path=OUT/'evidence.json'
with path.open('x') as f: json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps({'status':'PASS_FINITE_POST_ATTACHMENT_READINESS_EVIDENCE','path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bindings':bindings,'completed_utc':completed,'runtime':runtime},indent=2))
