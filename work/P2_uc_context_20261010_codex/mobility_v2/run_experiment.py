"""Persistent single-GPU execution and CPU scoring, with a hard total cap."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent.parent
OPS=Path(__file__).resolve().parent
ALLOCATION=json.loads((HERE/'ALLOCATION_MOBILITY_V2.json').read_text())
GPU=ALLOCATION['uuid']
import socket
assert ALLOCATION['host']==socket.gethostname()
assert (HERE/'MOBILITY_CLAIM_V2').is_dir()
ROOT=Path('/mnt/gluster_dcpu/yiyangliu/gwm_s134')
PY=str(ROOT/'env/bin/python')
ARMS=['real','zero','permuted','low_cfg']
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def save(name,d): (HERE/name).write_text(json.dumps(d,indent=2)+'\n')


def run():
    mobility=json.loads((OPS/'FREEZE.json').read_text())
    assert all(sha(OPS/k)==v for k,v in mobility['files'].items())
    frozen=json.loads((HERE/'FINGERPRINT.json').read_text())
    assert all(sha(HERE/k)==v for k,v in frozen['files'].items())
    inputs=json.loads((HERE/'INPUT_MANIFEST.json').read_text())
    # Inputs are revalidated once at actual execution, after queue waiting.
    for name,item in inputs['files'].items(): assert sha(Path(name))==item['sha256'],name
    for item in inputs['baseline'].values(): assert sha(Path(item['path']))==item['sha256']
    env=os.environ.copy();env.update(RUN_ROOT=str(ROOT/'src'),WEIGHTS=str(ROOT/'weights'),
        XDG_CACHE_HOME=str(ROOT/'cache'),MPLCONFIGDIR=str(ROOT/'cache/mpl'),HF_HOME=str(ROOT/'cache/hf'),
        PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=GPU,
        VARIANT='A',ADAPTER='/mnt/gluster_dcpu/yiyangliu/gwm_s141/runs/A/adapter_final.pt',
        DATA_ROOT=str(ROOT/'data/s139_stage'),WARP_DIR=str(ROOT/'data/S140_warps_chess'),SHARD='0/1',
        OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    out=HERE/'results'
    plan=json.loads((HERE/'PLAN.json').read_text())
    save('ENVIRONMENT.json',{'utc':now(),'python':sys.version,'packages':subprocess.check_output([PY,'-m','pip','freeze'],text=True),
        'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu','--format=csv,noheader'],text=True)})
    fresh_gpu=subprocess.check_output(['nvidia-smi','-i',GPU,'--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    mem,util=map(int,fresh_gpu.strip().split(','));assert mem<100 and util<5,'GPU allocation changed; no launch'
    # Recheck the complete queue eligibility predicate after input hashing.
    import importlib.util
    spec=importlib.util.spec_from_file_location('p2_allocation_gate',OPS/'queue.py')
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    sessions=subprocess.run(['tmux','list-sessions','-F','#S'],capture_output=True,text=True,timeout=10,check=True).stdout.splitlines()
    reserved={3,4} if any(x.startswith(tuple('s'+str(k) for k in range(143,150))) for x in sessions) else set()
    inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu,driver_version','--format=csv,noheader,nounits'],text=True,timeout=15)
    occupied=set(subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader,nounits'],text=True,timeout=15).splitlines())
    assert GPU in {g['uuid'] for g in gate.candidates(inventory,occupied,reserved)},'GPU eligibility changed; no launch'
    assert json.loads((HERE/'MOBILITY_CLAIM_V2'/'owner.json').read_text())['host']==socket.gethostname()
    out.mkdir(exist_ok=False)
    started=time.monotonic();save('GPU_STARTED.json',{'utc':now(),'cap_seconds':7200,'gpu_uuid':GPU,'gpu_index':ALLOCATION['index'],'host':ALLOCATION['host'],'operational_fingerprint':mobility['fingerprint']})
    def generate(arm,plan_file,seeds,folder):
        d=out/folder;assert not d.exists()
        e=env.copy();e.update(P2_ARM=arm,PLAN=str(HERE/plan_file),SEEDS=seeds,ARM_OUT=str(d))
        with (HERE/f'{folder}.log').open('w') as log:
            subprocess.run([PY,str(HERE/'generate.py')],env=e,stdout=log,stderr=subprocess.STDOUT,
                timeout=max(1,7200-(time.monotonic()-started)),check=True)
        return d
    replay=generate('native','REPLAY_PLAN.json','3','replay')
    filename=f"{plan['contexts'][0]['ctx_key']}__s3.npy"
    assert sha(replay/filename)==inputs['baseline'][filename]['sha256'],'native replay mismatch'
    recs=[json.loads(x) for p in replay.glob('RUNS*.jsonl') for x in p.read_text().splitlines() if x]
    assert len(recs)==1
    estimate=recs[0]['seconds']*48*1.25+600
    remaining=7200-(time.monotonic()-started)
    save('REPLAY_TIMING.json',{'replay_match':True,'generation_seconds':recs[0]['seconds'],
        'estimated_remaining_seconds':estimate,'remaining_seconds':remaining,'timing_gate_pass':estimate<=remaining})
    if estimate>remaining:
        elapsed=time.monotonic()-started
        save('GPU_FINISHED.json',{'utc':now(),'reserved_seconds':elapsed,'gpu_hours':elapsed/3600,'timing_gate_stop':True})
        save('RESULT.json',{'status':'COMPUTE_CAP','reason':'Full mandatory panel cannot fit frozen cap; no controls removed.'});return
    native=out/'native';native.mkdir()
    for name,item in inputs['baseline'].items(): os.symlink(item['path'],native/name)
    for arm in ARMS: generate(arm,'PLAN.json','3,4',arm)
    elapsed=time.monotonic()-started;assert elapsed<=7200
    save('GPU_FINISHED.json',{'utc':now(),'reserved_seconds':elapsed,'gpu_hours':elapsed/3600})
    expected={f"{c['ctx_key']}__s{s}.npy" for c in plan['contexts'] for s in [3,4]}
    seal={};traces={}
    import numpy as np
    for arm in ['native']+ARMS:
        paths={p.name:p for p in (out/arm).glob('*.npy')};assert set(paths)==expected
        for name,p in paths.items():
            a=np.load(p,allow_pickle=False);assert a.shape==(4,3,576,576) and np.isfinite(a).all()
            seal[f'{arm}/{name}']=sha(p)
            if arm!='native':
                t=json.loads(p.with_suffix('.trace.json').read_text());assert len(t['steps'])==50
                sig=(t['initial_context_noise_sha256'],[(x['cpu_rng'],x['cuda_rng']) for x in t['steps']])
                if name in traces: assert traces[name]==sig,'unequal RNG stream'
                else: traces[name]=sig
    native_trace=json.loads((replay/filename.replace('.npy','.trace.json')).read_text())
    assert traces[filename]==(native_trace['initial_context_noise_sha256'],[(x['cpu_rng'],x['cuda_rng']) for x in native_trace['steps']])
    save('OUTPUT_SEAL.json',{'utc':now(),'files':seal,'count':len(seal),'boundary':'All outputs sealed before scorer is started.'})
    cpu=env.copy();cpu['CUDA_VISIBLE_DEVICES']=''
    for arm in ['native']+ARMS:
        with (HERE/f'score_{arm}.log').open('w') as log:
            subprocess.run([PY,str(HERE/'score_s140.py'),str(out/arm),str(ROOT/'data/s139_datasets'),
                str(HERE/'PLAN.json'),str(ROOT/'data/S140_warps_chess'),str(out/f'SCORES_{arm}.json')],
                env=cpu,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
    subprocess.run([PY,str(HERE/'analyze.py'),str(HERE)],env=cpu,check=True,timeout=120)


if __name__=='__main__':
    try:run()
    except BaseException as e:
        save('EXECUTION_FAILURE.json',{'utc':now(),'type':type(e).__name__,'error':str(e),'status':'INVALID_OR_INCOMPLETE_NOT_SCIENTIFIC_NEGATIVE'})
        if (HERE/'GPU_STARTED.json').exists() and not (HERE/'GPU_FINISHED.json').exists():
            begin=datetime.datetime.fromisoformat(json.loads((HERE/'GPU_STARTED.json').read_text())['utc'])
            elapsed=(datetime.datetime.now(datetime.timezone.utc)-begin).total_seconds()
            save('GPU_FINISHED.json',{'utc':now(),'reserved_seconds':elapsed,'gpu_hours':elapsed/3600,'execution_failed':True})
        raise
