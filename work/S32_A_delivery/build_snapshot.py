#!/usr/bin/env python3
"""S32 A byte-copy delivery only. No numerical libraries or model execution."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
import hashlib, json, re, traceback

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WORK=ROOT/'work/S32_A_delivery'
OUT=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S32A_四个新片段真实推理_2026-09-07')
SELECTION_SHA='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
CONTRACT_SHA='1749d83fac56a8c7f50b74d37e2278239df25534318967fa93f4798eb5054124'
WINDOWS=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
LINK=re.compile(r'(!?\[[^\]\n]*\])\((<[^>\n]*>|[^)\n]*)\)')
payloads=[]; sources={}; rewrites=[]
def utc():return datetime.now(timezone.utc).isoformat()
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(Path(p).read_bytes())
def load(p):return json.loads(Path(p).read_text())
def put_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def link(label,p):return f'[{label}](<{p}>)'
def save(rel,b,source=None,source_sha=None,kind='generated'):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),f'No overwrite: {p}'
    p.write_bytes(b);assert sha(p)==digest(b)
    payloads.append(dict(relative_path=str(rel),source_path=str(source) if source else None,
        source_sha256=source_sha,destination_sha256=digest(b),bytes=len(b),kind=kind))
    return p
def md(rel,s):return save(rel,s.encode('utf-8'))
def copy(src,rel=None,expected=None):
    src=Path(src);assert src.suffix.lower() not in {'.npz','.pth','.pt'},'Large numerical archives are link only'
    b=src.read_bytes();h=digest(b)
    if expected:assert h==expected,f'Identity changed: {src}'
    sources[str(src)]=h
    rel=Path(rel) if rel else Path('证据')/src.relative_to(ROOT)
    if src.suffix=='.md':
        # Preserve original bytes, then make the readable Markdown portable across the snapshot layout.
        save(str(rel)+'.source.txt',b,src,h,'source_exact_copy')
        def convert(m):
            label,target=m.groups();raw=target[1:-1] if target.startswith('<') else target
            if raw.startswith(('http://','https://','mailto:','#')):return m.group(0)
            pathname,sep,frag=raw.partition('#');p=Path(unquote(pathname))
            p=p if p.is_absolute() else (src.parent/p).resolve()
            new=str(p)+(sep+frag if sep else '')
            rewrites.append(dict(source=str(src),old=raw,new=new))
            return label+'(<'+new+'>)'
        s=LINK.sub(convert,b.decode('utf-8'))
        if src.name in {'plan_candidate.md','exposure_summary.md','A_final_pre_review.md'}:
            s='> 历史阶段原文：其中“尚未运行/准备”等措辞指文件原记录时点；A 当前结果见本快照《先读我》。\n\n'+s
        return save(rel,s.encode('utf-8'),src,h,'markdown_absolute_links_with_original_preserved')
    return save(rel,b,src,h,'source_exact_copy')

def main():
    started=utc();assert not OUT.exists(),'Existing snapshot must not be overwritten'
    OUT.mkdir(parents=True)
    selection_path=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json'
    contract_path=ROOT/'work/S32_preparation/contract.json'
    assert sha(selection_path)==SELECTION_SHA and sha(contract_path)==CONTRACT_SHA
    s=load(selection_path);c=load(contract_path)
    assert [w['id'] for w in s['windows']]==WINDOWS==[w['id'] for w in c['windows']]
    check=load(ROOT/'work/S32_continuation/A_output_check.json');launch=load(ROOT/'work/S32_A_launch/receipt.json')
    dispatch=load(ROOT/'work/S32_A_execution/dispatch_receipt.json')
    assert check['status']=='PASS_ROOT_A_ARCHIVE_IDENTITIES' and check['payload_files_verified']==32
    assert launch['status']=='PASS_A_INFERENCE_ONLY' and launch['returncode']==0 and launch['contract_sha256']==CONTRACT_SHA
    assert dispatch['status']=='PASS_A_INFERENCE_ONLY'
    entries={w['window']:w for w in check['windows']}
    fixed=[
      'docs/S32_A_RESULTS.md',
      'work/S32_preparation/run_inference.py','work/S32_preparation/prepare_candidate.py',
      'work/S32_preparation/plan_candidate.md','work/S32_preparation/contract.json',
      'work/S32_preparation/contract_candidate.json','work/S32_preparation/source_read_manifest.json',
      'work/S32_preparation/preparation_receipt.json',
      'work/S32_input_freeze/selected_windows_rgb_sealed.json','work/S32_input_freeze/receipt.json',
      'work/S32_selection/selection_rule.md','work/S32_selection/rule_freeze_receipt.json',
      'work/S32_selection/selected_windows.json','work/S32_selection/selection_receipt.json',
      'work/S32_selection/exposure_summary.md','work/S32_selection/metadata_label_correction_receipt.json',
      'work/S32_independent_review/A_final_pre_review.json','work/S32_independent_review/A_final_pre_review.md',
      'work/S32_independent_review/A_source_check_receipt.json',
      'work/S32_continuation/root_pre_review.json','work/S32_continuation/A_output_check.json',
      'work/S32_continuation/freeze_and_launch_A.py',
      'work/S32_A_launch/receipt.json','work/S32_A_launch/stdout.txt','work/S32_A_launch/stderr.txt',
      'work/S32_A_execution/dispatch_receipt.json',
      'work/S32_nearby_literature/novelty_exclusions.md','work/S32_nearby_literature/retrieval_receipt.json']
    for rel in fixed:copy(ROOT/rel)
    photo_records=[];big=[];time_rows=[];small_count=0
    photo_index=['# 本轮 16 张真实原图','',
        '这些是 TUM 数据集原始 RGB 照片的逐字副本，不是生成图，也没有改色、裁剪或放大。每个窗口从 0 到 3 顺序推理。','']
    for w,cw in zip(s['windows'],c['windows']):
        wid=w['id'];directory=ROOT/'results/S32_fresh_window_inference'/wid
        rp=directory/'receipt.json';r=load(rp);e=entries[wid]
        assert sha(rp)==e['receipt_sha256'] and r['status']=='PASS_INFERENCE_SEALED' and r['window']==wid
        assert r['contract_sha256']==CONTRACT_SHA and r['frames_completed']==4
        assert r['counts']=={'model_calls':1,'state_initializations':1,'downstream_head_calls':4}
        assert all(r[k]==0 for k in ['sensor_depth_bytes_read','GT_pose_file_bytes_read','GA_calls','backward_calls','Adam_steps'])
        assert len(r['outputs'])==8 and r['full_saved_return_head_comparisons']==24
        copy(rp,expected=e['receipt_sha256'])
        for name,h in sorted(r['outputs'].items()):
            p=directory/name;assert p.is_file()
            if p.suffix=='.npz':
                big.append(dict(path=str(p),window_id=wid,sha256=h,bytes=p.stat().st_size,
                    identity_basis='Inherited sealed producer SHA and root 32-payload check; delivery only checked existence/stat, not archive bytes',copied=False))
            else:copy(p,expected=h);small_count+=1
        for name in ['receipt.json','stdout.txt','stderr.txt']:copy(ROOT/'work/S32_A_execution'/wid/name)
        photo_index+=['## '+wid,'']
        for f,cf in zip(w['frames'],cw['frames']):
            for key in ['index','source_rgb_index','path','rgb_time','sha256']:assert f[key]==cf[key]
            rel=Path('真实照片')/wid/f"frame_{f['index']:02d}_{Path(f['path']).name}"
            dest=copy(Path(f['path']),rel,expected=f['sha256'])
            photo_records.append(dict(window_id=wid,index=f['index'],source_rgb_index=f['source_rgb_index'],
                rgb_time_string=f['rgb_time_string'],source_path=f['path'],snapshot_path=str(dest),sha256=f['sha256']))
            photo_index += [f"第 {f['index']+1} 张；原零基索引 {f['source_rgb_index']}；时间 {f['rgb_time_string']}。",'',f'![{wid} frame {f["index"]}](<{dest}>)','']
        time_rows.append({k:e[k] for k in ['window','started_utc','completed_utc','model_load_seconds','inference_with_archival_seconds','outer_wall_seconds','peak_rss_bytes','receipt_sha256']})
    assert len(photo_records)==16 and small_count==12 and len(big)==20
    checkpoint=Path(c['checkpoint']);assert checkpoint.is_file() and checkpoint.stat().st_size==c['checkpoint_stat'][0]
    big.append(dict(path=str(checkpoint),window_id=None,sha256=c['checkpoint_sha256'],bytes=checkpoint.stat().st_size,
        identity_basis=c['checkpoint_identity_basis']+'; delivery did not rehash checkpoint',copied=False))
    elapsed=(datetime.fromisoformat(launch['completed_utc'])-datetime.fromisoformat(launch['started_utc'])).total_seconds()
    assert abs(elapsed-49.558569)<1e-9
    photo_path=md('照片索引.md','\n'.join(photo_index))
    save('照片清单.json',(json.dumps(dict(selection_sha256=SELECTION_SHA,photos=photo_records),ensure_ascii=False,indent=2)+'\n').encode())
    save('大文件链接清单.json',(json.dumps(big,ensure_ascii=False,indent=2)+'\n').encode())
    timing=['# A 实际运行记录','',f"实际 UTC {launch['started_utc']} 至 {launch['completed_utc']}；北京时间 2026-09-07 03:31:56 至 03:32:45。外层总计 {elapsed:.6f} 秒。",'',
      '| 窗口 | 加载模型秒 | 推理含存档秒 | 每窗外控秒 | 峰值 RSS 字节 |',
      '|---|---:|---:|---:|---:|']
    for e in time_rows:timing.append(f"| {e['window']} | {e['model_load_seconds']:.6f} | {e['inference_with_archival_seconds']:.6f} | {e['outer_wall_seconds']:.6f} | {e['peak_rss_bytes']} |")
    timing += ['', '加载、推理含存档、外控是三个不同计时口径。外控包含导入、预处理和校验；不是模型纯前向耗时。每窗 CPU8、180 秒、16 GiB 上限，四窗顺序完成。', '',
      '计数：4 次窗口级网络调用、16 次逐帧下游头前向、每帧 6 个输出，共 96 张量；每窗新建一次递推状态，窗内四帧沿原逻辑递推。0 GA／MST／Adam／反传／sensor-depth 读取。', '',
      '这里复用生产记录与根任务已完成的 32 载荷 SHA 核验。本交付重新核 16 原图、12 小载荷和所复制文件的字节身份，未重读预测 NPZ 或重算准确率。', '',
      link('实际外层回执',OUT/'证据/work/S32_A_launch/receipt.json')+'；'+link('根载荷核验',OUT/'证据/work/S32_continuation/A_output_check.json')+'。']
    md('实际运行记录.md','\n'.join(timing)+'\n')
    bigmd=['# 大文件与历史结果','', '以下只提供本机绝对链接，未复制模型或预测 NPZ。SHA 沿用已封存身份；本次交付仅检查文件存在与大小，不声称又独立重哈希大文件。','']
    for row in big:bigmd += [f"- {link((row['window_id']+'/' if row['window_id'] else '模型权重/')+Path(row['path']).name,row['path'])}，{row['bytes']} 字节；SHA `{row['sha256']}`。"]
    bigmd += ['', '此前 common4 的数值比较属于历史窗口，不能作为本轮 16 张照片的准确率。', '',
      '- '+link('S30：旧窗口两臂优化结果',ROOT/'docs/S30_RESULTS.md'),
      '- '+link('S31：旧窗口单标量恢复诊断',ROOT/'docs/S31_RESULTS.md'), '',
      '完整 VMem 视频生成仍未完成；本包是 CUT3R 几何预测的 A 阶段，不是生成视频或完整项目验收。']
    md('大文件与历史结果链接.md','\n'.join(bigmd)+'\n')
    md('先读我.md',f'''# S32A：真实照片与实际推理已经交付

这次用四个预定片段的 **16 张真实照片**，实际运行了本机 CUT3R 网络。照片就在 {link('真实照片文件夹',OUT/'真实照片')}，也可打开 {link('按顺序看 16 张照片',photo_path)}。它们是原数据逐字副本，没有生成或修饰。

实际运行于北京时间 **2026-09-07 03:31:56–03:32:45**，总计 **49.558569 秒**。共 4 次窗口网络调用、16 次逐帧头前向，保存 96 个输出张量。每窗加载约 3.1 秒、推理含存档约 5.8 秒、外控约 12.37–12.39 秒；{link('完整计时和证据',OUT/'实际运行记录.md')} 已保留各自口径。

**现在完成的是 A：真实推理与结果存档。** 这不表示新片段的深度更准确，也没有证明创新、生成视频或完成整个科研项目。本包不新增模型运行、优化、评分或绘图。

| 固定窗口 | 原零基照片索引 | A 推理 | B 相机条件 |
|---|---|---|---|
| fr2_desk_j1 | 987–990 | 4 张成功 | 4 张均缺原规则相机配对，三端点保留 NA |
| fr2_desk_j2 | 1974–1977 | 4 张成功 | 4/4 配对 |
| fr1_xyz_j1 | 264–267 | 4 张成功 | 4/4 配对 |
| fr1_xyz_j2 | 529–532 | 4 张成功 | 4/4 配对 |

fr1 这 8 张曾用于 S24；fr2 这 8 张不在已核 S21/S22 前 300 张内，其他历史曝光未知。两个场景都已使用，不能称盲测或未见场景。四张连续照片每窗约跨 0.10 秒，也不是长序列证据。

B 由主任务继续单独准备／冻结／执行；本快照只验收 A，不将 B 的并行进度冒充已评分。下一步需比较同一起点的零步、原 400 步、公共比例恢复三个普通对照，全部端点封存后再读传感器深度评分；缺相机窗不换片段。原四窗 × 三端点 × 四帧的 48 行完整分母保留。

进一步查阅：

- {link('S32A 完整报告',OUT/'证据/docs/S32_A_RESULTS.md')}。
- {link('本轮近邻文献与创新排除',OUT/'证据/work/S32_nearby_literature/novelty_exclusions.md')}：普通相机约束、保护局部几何或尺度恢复不能直接当新方法。
- {link('大文件与前轮结果链接',OUT/'大文件与历史结果链接.md')}：大模型和预测档案保留原位；S30/S31 是前轮窗口，未混入本轮结果。
- {link('逐载荷 SHA 清单',OUT/'manifest.json')}：源文件与副本身份、实际制作时点、范围均可查。

证据里的执行前计划与前审按原历史时点保留；其中“未运行”不改变 A 已实际完成的状态。原文另存 `.source.txt`，可读 Markdown 的本地证据链接改为绝对路径。快照是本次制作时点的副本，后续主项目更新不会自动写入这里。
''')
    copy(Path(__file__),Path('证据/build_snapshot.py'))
    # Validate all Markdown active local links. manifest.json is a planned output in this same transaction.
    links=[]
    for path in sorted(OUT.rglob('*.md')):
        for m in LINK.finditer(path.read_text()):
            target=m.group(2);raw=target[1:-1] if target.startswith('<') else target
            if raw.startswith(('http://','https://','mailto:','#')):continue
            p=Path(unquote(raw.partition('#')[0]));p=p if p.is_absolute() else (path.parent/p).resolve()
            assert p.exists() or p==OUT/'manifest.json',f'Missing local link: {path}: {p}'
            links.append(dict(markdown=str(path.relative_to(OUT)),target=str(p),exists=True,check='file/directory existence only'))
    save('本地链接核验.json',(json.dumps(dict(status='PASS_LOCAL_TARGETS_WITH_MANIFEST_CREATED_LAST',checked_utc=utc(),local_links=len(links),targets=links,rewritten_links=rewrites),ensure_ascii=False,indent=2)+'\n').encode())
    for p,h in sources.items():assert sha(p)==h,f'Source changed during copying: {p}'
    for row in payloads:assert sha(OUT/row['relative_path'])==row['destination_sha256']
    manifest=dict(schema='s32-a-user-snapshot-v1',status='PASS_DELIVERY_ONLY',started_utc=started,completed_utc=utc(),
        snapshot=str(OUT),selection_sha256=SELECTION_SHA,contract_sha256=CONTRACT_SHA,
        historical_scientific_execution={'started_utc':launch['started_utc'],'completed_utc':launch['completed_utc'],'elapsed_seconds':elapsed},
        payload_count=len(payloads),payload_bytes=sum(x['bytes'] for x in payloads),payloads=payloads,
        original_photos_copied=16,producer_small_payloads_copied=12,producer_NPZ_linked_only=20,checkpoint_linked_only=1,
        delivery_scope={'new_model_calls':0,'new_GA':0,'new_scoring':0,'new_plots':0,'sensor_PNG_bytes':0,'prediction_NPZ_bytes':0,'checkpoint_bytes':0,'RGB_files_byte_copied_and_SHA_verified':16,'RGB_pixel_decodes':0},
        provenance_scope='Team member different from A producer; artifact copy and existing-record consistency only, not independent numerical inference or full experimental audit',
        limits=['A only; no B or accuracy completion claim','Selected windows from already used scenes, not blind data','Parent output hash review reused for large archives, no fresh large-byte hash','No future automatic refresh; historical plans retain original-time language','Manifest excludes itself; final completion receipt records manifest SHA'])
    put_json(OUT/'manifest.json',manifest)
    assert all(Path(row['target']).exists() for row in links)
    receipt=dict(status='PASS_SNAPSHOT_DELIVERY',started_utc=started,completed_utc=utc(),snapshot=str(OUT),
        manifest_sha256=sha(OUT/'manifest.json'),script_sha256=sha(Path(__file__)),payload_count=len(payloads),
        total_files=len(list(OUT.rglob('*')))-sum(p.is_dir() for p in OUT.rglob('*')),
        payload_bytes=manifest['payload_bytes'],total_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
        original_photos=16,producer_small_payloads=12,linked_npz=20,linked_checkpoint=1,local_links_checked=len(links),
        all_local_targets_exist=True,all_payload_SHA_rechecked=True,all_copied_sources_unchanged=True,
        scientific_work_performed=False,command=['python3',str(Path(__file__))],scope=manifest['provenance_scope'])
    put_json(WORK/'receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except Exception:
        put_json(WORK/'failed_attempt.json',dict(status='FAILED_DELIVERY_ATTEMPT_PRESERVED',utc=utc(),traceback=traceback.format_exc(),snapshot=str(OUT)))
        raise
