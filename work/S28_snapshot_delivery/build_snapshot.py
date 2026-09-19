"""S28 deliverable copy only; no predictions, scoring, GA, sensor GT, plots."""
from pathlib import Path
from datetime import datetime, timezone
import re, json, hashlib, shutil, sys, urllib.parse

ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT=WS/'outputs/S28_梯度修复负结果与下一步_2026-09-07'
HERE=Path(__file__).resolve().parent
START=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def link(label,path):return f'[{label}](<{path}>)'
LINK=re.compile(r'(!?\[[^\]\n]*\])\((<[^>]+>|[^)]+)\)')
records=[]
link_rewrites=[]
def absolutize(text,source):
    def sub(m):
        raw=m.group(2).strip();target=raw[1:-1] if raw.startswith('<') else raw
        if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target) or target.startswith('#'):return m.group(0)
        path=Path(urllib.parse.unquote(target));path=path if path.is_absolute() else (source.parent/path).resolve()
        assert path.exists(),f'Missing source evidence {path}'
        link_rewrites.append({'source_document':str(source),'original':target,'absolute':str(path)})
        return f'{m.group(1)}(<{path}>)'
    return LINK.sub(sub,text)
def cp(source,relative,transform=False):
    source=Path(source);dest=OUT/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    original=source.read_bytes();source_sha=hashlib.sha256(original).hexdigest()
    content=absolutize(original.decode(),source).encode() if transform else original
    dest.write_bytes(content)
    assert sha(source)==source_sha and dest.read_bytes()==content
    records.append(dict(path=str(dest.relative_to(OUT)),bytes=len(content),sha256=sha(dest),source=str(source),source_sha256=source_sha,
       verification='Source SHA unchanged and exact bytes copied' if not transform else 'Source SHA unchanged; only Markdown link destinations rewritten to absolute bracketed local paths; exact transformed bytes verified',
       byte_identical_to_source=content==original))
    return dest

