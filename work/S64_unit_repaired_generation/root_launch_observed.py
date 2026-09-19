"""Observe the reviewed one-attempt launcher; preserve its exact external exit."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D=R/'work/S64_unit_repaired_generation'
O=D/'external_launch_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
authorization=json.loads((D/'ROOT_AUTHORIZATION_ORCHESTRATION.json').read_text())
assert authorization['returncode']==0
assert sha(D/'launch_generation.py')=='2998383f07bd9437440b24f465ef5624d7291890b8f750c9b6ce2795c33bfb35'
manifest=D/'review_attachment_01/manifest.json'
assert len(sys.argv)==2
assert sha(manifest)==sys.argv[1]
assert not O.exists()
O.mkdir()
sys.path.insert(0,str(R/'scripts'))
from research_log import append_event
argv=[str(R/'.venv-cut3r/bin/python'),'-B',str(D/'launch_generation.py'),'--manifest',str(manifest),'--manifest-sha256',sha(manifest),'--execution-directory',str(D/'execution_01')]
start=datetime.now(timezone.utc).isoformat();t0=time.monotonic()
with (O/'stdout.txt').open('xb') as out, (O/'stderr.txt').open('xb') as err:
    process=subprocess.Popen(argv,cwd=str(R),stdout=out,stderr=err)
    initial=dict(started_utc=start,argv=argv,supervisor_pid=process.pid,status='REVIEWED_LAUNCHER_STARTED_NOT_YET_MODEL_VERIFIED',scientific_status='NOT_EVALUATED')
    (O/'started.json').write_text(json.dumps(initial,ensure_ascii=False,indent=2)+'\n')
    append_event('启动S64单位修复变体唯一受控CPU生成进程',f'两项新发布后审查及唯一授权后启动reviewed launcher，PID{process.pid}。CPU8/FP32/576/两批各50步，原定总上限3600秒。进程启动不等于模型已载入或生成完成；后续读取真实运行证据。',[str((O/'started.json').relative_to(R))],'监测实际加载与两批生成，保留失败与外部退出码；保持原C2失败和原cohort边界，准备最小结果读回。')
    print(json.dumps(initial,ensure_ascii=False),flush=True)
    external_timeout=False
    try: code=process.wait(timeout=3900)
    except subprocess.TimeoutExpired:
        external_timeout=True
        process.terminate()
        try: code=process.wait(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill();code=process.wait(timeout=15)
result=dict(**initial,completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-t0,returncode=code,external_timeout=external_timeout,stdout_sha256=sha(O/'stdout.txt'),stderr_sha256=sha(O/'stderr.txt'))
result['status']='EXTERNALLY_OBSERVED_RETURN_PENDING_INDEPENDENT_TERMINAL_REVIEW'
with (O/'receipt.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
append_event('S64单位修复变体生成进程已返回',f'外部观测returncode={code}，elapsed={result["elapsed_seconds"]:.3f}秒，external_timeout={external_timeout}。须复核原始terminal/worker/archive证据才能确认生成，不能据退出码声称画质或创新。',[str((O/'receipt.json').relative_to(R))],'独立核正式终端、失败路径与archive，再进行实际单位调用、两批产物和第一批前缀身份读回；不补原cohort或声称创新。')
print(json.dumps(result,ensure_ascii=False),flush=True)
