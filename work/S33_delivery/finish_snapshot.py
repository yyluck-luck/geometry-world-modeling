#!/usr/bin/env python3
"""Finish a staged S33 user snapshot. Byte-copy only, never loads arrays/GT."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, traceback

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WORK=ROOT/'work/S33_delivery'
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT=WS/'outputs/S33_尺度约束四条件与真实照片_2026-09-07'
BASE=ROOT/'work/S32_A_delivery/build_snapshot.py'
REV=ROOT/'work/S33_independent_numeric_review/receipt.json'
REV_SHA='057b369b82e6b16af640222c16ada5536f67851b06dee7d248ce61eee6d21b0e'
SCORE_SHA='30976ca99eaf1b9e107aaa2001b3c60537f456d19073eaec3420d9bda37ef1f6'
SELECT_SHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
WINDOWS=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
spec=importlib.util.spec_from_file_location('s33_snapshot_copy_helper',BASE)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
a.OUT=OUT;a.WORK=WORK
sha=a.sha;read=a.load;copy=a.copy;md=a.md;link=a.link

def savejson(name,d):
    return a.save(name,(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())

def main(report_sha):
    started=a.utc()
    assert not (OUT/'manifest.json').exists(),'No finished snapshot overwrite'
    state=read(WORK/'stage_state.json')
    assert state['status']=='STAGED_REPORT_AND_INDEPENDENT_REVIEW_PENDING'
    a.payloads=state['payloads'];a.sources=state['sources'];a.rewrites=state['rewrites']
    report=ROOT/'docs/S33_RESULTS.md'
    assert sha(report)==report_sha
    assert sha(REV)==REV_SHA and read(REV)['status']=='PASS_INDEPENDENT_S33_SAVED_REVIEW'
    assert sha(ROOT/'results/S33_pair_scale_scoring/receipt.json')==SCORE_SHA
    copy(report,expected=report_sha)
    for directory in ['work/S33_independent_numeric_review','work/S33_independent_execution']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and p.suffix in {'.json','.py','.md','.txt','.csv','.diff'} and '__pycache__' not in p.parts:
                copy(p)
    copy(ROOT/'work/S33_root_preparation/independent_source_pre_review.json')
    for p in sorted((ROOT/'work/S33_reporting').iterdir()):
        if p.is_file() and p.suffix in {'.json','.py','.md','.txt','.png','.pdf','.svg'}:
            copy(p)
    # The old image is preserved in-project; include its archive record and link it explicitly.
    archive=ROOT/'work/S33_reporting/history_v1_before_verified_status'
    copy(archive/'archive_receipt.json')
    copy(Path(__file__),Path('证据/finish_snapshot.py'))
    report_text=report.read_text()
    table=report_text.split('| 固定窗口 |',1)[1].split('\n\n',1)[0]
    table='| 固定窗口 |'+table
    photos=['# 四个预定窗口的16张真实照片','',
      '这是已核 S32 快照照片的逐字副本。本轮 S33 复用这些照片产生的已保存网络输出，未重新运行网络。三个相机可用窗口的12张参与本轮新GA；fr2_desk_j1的4张保留展示，但因缺给定相机，本轮没有GA或评分。','']
    for w in WINDOWS:
        photos+=['## '+w,'']
        for p in state['photos']:
            if p['window_id']==w:
                photos += [f"帧 {p['frame_index']}，原零基索引 {p['source_rgb_index']}，RGB时间 {p['rgb_time']}。",'',f"![{w} frame {p['frame_index']}](<{p['snapshot_path']}>)",'']
    md('照片索引.md','\n'.join(photos)+'\n')
    md('先读我.md',f'''# S33：普通尺度约束在三个短片段上有效

**这次接受了一项有效的普通基线改进：训练中固定共同配对尺度后，三个可评分片段的深度误差都低于零步和事后比例恢复。** 完整评分与不同作者的保存量算术复核已实际通过。这个结果帮助我们排除基线中的具体问题，尚不是已经证明的新方法。

{table}

表中是 AbsRel（绝对相对深度误差，越低越好），每格为4帧等权均值。全部四个预定窗的均值仍是 **NA**；最后一行只描述原先固定的三个相机完整窗。新条件在这三个窗口的 RMSE 和 δ1 也更好；这不是“每一帧都更好”的声明。

- {link('完整报告与局限',OUT/'证据/docs/S33_RESULTS.md')}。
- {link('看四条件结果图',OUT/'证据/work/S33_reporting/s33_four_conditions.png')}：全部48个实际帧点、12个窗口均值，首窗缺失明确保留，统一0–50%坐标。
- {link('看16张真实照片',OUT/'照片索引.md')}，或打开 {link('真实照片文件夹',OUT/'真实照片')}。照片不是生成图；S33新GA只使用三个相机可用窗的12张，另4张是预定但缺相机的窗口。
- {link('完整64行CSV',OUT/'证据/results/S33_pair_scale_scoring/per_frame.csv')}：旧S32的48行原值导入，新条件16行中12行评分、4行NA。合计48行实际评分、16行NA。
- {link('本轮1200步及保存日志清单',OUT/'本轮完整日志清单.json')}；{link('不同作者实际复核回执',OUT/'证据/work/S33_independent_numeric_review/receipt.json')}；{link('完整复核保存结果',OUT/'证据/work/S33_independent_numeric_review/recomputed.json')}。

本轮新增3个窗口各400步，共1200次真实Adam/反向传播，复用S32已保存预测头，**0次新网络推理**。实际生产为北京时间 **2026-09-07 04:21:37–04:23:02**，外控总计85.793940秒；主评分04:24:46完成，独立复核04:39:24–04:39:28完成。旧三控没有重跑；新条件也没有再加事后k。

独立核验检查完整64行结构及旧48原值，另式复算12个新评分与缺失规则，并核查1200条优化、1200条梯度、1200条尺度保存记录。AbsRel/RMSE最大算术差约4.16×10⁻¹⁷／2.78×10⁻¹⁷。保存梯度记录的核查不等于重新反传，数值复核也不是外部团队复现实验。

相机使用给定GT光学位姿；这些场景和短窗已经看过，每窗仅约0.10秒，局部帧相关。不能据此声称盲测泛化、灾难遗忘解决、生成视频提升或项目全部完成。共同pair尺度约束是已有思路，下一步按报告回到真实old4→new4消费者，不能把本轮全深度可训练条件直接推广到旧深度冻结的记忆链。

{link('大数组与S32历史证据链接',OUT/'大数组与历史证据链接.md')}保留原位的大文件入口；本包未复制模型或NPZ。{link('逐载荷SHA清单',OUT/'manifest.json')}记录每份副本的来源、身份、实际制作时点和范围。

执行前计划和前审中的“未运行”属于历史时点；当前状态以实际回执为准。图的 `plotted_data.json` 保留首次制作的完整字节，其中PENDING是历史标记，当前核验状态见新图、图注和绑定回执。旧PENDING图另存原项目历史目录。本快照是当前时点的交付，不会自动覆盖之后的研究进度。
''')
    b=['# 大数组与前轮证据','',
      '下列大文件只链接。SHA沿用已封存生产与独立核验身份，本交付只核路径存在/大小，没有读取数组字节或再次评分。','']
    for row in state['large_links']:
        p=Path(row['path']);assert p.exists() and p.stat().st_size==row['bytes']
        b.append(f"- {link(row['window_id']+'/'+str(p.relative_to(ROOT/'results/S33_pair_scale_control'/row['window_id'])),p)}；{row['bytes']}字节；SHA `{row['sha256']}`。")
    previous=Path(state['previous_snapshot'])
    b+=['','S32是前一轮已完成的三条件结果，其大证据保留原件：','',
      '- '+link('S32完整历史快照',previous/'先读我.md'),
      '- '+link('S32大文件/模型入口',previous/'大文件与历史结果链接.md'),
      '- '+link('S32全部优化与梯度日志',previous/'完整优化日志清单.json'),
      '- '+link('S32独立复核首跑失败原件',ROOT/'work/S32_independent_numeric_review/receipt.json'),
      '- '+link('S32独立复核v2通过原件',ROOT/'work/S32_independent_numeric_review_v2/receipt.json'),
      '- '+link('S33旧PENDING图与回执归档',archive),
      '', '本轮原始初始化33张量、全部末端raw等已列上方；不要把重放或保存量核查当历史未保存状态。完整VMem视频生成未执行。']
    md('大数组与历史证据链接.md','\n'.join(b)+'\n')
    links=[]
    for p in sorted(OUT.rglob('*.md')):
        for match in a.LINK.finditer(p.read_text()):
            raw=match.group(2);raw=raw[1:-1] if raw.startswith('<') else raw
            if raw.startswith(('http://','https://','mailto:','#')):continue
            q=Path(a.unquote(raw.partition('#')[0]));q=q if q.is_absolute() else (p.parent/q).resolve()
            assert q.exists() or q==OUT/'manifest.json',f'Missing local link: {p}: {q}'
            links.append(dict(markdown=str(p.relative_to(OUT)),target=str(q)))
    savejson('本地链接核验.json',dict(status='PASS_MANIFEST_CREATED_LAST',checked_utc=a.utc(),count=len(links),links=links))
    for p,h in a.sources.items():assert sha(p)==h,'Copied source changed: '+p
    for row in a.payloads:assert sha(OUT/row['relative_path'])==row['destination_sha256']
    manifest=dict(schema='s33-complete-user-snapshot-v1',status='PASS',started_utc=state['started_utc'],finalization_started_utc=started,completed_utc=a.utc(),snapshot=str(OUT),
      report_source_sha256=report_sha,main_score_receipt_sha256=SCORE_SHA,independent_review_receipt_sha256=REV_SHA,selection_sha256=SELECT_SHA,
      previous_S32_snapshot_manifest_sha256=state['previous_manifest_sha256'],payload_count=len(a.payloads),payloads=a.payloads,payload_bytes=sum(x['bytes'] for x in a.payloads),
      original_photos=16,photos_in_new_GA=12,photos_from_missing_pose_window=4,score_rows=64,scored_rows=48,NA_rows=16,old_imported_rows=48,new_scored_rows=12,new_NA_rows=4,
      new_optimization_records=1200,new_gradient_records=1200,new_scale_records=1200,large_files_linked_only=len(state['large_links']),
      delivery_only=dict(new_model=0,new_GA=0,new_score=0,new_plots=0,sensor_GT_bytes=0,prediction_array_bytes=0,RGB_pixel_decodes=0),
      limitations=['Artifact delivery only; previously completed numeric audit is cited, not rerun','Given GT camera and already seen short windows; no novelty or full-video/project completion','Large NPZ/NPY and S32 historic evidence remain absolute local links','Old figure/PENDING data creation provenance retained; current review identity explicit','Manifest excludes itself; external completion receipt binds its SHA','Only this snapshot and time range checked; no automatic coverage of future changes'])
    a.put_json(OUT/'manifest.json',manifest)
    assert all(Path(x['target']).exists() for x in links)
    receipt=dict(status='PASS_COMPLETE_S33_USER_SNAPSHOT',started_utc=state['started_utc'],finalization_started_utc=started,completed_utc=a.utc(),snapshot=str(OUT),manifest_sha256=sha(OUT/'manifest.json'),
      payload_count=len(a.payloads),total_files=sum(p.is_file() for p in OUT.rglob('*')),payload_bytes=manifest['payload_bytes'],total_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
      original_photos=16,local_links_verified=len(links),all_local_targets_exist=True,all_payload_SHA_verified=True,all_copied_sources_unchanged=True,
      report_source_sha256=report_sha,script_sha256=sha(__file__),stage_script_sha256=sha(WORK/'stage_snapshot.py'),source_stage_state_sha256=sha(WORK/'stage_state.json'),
      actual_command=['python3',str(Path(__file__)),'--report-sha',report_sha],scientific_execution_by_delivery=0)
    a.put_json(WORK/'receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report-sha',required=True);args=p.parse_args()
    try:main(args.report_sha)
    except Exception:
        a.put_json(WORK/'failed_finalization_attempt.json',dict(status='FAILED_DELIVERY_ATTEMPT_PRESERVED',utc=a.utc(),error=traceback.format_exc()))
        raise
