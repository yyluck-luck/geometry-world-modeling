#!/usr/bin/env python3
"""S34 final user snapshot, byte copy and Markdown links only. No array decode."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,traceback
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WORK=ROOT/'work/S34_reporting'
OUT=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S34_固定旧地图三条件与真实照片_2026-09-07')
HELPER=ROOT/'work/S32_A_delivery/build_snapshot.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest()=='77412e0090cf4c2db7bff5254c00f4397068a27b8b9d33a75c4045de114e87e0'
spec=importlib.util.spec_from_file_location('s34_byte_delivery_helper',HELPER)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.OUT=OUT;a.WORK=WORK
sha=a.sha;read=a.load;link=a.link;md=a.md
ENDS=['old_fixed_zero','old_fixed_free_400','old_fixed_common_scale_400']
MODES=['common_old']+ENDS
SCORE=ROOT/'results/S34_depth_scoring'
PROD=ROOT/'results/S34_geometry_producer'
CONS=ROOT/'results/S34_original_consumer'
SOURCE_IDS={ROOT/'work/S34_preparation/contract.json':'2c51a060a294a335c3844b04dc78028bd687b724266792ea89f1a6cb597cb465',
SCORE/'receipt.json':'4189323ed3715844033c2b13b1c754011f85261dc0df25cb9d31bfbb02bcb9b5',
ROOT/'work/S34_independent_numeric_review/receipt.json':'2885ee548926e8bf2bea65e157604428228c70d109e5316b8819c1b908512afa',
ROOT/'work/S34_consumer_numeric_review/executed/receipt.json':'59d688e7c15ce6e0e374f1e41c98b3922d7e8d17ba0c644e08ea72779f726316',
WORK/'delivery_receipt.json':'52906560a1c74dbde85169ae1bf3cf4832a3cf041b9bd6c2cc1479f09a3244ac'}
copied=set()
def copy(p,relative=None,expected=None):
    p=Path(p)
    if p in copied:return
    relative=Path(relative) if relative else Path('证据')/p.relative_to(ROOT)
    if p.suffix=='.npz':
        raw=p.read_bytes();h=a.digest(raw)
        if expected:assert h==expected
        a.sources[str(p)]=h;a.save(relative,raw,p,h,'source_exact_copy_saved_array_no_decode')
    else:a.copy(p,relative,expected)
    copied.add(p)
def sj(name,v):return a.save(name,(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def main(report_sha):
    started=a.utc();assert not OUT.exists(),'Do not overwrite an existing snapshot'
    report=ROOT/'docs/S34_RESULTS.md';assert sha(report)==report_sha,'Root-approved final report only'
    for p,h in SOURCE_IDS.items():assert sha(p)==h,p
    assert read(SCORE/'receipt.json')['status']=='PASS'
    assert read(ROOT/'work/S34_independent_numeric_review/receipt.json')['status']=='PASS_INDEPENDENT_S34_GEOMETRY_SCORE_REVIEW'
    assert read(ROOT/'work/S34_consumer_numeric_review/executed/receipt.json')['status']=='PASS_INDEPENDENT_SAVED_CONSUMER_REVIEW'
    assert read(WORK/'delivery_receipt.json')['actual_visual_QA'] is True
    OUT.mkdir(parents=True)
    c=read(ROOT/'work/S34_preparation/contract.json');m=read(SCORE/'metrics.json')
    copy(report,expected=report_sha);copy(ROOT/'docs/S34_NEXT_STEP.md')
    dirs=['work/S34_preparation','work/S34_consumer_preparation','work/S34_scoring_preparation',
        'work/S34_independent_review','work/S34_root_preparation','work/S34_independent_numeric_review',
        'work/S34_consumer_numeric_review','work/S34_launch','work/S34_producer_execution',
        'work/S34_consumer_execution','work/S34_scoring_execution','work/S34_independent_execution',
        'work/S34_consumer_review_execution']
    for rel in dirs:
        for p in sorted((ROOT/rel).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.md','.txt','.csv','.diff'}:copy(p)
    for p in sorted(WORK.iterdir()):
        if not p.is_file() or p.name.startswith('snapshot_'):continue
        if p.suffix in {'.json','.py','.md','.txt','.png','.pdf','.svg'}:
            if p.name.startswith('s34_renderer_depths.'):copy(p,Path('渲染深度图')/p.name)
            elif p.name.startswith('s34_depth_scores.'):copy(p,Path('结果图')/p.name)
            else:copy(p)
    for p in sorted(SCORE.iterdir()):
        if p.is_file():copy(p,expected=read(SCORE/'receipt.json').get('outputs',{}).get(p.name))
    big=[];logs=[]
    for mode in MODES:
        directory=PROD/mode;rec=read(directory/'receipt.json');assert rec['status']=='PASS'
        copy(directory/'receipt.json')
        for name,h in sorted(rec['outputs'].items()):
            p=directory/name;assert p.is_file()
            if p.suffix=='.npz' and p.stat().st_size>1024**2:
                big.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size,kind='S34_geometry_archive',copied=False,
                    identity_basis='Sealed producer/independent receipt identity; delivery checks stat only for this large file'))
            else:copy(p,expected=h)
        if mode in ENDS[1:]:
            for name in ['optimization_trace.jsonl','gradient_depth_trace.jsonl','s34_scale_trace.jsonl']:
                p=directory/name;rows=[json.loads(line) for line in p.read_text().splitlines()]
                assert len(rows)==400 and [r['iteration'] for r in rows]==list(range(400))
                logs.append(dict(endpoint=mode,path=str(p),snapshot_path=str(OUT/'证据'/p.relative_to(ROOT)),sha256=sha(p),records=400,kind=name))
    cr=read(CONS/'receipt.json');assert cr['status']=='PASS_ORIGINAL_CONSUMER_COMPONENTS'
    copy(CONS/'receipt.json')
    for name,h in sorted(cr['outputs'].items()):copy(CONS/name,expected=h)
    # Original dependencies and large prior input arrays remain locally accessible, not copied again.
    for p,h in c['assets'].items():
        q=Path(p)
        if q.suffix=='.npz':big.append(dict(path=p,sha256=h,bytes=q.stat().st_size,kind='prior_saved_head_or_initialization',copied=False,identity_basis='Formal S34 contract inherited SHA, existence/size only in delivery'))
    unique={r['path']:r for r in big};big=list(unique.values())
    photos=[];photomd=['# 本轮八张原始真实照片','',
        '这是 TUM fr2_desk 首八张 RGB 照片的逐字副本，没有生成、裁剪、调色或缩放。S34 复用它们已经保存的 CUT3R 预测头，本轮没有重新运行网络。帧 0–3 建共同旧地图并固定旧深度，帧 4–7 为新增帧，只有新增四帧做本轮传感器深度评分。','']
    assert [f['index'] for f in c['frames']]==list(range(8))
    for f in c['frames']:
        p=Path(f['path']);rel=Path('真实照片')/f"frame_{f['index']:02d}_{p.name}";copy(p,rel,expected=f['sha256'])
        row=dict(index=f['index'],role='old_fixed' if f['index']<4 else 'new_scored',rgb_time=f['rgb_time'],source_path=str(p),snapshot_path=str(OUT/rel),sha256=f['sha256'])
        photos.append(row);photomd += [f"## 帧 {f['index']} · {'固定旧帧' if f['index']<4 else '新增评分帧'}",'',f"RGB 时间：{f['rgb_time']}。",'',f"![真实照片 frame {f['index']}](<{OUT/rel}>)",'']
    md('照片索引.md','\n'.join(photomd)+'\n');sj('照片清单.json',dict(producer_contract_sha256=SOURCE_IDS[ROOT/'work/S34_preparation/contract.json'],photos=photos,byte_copies_verified=True,pixel_decodes=0))
    sj('完整优化日志清单.json',dict(optimization_records=800,gradient_records=800,scale_records=800,files=logs,scope='Copies of already validated saved records, no backward rerun'))
    sj('大数组链接清单.json',big)
    bigmd=['# 大数组与原依赖入口','',
        '下列文件保留原位。本包没有复制大体积几何初末数组、旧网络头或模型依赖；每项 SHA 来自已封存合同/回执，本次交付只核存在和大小，没有重新读取这些大数组字节。三幅原始 render 与四份完整地图/cache 等较小 consumer 保存档案已逐字复制在本包证据目录，未重新计算。','']
    for r in big:bigmd.append(f"- {link(r['kind']+'/'+Path(r['path']).name,r['path'])}：{r['bytes']} 字节；SHA `{r['sha256']}`。")
    bigmd+=['','## 原代码/历史条件（不作为本轮新增执行）','']
    for field in ['parent_manifest','parent_runner','s28_runner','s30_runner','optimizer_source','old_receipt','old_inputs_seal','s30_initial_gate','control_array']:
        bigmd.append('- '+link(field,c[field]))
    for e in ['docs/S33_RESULTS.md','docs/S29_RESULTS.md','work/S33_next_decision/review.md']:
        bigmd.append('- '+link(e,ROOT/e))
    bigmd+=['','以上均为本机绝对路径；迁移到另一台电脑需一并迁移原项目。完整 VMem 视频生成未执行，最终 context IDs 缺 NMS/latent 历史，不能由这些候选名单代替。']
    md('大数组与原依赖链接.md','\n'.join(bigmd)+'\n')
    table=['| 普通条件 | 新4帧平均 AbsRel ↓ | RMSE（米）↓ | δ1 ↑ |','|---|---:|---:|---:|']
    labels=['零步','自由优化400步','共同尺度约束400步']
    for label,e in zip(labels,ENDS):
        g=m['primary_new4'][e];table.append(f"| {label} | {100*g['absrel']:.4f}% | {g['rmse_m']:.6f} | {100*g['delta1']:.4f}% |")
    md('先读我.md',f'''# S34：固定旧地图的真实三条件对照

**真实八帧链条已经跑通：共同旧地图只建一次，随后三份副本各加入新四帧，并实际执行原地图渲染与来源票权。** 新四帧深度误差的平均 AbsRel 为零步 4.6059%、自由优化 4.3474%、共同尺度约束 4.3221%。主评分和两个不同作者的保存量复核均实际 PASS；共同尺度约束相对自由优化的差别很小，这是一项普通基线对照，尚不是创新成果或完整项目完成。

{chr(10).join(table)}

AbsRel 是绝对相对深度误差，RMSE 是以米计的均方根误差，δ1 是预测在指定比例范围内的像素比例。均值按四个预定新增帧等权计算；帧7在两个400步条件下的AbsRel都略差于零步，不能说每帧都进步。像素和相邻帧不能当独立重复实验，没有显著性检验。

- {link('按顺序看八张真实照片',OUT/'照片索引.md')}；原图直接在 {link('真实照片目录',OUT/'真实照片')}。前四帧固定旧深度，后四帧是新增评分帧。
- {link('完整12帧点与三均值结果图',OUT/'结果图/s34_depth_scores.png')}，以及 {link('完整12行CSV',OUT/'证据/results/S34_depth_scoring/per_frame.csv')}。
- {link('三种条件的实际深度渲染',OUT/'渲染深度图/s34_renderer_depths.png')}：浅灰是未覆盖，色标共用 0–7.787 米。这些不是生成照片，也不是 GT 可见性准确率。
- {link('完整报告与边界',OUT/'证据/docs/S34_RESULTS.md')}；同目录 `.source.txt` 保存原报告完整原始字节，可读版只改本地链接目标。
- {link('深度/参数/优化日志独立复核',OUT/'证据/work/S34_independent_numeric_review/receipt.json')} 与 {link('地图保存量和来源票权独立复核',OUT/'证据/work/S34_consumer_numeric_review/executed/receipt.json')}；{link('完整800步日志索引',OUT/'完整优化日志清单.json')}。
- {link('真实原consumer地图与渲染数组',OUT/'证据/results/S34_original_consumer')}；{link('大数组和原依赖链接',OUT/'大数组与原依赖链接.md')}；{link('每个载荷的SHA清单',OUT/'manifest.json')}。

三条件旧地图的已有几何保持不变，地图新增点、渲染与来源权重存在差异；但虚拟渲染焦距也随原focal历史变化，不能把渲染差异唯一归因于地图质量。三组预 NMS 候选源均为 **0–7 全八帧**，没有筛选结果变好的证据。**最终 context IDs 未运行**，因为原 NMS/latent 历史缺失，不能假定阈值补出最终检索，也没有生成视频。

本轮复用旧真实网络头，0次新网络调用；新执行两次8帧MST、14次PnP、800次Adam/反向传播、四次原clean，消费者建一次旧图、深拷贝三次、真实渲染三次。生产外控实际为 UTC 2026-09-06 21:38:49–21:40:48（北京时间09-07 05:38:49–05:40:48），119.658477秒；消费者外控13.479520秒。主评分于21:44:44–45 UTC完成，消费者保存量复核21:44:44–45，深度/raw独立复核21:47:54–58完成。这些是不同时段/口径，不能加总称纯模型推理时间。

深度/raw复核另式核12行/3均值、228项初末raw、57项跨臂共同初态及各800条优化/梯度/尺度保存记录；AbsRel/RMSE算术最大差约1.39×10⁻¹⁷/5.55×10⁻¹⁷。保存梯度只核记录，未重新反传；地图复核不是第二套renderer的独立重实现。当前使用已见短序列和给定GT相机，不能外推未知场景、长期记忆、检索质量或生成视频收益。

本包仅做图和交付副本，没有新模型/优化/评分/传感器GT读取。照片逐字复制；渲染使用已保存栅格。执行前计划中“尚未运行”保留其原时点含义，最新状态以实际回执为准；本快照不自动覆盖未来研究更新。
''')
    links=[]
    for p in sorted(OUT.rglob('*.md')):
        for mt in a.LINK.finditer(p.read_text()):
            raw=mt.group(2);raw=raw[1:-1] if raw.startswith('<') else raw
            if raw.startswith(('http://','https://','mailto:','#')):continue
            q=Path(a.unquote(raw.partition('#')[0]));q=q if q.is_absolute() else (p.parent/q).resolve()
            assert q.exists() or q==OUT/'manifest.json',f'Missing active local link: {p}: {q}'
            links.append(dict(markdown=str(p.relative_to(OUT)),target=str(q)))
    sj('本地链接核验.json',dict(status='PASS_MANIFEST_WRITTEN_LAST',checked_utc=a.utc(),count=len(links),targets=links,rewritten_link_targets=a.rewrites))
    for p,h in a.sources.items():assert sha(p)==h,'Source changed during copy: '+p
    for row in a.payloads:assert sha(OUT/row['relative_path'])==row['destination_sha256'],'Copy SHA mismatch'
    manifest=dict(schema='s34-final-user-snapshot-v1',status='PASS_DELIVERY',started_utc=started,completed_utc=a.utc(),snapshot=str(OUT),
        report_source_sha256=report_sha,critical_source_sha256={str(p):h for p,h in SOURCE_IDS.items()},
        payload_count=len(a.payloads),payload_bytes=sum(r['bytes'] for r in a.payloads),payloads=a.payloads,
        original_photos=8,old_fixed_photos=4,new_scored_photos=4,score_rows=12,score_groups=3,
        saved_consumer_maps=4,saved_consumer_renders=3,optimization_records=800,gradient_records=800,scale_records=800,
        large_link_count=len(big),all_payloads_sha_verified=True,local_link_count=len(links),
        role_scope='Snapshot/figure author also authored consumer and independent geometry reviewer. Consumer independent saved review authored separately; no claimed self-independent consumer audit.',
        delivery_only=dict(new_model=0,new_GA=0,new_score=0,new_renderer=0,sensor_GT_reads=0,RGB_pixel_decodes=0,byte_copy_only=True),
        limitations=['Given GT cameras, already seen eight-frame short sequence','Ordinary controls, no innovation/fullproject/video success','All3 candidate IDs0–7 identical; final contexts NOT RUN','Large archives inherit frozen SHA and stat-only link checks, not freshly rehashed','Native source Markdown preserved; readable copies change only links','This snapshot/time only, no future automatic refresh','Manifest excludes itself; external snapshot_receipt records its SHA'])
    a.put_json(OUT/'manifest.json',manifest)
    assert all(Path(x['target']).exists() for x in links)
    rec=dict(status='PASS_COMPLETE_S34_USER_SNAPSHOT',started_utc=started,completed_utc=a.utc(),snapshot=str(OUT),
        manifest_sha256=sha(OUT/'manifest.json'),payload_count=len(a.payloads),total_files=sum(p.is_file() for p in OUT.rglob('*')),
        payload_bytes=manifest['payload_bytes'],total_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
        photos=8,local_links=len(links),all_local_targets_exist=True,all_payloads_SHA_verified=True,all_copied_sources_unchanged=True,
        report_sha256=report_sha,script_sha256=sha(__file__),helper_sha256=sha(HELPER),
        command=['python3',str(Path(__file__)),'--report-sha',report_sha],new_scientific_execution=0)
    a.put_json(WORK/'snapshot_receipt.json',rec);print(json.dumps(rec,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report-sha',required=True);arg=p.parse_args()
    try:main(arg.report_sha)
    except Exception:
        a.put_json(WORK/'snapshot_failure.json',dict(status='FAILED_DELIVERY_PRESERVED',utc=a.utc(),error=traceback.format_exc()));raise
