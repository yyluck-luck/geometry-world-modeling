#!/usr/bin/env python3
"""One reviewed continuation: wait for this download, freeze, run, seal and verify."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,sys,time,traceback
from research_log import append_event
R=Path(__file__).resolve().parents[1]
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def main():
    out=R/'work/S17B_dispatch';assert not out.exists();out.mkdir()
    receipt=dict(started_utc=utc(),status='WAITING_FOR_DOWNLOAD',operations=[],model_dispatches=0)
    def save():receipt['updated_utc']=utc();dump(out/'receipt.json',receipt)
    def run(name,command):
        receipt['phase']=name;save();start=utc();print(name,flush=True)
        with (out/f'{name}_stdout.txt').open('w') as stdout,(out/f'{name}_stderr.txt').open('w') as stderr:
            result=subprocess.run(command,stdout=stdout,stderr=stderr,cwd=R)
        receipt['operations'].append(dict(name=name,command=command,started_utc=start,completed_utc=utc(),returncode=result.returncode));save()
        if result.returncode:raise RuntimeError(f'{name} returned {result.returncode}; original evidence preserved')
    start=time.monotonic();save()
    download=R/'work/S17A_checkpoint_resume_ranges/receipt.json'
    try:
        while True:
            try:state=json.loads(download.read_text())
            except json.JSONDecodeError:time.sleep(.1);continue
            if state['status']=='PASS':break
            if state['status']!='RUNNING':raise RuntimeError('Download not PASS; no model dispatched')
            if time.monotonic()-start>1300:raise TimeoutError('Wait ended; download is not authorized to exceed its own contract')
            time.sleep(5)
        append_event('S17A公开512权重完整获取并通过作者SHA','保留首轮中断前缀并续传所有剩余字节；完整3173761006B和固定作者LFS SHA通过，仍0反序列化/模型调用。',[str(download)],'进行已审S17B冻结和两实拍真实运行',occurred_at=state['completed_utc'],time_source='Backfilled from actual completed downloader receipt')
        run('freeze',[sys.executable,str(R/'scripts/freeze_s17b_dpt.py'),'--download-receipt',str(download),'--peer-review',str(R/'work/S17B_review/review_receipt.json'),'--root-review',str(R/'work/S17B_root_review/receipt.json')])
        manifest=R/'docs/S17B_EXECUTION_MANIFEST.json';result_dir=R/'results/S17B_dpt_two_frames';control=R/'work/S17B_execution/model'
        receipt.update(status='RUNNING_MODEL',model_dispatches=1);save()
        append_event('S17B冻结后开始两张真实照片512 DPT运行','已核完整ZIP CRC、99原源码/两实拍和独立前审；CPU8FP32seed0，外部600s32GiB保护，0GT和query。',[str(manifest),'work/S17B_root_freeze/receipt.json'],'保存真实19数组后封存与不同数学核验')
        run('controlled_model',[sys.executable,str(R/'scripts/run_s14d_controlled.py'),'--manifest',str(manifest),'--output',str(result_dir),'--control',str(control)])
        meta=json.loads((result_dir/'run_metadata.json').read_text());caller=control/'caller_receipt.json'
        assert meta['status']=='SUCCESS' and json.loads(caller.read_text())['status']=='PASS'
        seal=R/'docs/S17B_OUTPUT_SEAL.json';assert not seal.exists()
        identities={str(p):sha(p) for p in sorted(result_dir.iterdir()) if p.is_file()}
        for p in [manifest,caller,control/'stdout.txt',control/'stderr.txt']:identities[str(p)]=sha(p)
        dump(seal,dict(schema='s17b-output-seal-v1',sealed_utc=utc(),identities=identities,model_calls=1,history_rgb=2,target_rgb=0,target_depth=0,query_calls=0))
        append_event('S17B实际512 DPT两实拍前向完成','真实两图产生12输出头、5state、2pose数组；仅组件成功，0目标图/GT/query/video。已封存全部原始输出和caller。',[str(result_dir/'run_metadata.json'),str(seal),str(caller)],'不同作者NumPy/SciPy代码重读真实档案核验',occurred_at=meta['completed_utc'],time_source='Backfilled from actual model receipt')
        verify=R/'results/S17B_dpt_independent'
        run('independent_verify',[str(R/'.venv/bin/python'),str(R/'scripts/verify_s17b_dpt_history.py'),'--manifest',str(manifest),'--manifest-sha256',sha(manifest),'--seal',str(seal),'--seal-sha256',sha(seal),'--run-dir',str(result_dir),'--caller-receipt',str(caller),'--output',str(verify)])
        v=json.loads((verify/'verification.json').read_text());assert v['status']=='PASS'
        append_event('S17B真实档案的不同实现核验通过','NumPy/SciPy重开19数组，独立位姿变换、DPT尺寸与真实编码器计数、全部文件/数组身份和外控通过；读取权重/图像字节校验但0反序列化/图片解码，不评深度准确率。',[str(verify/'verification.json')],'制作固定两实拍和无米标定深度图，接续VMem嵌入几何',occurred_at=v['completed_utc'],time_source='Backfilled from actual independent verification receipt')
        receipt['status']='PASS'
    except BaseException as e:
        receipt.update(status='FAILED',error=repr(e),traceback=traceback.format_exc())
        append_event('S17B接续调度遇到未完成条件','阶段停止并保留原回执：'+str(e),[str(out/'receipt.json')],'查实际失败阶段，在新合同/目录修复；不复跑成功阶段')
    finally:
        receipt['completed_utc']=utc();save();print(json.dumps(receipt,indent=2),flush=True)
    return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
