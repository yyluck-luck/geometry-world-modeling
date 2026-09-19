#!/usr/bin/env python3
"""Two-stage S32 artifact snapshot, never decodes arrays or sensor images."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,re
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WORK=ROOT/'work/S32_full_delivery'
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT=WS/'outputs/S32_新片段三对照与真实照片_2026-09-07'
A=WS/'outputs/S32A_四个新片段真实推理_2026-09-07'
ASH='99e1676370403d84d3570597cb263f587a8a2a00ad5f22f829dd8e9d9afaee08'
SELSH='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
REVSH='2933625352cc2edb2d5581d78418eaffdc0ae108b8bbae41333a5fac8fbb2a97'
SCORESH='834627965eaa4198e42a8a00c43951949bf45a15bbdd0e28f871e63d98017b37'
WINDOWS=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
ENDS=['initial_0step','corrected_getter_400','global_rescaled_400']
BASE=ROOT/'work/S32_A_delivery/build_snapshot.py'
spec=importlib.util.spec_from_file_location('s32_delivery_copy_helper',BASE);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
a.OUT=OUT;a.WORK=WORK
sha=a.sha;read=a.load;utc=a.utc;link=a.link;md=a.md;save=a.save;copy=a.copy
def write(p,d):a.put_json(p,d)
def savejson(name,d):return save(name,(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def exact_source(rel,expected=None):return copy(ROOT/rel,expected=expected)
def stage():
    assert not OUT.exists() and not (WORK/'stage_state.json').exists(),'No overwrite'
    started=utc();OUT.mkdir(parents=True)
    assert sha(A/'manifest.json')==ASH
    selp=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json';assert sha(selp)==SELSH
    sel=read(selp);am=read(A/'manifest.json');arows={x['relative_path']:x for x in am['payloads']}
    expectedphotos={f['sha256']:f for w in sel['windows'] for f in w['frames']}
    photos=[]
    for old in sorted((A/'真实照片').rglob('*.png')):
        rel=old.relative_to(A);h=sha(old);assert h==arows[str(rel)]['destination_sha256'] and h in expectedphotos
        new=copy(old,rel,expected=h);f=expectedphotos[h]
        photos.append(dict(window_id=rel.parts[1],frame_index=f['index'],source_rgb_index=f['source_rgb_index'],
            rgb_time_string=f['rgb_time_string'],original_RGB_path=f['path'],source_A_snapshot=str(old),
            destination=str(new),sha256=h))
    assert len(photos)==16
    copy(A/'manifest.json',Path('证据/A_snapshot_manifest.json'),expected=ASH)
    fixed=['work/S32_input_freeze/selected_windows_rgb_sealed.json','work/S32_input_freeze/receipt.json',
        'work/S32_selection/selection_rule.md','work/S32_selection/selected_windows.json','work/S32_selection/selection_receipt.json','work/S32_selection/exposure_summary.md',
        'work/S32_A_launch/receipt.json','work/S32_A_execution/dispatch_receipt.json','work/S32_continuation/A_output_check.json',
        'work/S32_continuation/B_root_pre_review.json','work/S32_continuation/score_root_pre_review.json',
        'work/S32_continuation/independent_numeric_root_pre_review.json','work/S32_continuation/independent_numeric_v2_root_pre_review.json',
        'work/S32_continuation/freeze_and_launch_B.py','work/S32_continuation/seal_and_score.py',
        'work/S32_independent_review/A_final_pre_review.json','work/S32_independent_review/B_final_pre_review.json',
        'work/S32_independent_review/B_final_pre_review.md','work/S32_independent_review/B_source_check_receipt.json',
        'work/S32_nearby_literature/novelty_exclusions.md','work/S32_nearby_literature/retrieval_receipt.json']
    for n in ['run_inference.py','contract.json','run_consumer.py','B_plan_candidate.md','B_contract.json','B_contract_candidate.json',
        'prepare_consumer_candidate.py','B_preparation_receipt.json','B_derivation_proof.json','B_worker.diff','B_observer.diff']:
        fixed.append('work/S32_preparation/'+n)
    for n in ['score_s32.py','protocol.md','manifest.json','manifest_candidate.json','prepare_candidate.py','budget_correction_receipt.json']:
        fixed.append('work/S32_scoring_preparation/'+n)
    for rel in fixed:exact_source(rel)
    # All direct execution and verification artifacts are text/JSON; retain the failed v1 attempt.
    for directory in ['work/S32_B_launch','work/S32_B_execution','work/S32_scoring_freeze','work/S32_scoring_execution',
        'work/S32_independent_execution','work/S32_independent_execution_v2']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and p.suffix in {'.json','.txt'}:copy(p)
    for directory in ['work/S32_independent_numeric_review','work/S32_independent_numeric_review_v2']:
        for p in sorted((ROOT/directory).iterdir()):
            if p.is_file() and p.suffix in {'.json','.py','.md','.diff'}:copy(p)
    for p in sorted((ROOT/'results/S32_consumer_scoring').iterdir()):
        if p.is_file() and p.suffix in {'.json','.csv'}:copy(p)
    for p in sorted((ROOT/'work/S32_reporting').iterdir()):
        if p.is_file() and p.suffix in {'.json','.py','.md','.png','.svg','.pdf'}:copy(p)
    big=[];traces=[]
    for w in WINDOWS:
        rp=ROOT/'results/S32_consumer_windows'/w/'receipt.json';r=read(rp);copy(rp)
        assert r['window_id']==w and r['selection_sha256']==SELSH
        assert r['status']==('UNAVAILABLE' if w=='fr2_desk_j1' else 'PASS')
        for rel,h in r['outputs'].items():
            p=rp.parent/rel;assert p.is_file()
            if p.suffix in {'.npz','.npy'}:
                big.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size,window_id=w,
                    source_receipt=str(rp),copied=False,identity_scope='Inherited PASS producer/v2 audit; delivery existence/stat only, no numerical archive bytes read'))
            else:
                copy(p,expected=h)
                if p.name in ['optimization_trace.jsonl','gradient_depth_trace.jsonl']:
                    count=sum(bool(line.strip()) for line in p.read_text().splitlines());assert count==400
                    traces.append(dict(window_id=w,kind=p.name,records=count,path=str(p),sha256=h))
        ap=ROOT/'results/S32_fresh_window_inference'/w/'receipt.json';ar=read(ap);copy(ap)
        for rel,h in ar['outputs'].items():
            p=ap.parent/rel
            if p.suffix=='.npz':big.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size,window_id=w,source_receipt=str(ap),copied=False,identity_scope='Inherited A producer/root SHA check; delivery existence/stat only'))
            else:copy(p,expected=h)
    assert len(traces)==6 and sum(x['records'] for x in traces if x['kind']=='optimization_trace.jsonl')==1200
    assert sum(x['records'] for x in traces if x['kind']=='gradient_depth_trace.jsonl')==1200
    ac=read(ROOT/'work/S32_preparation/contract.json');cp=Path(ac['checkpoint']);assert cp.is_file()
    big.append(dict(path=str(cp),sha256=ac['checkpoint_sha256'],bytes=cp.stat().st_size,window_id=None,source_receipt=str(ROOT/'work/S32_preparation/contract.json'),copied=False,identity_scope='Inherited model identity, no new3GB hash'))
    assert sha(ROOT/'work/S32_independent_numeric_review_v2/receipt.json')==REVSH
    assert sha(ROOT/'results/S32_consumer_scoring/receipt.json')==SCORESH
    savejson('照片清单.json',dict(A_snapshot_manifest_sha256=ASH,selection_sha256=SELSH,photos=photos))
    savejson('大文件链接清单.json',big);savejson('完整优化日志清单.json',dict(records=traces,optimization_steps=1200,gradient_records=1200,note='Saved-log identity/line count only; no gradient recomputation'))
    copy(Path(__file__),Path('证据/build_snapshot.py'));copy(BASE,Path('证据/copy_helper_A.py'))
    state=dict(status='STAGED_WAITING_FOR_PARENT_FINAL_REPORT',started_utc=started,staged_utc=utc(),payloads=a.payloads,sources=a.sources,rewrites=a.rewrites,photos=photos,big=big,traces=traces)
    write(WORK/'stage_state.json',state);print(json.dumps(dict(status=state['status'],files_staged=len(a.payloads),photos=len(photos),linked_large_files=len(big)),indent=2))

def finish(report_sha):
    state=read(WORK/'stage_state.json');assert state['status']=='STAGED_WAITING_FOR_PARENT_FINAL_REPORT'
    assert not (OUT/'manifest.json').exists(),'No finished snapshot overwrite'
    a.payloads=state['payloads'];a.sources=state['sources'];a.rewrites=state['rewrites']
    report=ROOT/'docs/S32_RESULTS.md';assert sha(report)==report_sha
    copy(report,expected=report_sha)
    for row in a.payloads:assert sha(OUT/row['relative_path'])==row['destination_sha256']
    m=read(ROOT/'results/S32_consumer_scoring/metrics.json');rev=read(ROOT/'work/S32_independent_numeric_review_v2/receipt.json')
    assert sha(ROOT/'work/S32_independent_numeric_review_v2/receipt.json')==REVSH
    assert rev['status']=='PASS_INDEPENDENT_SAVED_NUMERIC_REVIEW'
    photos=['# 本轮16张真实照片','', '逐字复用已核S32A照片；不是生成图。本轮4窗各4张，全部保留。','']
    for w in WINDOWS:
        photos+=['## '+w,'']
        for p in state['photos']:
            if p['window_id']==w:photos +=[f"帧 {p['frame_index']}，原零基索引 {p['source_rgb_index']}，时间 {p['rgb_time_string']}。",'',f"![{w} frame {p['frame_index']}](<{p['destination']}>)",'']
    md('照片索引.md','\n'.join(photos)+'\n')
    table=['| 窗口 | 零步 AbsRel | 修getter原400步 | 400步+公共尺度恢复 |','|---|---:|---:|---:|']
    for w in WINDOWS:
        vals=[m['window_groups'][w][e]['absrel'] for e in ENDS];table.append('| '+w+' | '+' | '.join('NA' if v is None else f'{100*v:.5f}%' for v in vals)+' |')
    table.append('| 原4窗等权均值 | NA | NA | NA |')
    summary=[m['endpoint_summaries'][e]['three_preselected_pose_eligible']['absrel']*100 for e in ENDS]
    md('先读我.md',f'''# S32：三个新片段的优化结果已经核验

**三个可评分片段中，原400步优化后的深度误差都高于零步起点。** 公共比例恢复后接近零步水平，但不代表已经解决问题。以下是实际照片推理、实际几何优化及真实传感器深度评分，已由不同作者用另一算式复核；不是模拟数据。

{'\n'.join(table)}

AbsRel 是绝对相对深度误差，越低越好；每格是该窗4帧等权均值。fr2_desk_j1按原小于20毫秒一对一规则缺相机配对，A推理成功但B三端点均NA；没有删窗或换片段，所以原四窗均值仍为NA。另附三个预定相机可用窗口的描述均值为 **{summary[0]:.5f}% / {summary[1]:.5f}% / {summary[2]:.5f}%**，不能代替四窗均值。

- {link('看完整图',OUT/'证据/work/S32_reporting/s32_window_absrel.png')}：全部36实际帧点和9均值，首窗明确NA。
- {link('看16张真实照片',OUT/'照片索引.md')}，或打开 {link('照片文件夹',OUT/'真实照片')}。
- {link('完整S32报告',OUT/'证据/docs/S32_RESULTS.md')}；{link('完整48行CSV',OUT/'证据/results/S32_consumer_scoring/per_frame.csv')}。
- {link('全部1200步及1200条梯度记录清单',OUT/'完整优化日志清单.json')}：保存日志已复制，不把日志范数称为再次反传。
- {link('不同作者v2复核回执',OUT/'证据/work/S32_independent_numeric_review_v2/receipt.json')}；{link('首轮失败回执',OUT/'证据/work/S32_independent_numeric_review/receipt.json')}。

A实际用了49.558569秒，4次新网络推理、16次逐帧头前向。B实际北京时间03:44:57–03:46:23完成三个窗口各400步，共1200步，另保留一个缺相机窗口。主评分北京时间03:46:37–03:46:38完成；不同作者v2复核04:06:31–04:06:33通过，完整48行/36评分/12NA及2,359,296个尺度诊断像素均纳入；AbsRel/RMSE最大算术差约1.11×10⁻¹⁶。

第一次独立复核因把二维深度叶误当一维而失败，原件保留；另立v2仅修形状断言后完整重算通过，没有放宽指标容差，也没有重跑网络或GA。当前图首已标注算术核验通过；plotted_data.json保留首次制图时整份字节，里面的pending只是历史状态，最新身份见图注和新回执。

本轮相机是给定GT光学位姿；这两个场景已有历史曝光，每个4帧短窗仅约0.10秒，局部帧有相关性，不能当成独立样本作显著性结论。三控都是普通对照，不是已证明的新方法；也未完成old4→new4完整记忆链或VMem视频生成。下一步科学判断以完整报告为准，本快照不擅自启动新实验。

{link('大数组、模型与历史结果链接',OUT/'大文件与历史结果链接.md')}只指向本机原文件，不复制数百MB数组。{link('逐载荷SHA清单',OUT/'manifest.json')}记录来源、时间与检查范围。证据目录内执行前计划按其历史时点保留；这份快照不会随主项目自动更新。
''')
    b=['# 大文件与历史结果链接','', '以下模型、NPZ、NPY保留原位置；本交付只核文件存在和大小，SHA来自已封存生产/核验回执，未重新读取数组字节。','']
    for x in state['big']:b.append(f"- {link((x['window_id']+'/' if x['window_id'] else '')+Path(x['path']).name,x['path'])}；{x['bytes']}字节；SHA `{x['sha256']}`。")
    b += ['', '此前共同4帧是另一批历史输入，不能替代本轮结果：', '', '- '+link('S30',ROOT/'docs/S30_RESULTS.md'),'- '+link('S31',ROOT/'docs/S31_RESULTS.md')]
    md('大文件与历史结果链接.md','\n'.join(b)+'\n')
    links=[]
    for p in sorted(OUT.rglob('*.md')):
        for match in a.LINK.finditer(p.read_text()):
            raw=match.group(2);raw=raw[1:-1] if raw.startswith('<') else raw
            if raw.startswith(('http://','https://','mailto:','#')):continue
            q=Path(a.unquote(raw.partition('#')[0]));q=q if q.is_absolute() else (p.parent/q).resolve()
            assert q.exists() or q==OUT/'manifest.json',f'Missing local link: {p}: {q}'
            links.append(dict(markdown=str(p.relative_to(OUT)),target=str(q)))
    savejson('本地链接核验.json',dict(status='PASS_FINAL_MANIFEST_CREATED_LAST',checked_utc=utc(),local_link_count=len(links),links=links))
    for p,h in a.sources.items():assert sha(p)==h,'Source changed during snapshot: '+p
    for row in a.payloads:assert sha(OUT/row['relative_path'])==row['destination_sha256']
    manifest=dict(schema='s32-complete-user-snapshot-v1',status='PASS',started_utc=state['started_utc'],completed_utc=utc(),snapshot=str(OUT),
        report_source_sha256=report_sha,main_score_receipt_sha256=SCORESH,independent_v2_receipt_sha256=REVSH,
        selection_sha256=SELSH,A_snapshot_manifest_sha256=ASH,payload_count=len(a.payloads),payloads=a.payloads,
        payload_bytes=sum(x['bytes'] for x in a.payloads),photos=16,optimization_log_records=1200,gradient_log_records=1200,
        retained_NA_score_rows=12,complete_score_rows=48,linked_large_file_count=len(state['big']),
        delivery_only=dict(new_model=0,new_GA=0,new_score=0,sensor_GT_files_read=0,prediction_array_bytes_read=0,photo_pixel_decodes=0),
        limitations=['Artifact delivery with different-author arithmetic already completed, not another scientific recomputation','Historical v1 failure preserved','Large files only linked with inherited SHA','Snapshot excludes automatic future updates','Manifest excludes itself; external delivery receipt binds final manifest'])
    write(OUT/'manifest.json',manifest)
    assert all(Path(x['target']).exists() for x in links)
    receipt=dict(status='PASS_COMPLETE_S32_USER_SNAPSHOT',started_utc=state['started_utc'],completed_utc=utc(),snapshot=str(OUT),manifest_sha256=sha(OUT/'manifest.json'),
        payload_count=len(a.payloads),total_files=sum(p.is_file() for p in OUT.rglob('*')),total_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
        local_links_verified=len(links),photos_SHA_verified=16,all_payload_SHA_verified=True,all_sources_unchanged=True,
        script_sha256=sha(__file__),report_source_sha256=report_sha,scientific_execution_by_delivery=0)
    write(WORK/'receipt.json',receipt);print(json.dumps(receipt,indent=2,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['stage','finish']);p.add_argument('--report-sha');args=p.parse_args()
    if args.mode=='stage':stage()
    else:assert args.report_sha;finish(args.report_sha)
