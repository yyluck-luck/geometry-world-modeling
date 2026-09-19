"""Root boundary: all fixed-window endpoints first, then GT bytes, then score."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
PREP=ROOT/'work/S32_scoring_preparation'
OUT=ROOT/'work/S32_scoring_freeze'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    candidate=PREP/'manifest_candidate.json'
    assert sha(candidate)=='d81e719029732d2fb1219aa04175d6af173db620feeead980decf83503ccd186'
    c=read(candidate)
    assert c['resource']==dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3)
    for p,h in c['control_sha256'].items():assert sha(p)==h,p
    assert sha(PREP/'score_s32.py')=='adb646284110b38741c311e893064558ca4d409ecc3b5e7e75c4540f1203c319'
    review=ROOT/'work/S32_continuation/score_root_pre_review.json'
    rr=read(review);assert rr['status']=='PASS_ROOT_SCORER_SOURCE_REVIEW' and rr['runner_sha256']==sha(PREP/'score_s32.py')
    dispatch=ROOT/'work/S32_B_execution/dispatch_receipt.json'
    dr=read(dispatch)
    assert dr['status']=='COMPLETE_FIXED_WINDOW_MATRIX_SEALED'
    bcontract=ROOT/'work/S32_preparation/B_contract.json'
    assert sha(bcontract)==dr['contract_sha256']
    selection=read(c['selection_path'])
    assert sha(c['selection_path'])==c['selection_sha256']
    assert [w['id'] for w in c['windows']]==[w['id'] for w in selection['windows']]==list(dr['windows'])
    assert not (PREP/'manifest.json').exists() and not Path(c['output_root']).exists()
    OUT.mkdir(exist_ok=False)
    barrier=dict(status='CHECKING_ALL_WINDOW_TERMINALS_AND_OUTPUTS_BEFORE_GT',started_utc=now(),B_contract_sha256=sha(bcontract),dispatch_sha256=sha(dispatch),selection_sha256=c['selection_sha256'],window_receipts={},producer_outputs={},sensor_depth_PNG_bytes_read=0,root_prediction_array_decodes=0)
    write(OUT/'endpoint_barrier.json',barrier)
    for window in c['windows']:
        p=Path(window['producer_receipt']['path']);h=sha(p);r=read(p)
        assert h==dr['windows'][window['id']]['receipt_sha256']
        assert r['window_id']==window['id'] and r['selection_sha256']==c['selection_sha256'] and r['contract_sha256']==sha(bcontract)
        assert r['status'] in ('PASS','FAILED','UNAVAILABLE')
        if window['id']=='fr2_desk_j1':assert r['status']=='UNAVAILABLE' and r['missing_pose_frame_indices']==list(range(4))
        else:assert r['status'] in ('PASS','FAILED')
        window['producer_receipt']['sha256']=h
        barrier['window_receipts'][str(p)]=h
        window['availability']='AVAILABLE' if r['status']=='PASS' else 'UNAVAILABLE_MISSING_POSE' if r['status']=='UNAVAILABLE' else 'UNAVAILABLE_PRODUCER_FAILED'
        window['reason']='' if r['status']=='PASS' else r.get('reason','Recorded terminal producer failure')
        if r['status']=='PASS':
            for name,expected in r['outputs'].items():
                product=p.parent/name
                assert not Path(name).is_absolute() and product.resolve().is_relative_to(p.parent.resolve())
                assert sha(product)==expected,product
                barrier['producer_outputs'][str(product)]=expected
        for name,item in window['endpoints'].items():
            if r['status']=='PASS':
                q=p.parent/(name+'.npz');assert r['outputs'][q.name]==barrier['producer_outputs'][str(q)]
                item.update(status='AVAILABLE',path=str(q),sha256=r['outputs'][q.name])
            else:item.update(status='UNAVAILABLE',path=None,sha256=None)
    barrier.update(status='PASS_ALL_WINDOW_TERMINALS_AND_AVAILABLE_ENDPOINTS_SEALED_BEFORE_ROOT_GT_READ',completed_utc=now(),prespecified_windows=4,endpoint_groups=12,available_windows=sum(w['availability']=='AVAILABLE' for w in c['windows']))
    write(OUT/'endpoint_barrier.json',barrier)
    # First sensor-depth file-byte access in this root script occurs only below.
    gt=dict(status='READING_GT_BYTES_ONLY_AFTER_ENDPOINT_SEAL',started_utc=now(),endpoint_barrier_sha256=sha(OUT/'endpoint_barrier.json'),files=[],image_decodes=0)
    write(OUT/'GT_byte_freeze.json',gt)
    for window in c['windows']:
        for frame in window['frames']:
            if window['availability']=='AVAILABLE' and frame['depth_path'] is not None:
                p=Path(frame['depth_path']);assert p.parent.name=='depth' and p.suffix=='.png'
                h=sha(p);frame['depth_sha256']=h;frame['depth_identity_status']='ACTUAL_ROOT_BYTES_SEALED_AFTER_ALL_ENDPOINTS'
                gt['files'].append(dict(window=window['id'],index=frame['index'],path=str(p),sha256=h,bytes=p.stat().st_size))
            else:frame['depth_sha256']=None;frame['depth_identity_status']='NOT_READ_UNAVAILABLE_WINDOW_OR_ASSOCIATION'
    gt.update(status='PASS_GT_BYTES_SEALED_NO_IMAGE_DECODE',completed_utc=now(),files_read=len(gt['files']))
    write(OUT/'GT_byte_freeze.json',gt)
    c.update(status='FROZEN',frozen_utc=now(),candidate_sha256=sha(candidate),root_review=str(review),upstream_seal_receipts_status='ACTUAL_ROOT_ENDPOINT_THEN_GT_BYTE_SEALS')
    c['upstream_seal_receipts']=[dict(path=str(p),sha256=sha(p)) for p in [OUT/'endpoint_barrier.json',OUT/'GT_byte_freeze.json']]
    c['control_sha256'].update({str(review):sha(review),str(bcontract):sha(bcontract)})
    manifest=PREP/'manifest.json';write(manifest,c)
    write(OUT/'freeze_receipt.json',dict(status='FROZEN',frozen_utc=c['frozen_utc'],manifest_sha256=sha(manifest),endpoint_barrier_sha256=sha(OUT/'endpoint_barrier.json'),GT_byte_freeze_sha256=sha(OUT/'GT_byte_freeze.json'),root_script_sha256=sha(__file__),new_GT_file_bytes_read=len(gt['files']),image_decodes=0))
    sys.path.insert(0,str(ROOT/'scripts'));from research_log import append_event
    append_event('S32B全窗口终态封存后才读取评分深度字节',f'四固定窗及所有可用端点已封存；可用窗{barrier["available_windows"]}，原4窗/12组/48行分母保持。根随后实际读{len(gt["files"])}个sensor-depth文件的字节并封SHA，尚无根图像解码或数值评分。正式评分合同现冻结。',evidence=[str(OUT/'endpoint_barrier.json'),str(OUT/'GT_byte_freeze.json'),str(manifest)],next_step='单次运行原冻结指标评分，再执行不同公式全量复核。',occurred_at=c['frozen_utc'],time_source='actual root endpoint and GT byte barrier clock')
    parent=ROOT/'scripts/s26b_consumer_baseline.py';assert sha(parent)=='61e00503829dad7e9d1260fb408b81e8b281198e3cbf4bcab8367a493f982834'
    spec=importlib.util.spec_from_file_location('s32_root_score_supervisor',parent);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    b.WORK=ROOT/'work/S32_scoring_execution';b.WORK.mkdir(exist_ok=False)
    for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
    command=[sys.executable,str(PREP/'score_s32.py'),'--manifest',str(manifest),'--sha256',sha(manifest)]
    b.supervised(command,'scoring',120,2*1024**3)
    result=read(Path(c['output_root'])/'receipt.json');assert result['status']=='PASS'
    append_event('S32主评分实际完成',f'主评分产出完整48行/12组；可用窗{result["available_windows"]}，实际GT图像解码{result["GT_images_decoded"]}张，每可用帧供三端点共用。原缺失NA保留；待不同公式独立复核后解释精确结论。',evidence=[str(Path(c['output_root'])/'receipt.json'),str(b.WORK/'scoring/receipt.json')],next_step='全量独立数值复核，随后汇报各窗口零步/400步/公共尺度结果。',occurred_at=result['completed_utc'],time_source='actual scorer completion receipt')
    print(json.dumps(dict(status='PASS_MAIN_SCORE_NOT_INDEPENDENTLY_VERIFIED',manifest_sha256=sha(manifest),scored_receipt_sha256=sha(Path(c['output_root'])/'receipt.json'),GT_images_decoded=result['GT_images_decoded'],available_windows=result['available_windows']),ensure_ascii=False))

if __name__=='__main__':main()