def main():
    assert not OUT.exists(),'Refuse existing snapshot'
    OUT.mkdir(parents=True)
    write(HERE/'attempt.json',dict(started_utc=START,script_sha256=sha(Path(__file__)),target=str(OUT),command=[sys.executable,str(Path(__file__))]))
    report=ROOT/'docs/S28_RESULTS.md'
    cp(report,'S28_RESULTS.md',True)
    cp(report,'证据/S28_RESULTS.original_source.txt')
    for name in ['s28_gradient_control.png','s28_gradient_control.pdf','s28_gradient_control.svg','caption.md','plot_receipt.json','visual_qa.json','figure_design_and_QA.md']:
        cp(ROOT/'work/S28_reporting'/name,'图表/'+name,transform=name.endswith('.md'))
    for name in ['metrics.json','per_frame.csv','receipt.json']:
        cp(ROOT/'results/S28_gradient_scale_control/scoring'/name,'评分/'+name)
    for name in ['receipt.json','initial_and_depth_review.json','trace_review.json','recomputed_metrics.json','launch_receipt.json','recompute.py','root_preexecution_review.json']:
        cp(ROOT/'work/S28_independent_numeric_review'/name,'独立复核/'+name)
    for arm in ['original','gradient_only']:
        for name in ['gradient_depth_trace.jsonl','receipt.json']:
            cp(ROOT/'results/S28_gradient_scale_control'/arm/name,'原始记录/'+arm+'/'+name)
    cp(ROOT/'work/S28_gradient_scale_control/contract.json','执行/contract.json')
    cp(ROOT/'work/S28_gradient_scale_control/getter.diff','执行/getter.diff')
    cp(ROOT/'work/S28_launch/receipt.json','执行/launch_receipt.json')
    cp(ROOT/'work/S28_execution/dispatch_receipt.json','执行/dispatch_receipt.json')
    cp(ROOT/'work/S28_independent_review/final_review.json','执行/independent_pre_review.json')
    parent=ROOT/'work/S26B_preparation/run_manifest.json';parent_sha=sha(parent)
    meta=json.loads(parent.read_text());frames=meta['candidate']['frames'][:4]
    assert [r['index'] for r in frames]==list(range(4))
    previous=WS/'outputs/S27_深度未更新的真实证据_2026-09-07'
    prevmanifest=previous/'manifest.json'
    photo_records=[]
    for row in frames:
        filename=f"frame_{row['index']:02d}_{Path(row['path']).name}"
        source=previous/'真实照片'/filename
        assert sha(source)==row['sha256'],'Prior snapshot photo must match original frozen RGB manifest'
        dest=cp(source,'真实照片_本轮仅前4帧/'+filename)
        photo_records.append(dict(**row,snapshot_source=str(source),copied_file=str(dest.relative_to(OUT)),copied_sha256=sha(dest),role='S28 actual common4 RGB input; not sensor depth or generated image'))
    assert sha(parent)==parent_sha
    write(OUT/'真实照片_本轮仅前4帧/照片来源.json',dict(utc=datetime.now(timezone.utc).isoformat(),parent_manifest=str(parent),parent_manifest_sha256=parent_sha,
        prior_snapshot_manifest=str(prevmanifest),prior_snapshot_manifest_sha256=sha(prevmanifest),selection='Exact frozen input prefix indices 0,1,2,3; original eight-image PIL preparation remains reported in S28 but frames4..7 are not copied as S28 evaluated frames',
        evidence_scope='RGB photo bytes copied from previous snapshot and matched to original manifest SHA; no image decoding, resize, GT-depth access or model generation',frames=photo_records))
    large=[]
    for arm in ['original','gradient_only']:
        base=ROOT/'results/S28_gradient_scale_control'/arm;r=json.loads((base/'receipt.json').read_text())
        for n in ['output.npz','initial_raw.npz','final_raw_before_clean.npz']:
            f=base/n;assert f.is_file()
            large.append(dict(arm=arm,path=str(f),bytes=f.stat().st_size,expected_sha256=r['outputs'][n],identity_source=str(base/'receipt.json'),check_scope='Existence and size stat only; SHA inherited from sealed PASS receipt; payload not opened or rehashed during packaging',copied=False))
    write(OUT/'大型数组_仅链接.json',dict(utc=datetime.now(timezone.utc).isoformat(),files=large))
    large_md='# 大型数组仅保留本机链接\n\n这些是已经保存的真实实验数组。此快照未复制、解码或重算它们；清单中的 SHA 沿用原 PASS 回执，打包只检查文件存在和大小。\n\n'+'\n'.join('- '+link(f"{r['arm']}/{Path(r['path']).name}",r['path']) for r in large)+'\n'
    (OUT/'大型数组_仅链接.md').write_text(large_md)
    nextdir=ROOT/'work/S29_scale_control_preparation';assert nextdir.is_dir()
    readme=f'''# 先读我：S28 梯度修复负结果

这轮已经完成真实组件对照，并通过不同作者的数值复核：**仅修复深度梯度后，四帧平均相对误差从 83.3382% 增加到 87.4762%，越高越差。** 优化目标同时降得更多，说明“优化器的目标更低”不能替代“真实深度更准”。

这是同一组已见真实照片与已有网络预测上的两次新 400 步优化，不是新网络推理、生成照片或视频，也不是已证明的新算法。不同作者复核已实际于 UTC 17:33:30.489380—17:33:31.869876 完成；此快照只复制其材料，没有再次评分或运行优化。

建议按顺序打开：

1. {link('完整 S28 结果报告',OUT/'S28_RESULTS.md')}。
2. {link('三联图 PNG',OUT/'图表/s28_gradient_control.png')}、{link('论文用向量 PDF',OUT/'图表/s28_gradient_control.pdf')}及{link('图注',OUT/'图表/caption.md')}。
3. {link('四张本轮真实照片',OUT/'真实照片_本轮仅前4帧')}。只复制原输入索引 0–3，来自 TUM fr2_desk 的已有真实 RGB 照片，均核对原冻结 manifest SHA；后四帧没有在本轮评分，未混入此照片文件夹。
4. {link('逐帧评分 CSV',OUT/'评分/per_frame.csv')}、{link('独立复核回执',OUT/'独立复核/receipt.json')}、{link('初态与深度复核',OUT/'独立复核/initial_and_depth_review.json')}及{link('800 步记录复核',OUT/'独立复核/trace_review.json')}。
5. 原记录：{link('原版全部 400 步',OUT/'原始记录/original/gradient_depth_trace.jsonl')}和{link('修复版全部 400 步',OUT/'原始记录/gradient_only/gradient_depth_trace.jsonl')}；大数组见{link('仅链接清单',OUT/'大型数组_仅链接.md')}。

**下一步 S29：初始化尺度控制正在实现准备，尚未运行。** 按本次交付截点，它将把平移起点变化与尺度变化分开做普通初始化对照；不能把候选方案称为已测收益。原始准备目录为{link('S29 准备材料',nextdir)}，这是会继续变化的外部目录；其未来内容不属于本快照核验范围。

快照建立开始时间：{START}（UTC，北京时间加 8 小时）。快照清单会记录完成时间、每文件来源、SHA 与转换方式。报告中的原相对证据链接已改成绝对本机路径；这方便本机点击，跨电脑移动时需保留原项目或重新映射路径。照片只复制未解码；本次新增预测／GA／评分／传感器 GT 读取／绘图均为 0。项目后续机制创新、跨场景和真实生成消费者验证仍未完成。
'''
    (OUT/'先读我.md').write_text(readme)
    # Validate all active Markdown links in every snapshot markdown, including
    # externally linked canonical evidence. Do not follow JSON metadata paths.
    links=[]
    for doc in OUT.rglob('*.md'):
        for mt in LINK.finditer(doc.read_text()):
            raw=mt.group(2).strip();target=raw[1:-1] if raw.startswith('<') else raw
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target) or target.startswith('#'):continue
            q=Path(urllib.parse.unquote(target));assert q.is_absolute(),f'Nonabsolute {doc}: {target}'
            assert q.exists(),f'Missing {doc}: {q}'
            links.append(dict(document=str(doc.relative_to(OUT)),target=str(q),exists=True,kind='directory' if q.is_dir() else 'file'))
    write(OUT/'本地链接核查.json',dict(status='PASS',checked_utc=datetime.now(timezone.utc).isoformat(),scope='All active local Markdown link destinations in snapshot markdown; source-relative evidence links rewritten to canonical absolute bracketed paths; no embedded JSON provenance arrays decoded or followed',count=len(links),links=links,rewrites=link_rewrites))
    for r in records:
        assert sha(OUT/r['path'])==r['sha256'] and sha(Path(r['source']))==r['source_sha256']
    allfiles=[]
    known={r['path']:r for r in records}
    for q in sorted(OUT.rglob('*')):
        if q.is_file():
            rel=str(q.relative_to(OUT));allfiles.append(known.get(rel,dict(path=rel,bytes=q.stat().st_size,sha256=sha(q),source='Generated snapshot navigation/provenance from already existing metadata; no scientific computation',byte_identical_to_source=False)))
    total=sum(r['bytes'] for r in allfiles)
    manifest=dict(status='PASS_SNAPSHOT_COPY_AND_LINK_CHECK',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),snapshot_root=str(OUT),payload_file_count=len(allfiles),total_file_count_including_manifest=len(allfiles)+1,payload_bytes=total,
        source_report_sha256=sha(report),copy_count=len(records),copies_source_sha_and_destination_verified=True,link_count=len(links),all_markdown_local_links_exist=True,
        script_path=str(Path(__file__)),script_sha256=sha(Path(__file__)),command=[sys.executable,str(Path(__file__))],
        scientific_scope='Completed S28 known-common4 matched engineering negative result, independently verified; S29 is implementation preparation at this delivery cutoff, not an executed result',
        limits=['Absolute local links depend on original workspace paths; not a portable self-contained experiment archive','Large NPZ arrays referenced by existence+recorded sealed SHA only, not copied or rehashed','Only four RGB photos copied; verified against original first-four manifest records, no GT image reads','New predictions, scoring, GA, GT sensor byte reads, and plotting are all zero','Snapshot identity covers this cutoff only; does not automatically certify later source updates'],files=allfiles)
    write(OUT/'manifest.json',manifest)
    actual=[q for q in OUT.rglob('*') if q.is_file()];assert len(actual)==manifest['total_file_count_including_manifest']
    result=dict(status=manifest['status'],snapshot=str(OUT),manifest_sha256=sha(OUT/'manifest.json'),file_count=len(actual),payload_bytes=total,completed_utc=manifest['completed_utc'],links_checked=len(links))
    write(HERE/'receipt.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
