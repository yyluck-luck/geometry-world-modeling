from pathlib import Path
import hashlib,re
base=Path(__file__).resolve().parents[1]
sha=lambda name:hashlib.sha256((base/name).read_bytes()).hexdigest()
def set_pin(path,key,digest):
 s=path.read_text();s,count=re.subn(r'(^'+re.escape(key)+r' = ")[0-9a-f]{64}("$)',lambda m:m[1]+digest+m[2],s,flags=re.M)
 assert count==1,(path,key,count);path.write_text(s)
set_pin(base/'generation_gate.py','C2_PROTOCOL_SHA256',sha('PROTOCOL.md'))
set_pin(base/'generation_gate.py','FREEZE_PROTOCOL_SHA256',sha('FREEZE_PROTOCOL.md'))
set_pin(base/'freeze_c2_manifest.py','FREEZE_PROTOCOL_SHA256',sha('FREEZE_PROTOCOL.md'))
for filename in ['launch_generation.py','create_launch_authorization.py']:set_pin(base/filename,'GATE_SHA256',sha('generation_gate.py'))
p=base/'freeze_c2_manifest.py';s=p.read_text()
for name in ['generation_gate.py','runtime_adapter.py','launch_generation.py','create_launch_authorization.py','PROTOCOL.md']:
 s,count=re.subn(r'("'+re.escape(name)+r'": ")[0-9a-f]{64}("[,\n])',lambda m:m[1]+sha(name)+m[2],s)
 assert count==1,(name,count)
p.write_text(s)
print({p.name:sha(p.name) for p in base.iterdir() if p.name in ['PROTOCOL.md','FREEZE_PROTOCOL.md','generation_gate.py','runtime_adapter.py','launch_generation.py','freeze_c2_manifest.py','create_launch_authorization.py','inference_seed44.yaml','static_selftest.py']})
