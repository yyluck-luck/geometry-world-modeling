"""S29 snapshot packaging only. No experiment or array decoding."""
from pathlib import Path
from datetime import datetime,timezone
import re,json,hashlib,sys,urllib.parse
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT=WS/'outputs/S29_初始化尺度的真实证据_2026-09-07'
HERE=Path(__file__).resolve().parent
START=datetime.now(timezone.utc).isoformat()
PAT=re.compile(r'(!?\[[^\]\n]*\])\((<[^>]+>|[^)]+)\)')
records=[];rewrites=[]
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
def write(q,x):q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def link(label,q):return f'[{label}](<{q}>)'
def normalize(text,src):
 def sub(m):
  x=m.group(2).strip();x=x[1:-1] if x.startswith('<') else x
  if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',x) or x.startswith('#'):return m.group(0)
  q=Path(urllib.parse.unquote(x));q=q if q.is_absolute() else (src.parent/q).resolve()
  assert q.exists(),str(q)
  rewrites.append(dict(source=str(src),old=x,new=str(q)))
  return f'{m.group(1)}(<{q}>)'
 return PAT.sub(sub,text)
def cp(src,name,md=False):
 src=Path(src);q=OUT/name;q.parent.mkdir(parents=True,exist_ok=True)
 b=src.read_bytes();h=hashlib.sha256(b).hexdigest();v=normalize(b.decode(),src).encode() if md else b
 q.write_bytes(v);assert q.read_bytes()==v and sha(src)==h
 records.append(dict(path=str(q.relative_to(OUT)),source=str(src),source_sha256=h,sha256=sha(q),bytes=len(v),byte_identical_to_source=b==v,verification='Exact byte copy, source SHA stable' if b==v else 'Markdown destinations only rewritten to absolute bracketed paths; source SHA stable and transformed bytes verified'))
 return q

def main():
 assert not OUT.exists(),'No overwrite'
 report=ROOT/'docs/S29_RESULTS.md';assert sha(report)=='2d1752c72db4cfba2d3802fb71e0f6a8853c0cf2d1fc470f4695802b0c853039'
 OUT.mkdir(parents=True)
 write(HERE/'attempt.json',dict(started_utc=START,script_sha256=sha(Path(__file__)),command=[sys.executable,str(Path(__file__))],target=str(OUT)))
 cp(report,'S29_RESULTS.md',True);cp(report,'证据/S29_RESULTS.original_source.txt')
 for arm in ('C2t','C2a'):
  base=ROOT/'results/S29_scale_control'/arm;r=json.loads((base/'receipt.json').read_text());assert r['status']=='PASS_INITIALIZATION_EXECUTED'
  for n in ('receipt.json','inputs_seal.json','prefix_metadata.json','initial_raw_metadata.json'):cp(base/n,'实际初始化/'+arm+'/'+n)
 val=ROOT/'results/S29_scale_control/validation';v=json.loads((val/'receipt.json').read_text());assert v['status']=='PASS_VALIDATION_EXECUTED' and v['hypothesis_passed'] is True
 for n in ('receipt.json','comparisons.json','consumed_identity_checks.json','prefix_identity_checks.json','pre_decode_seal.json'):
  if n!='receipt.json':assert sha(val/n)==v['outputs'][n]
  cp(val/n,'全部比较与验证/'+n)
 rr=ROOT/'work/S29_root_numeric_review';r=json.loads((rr/'receipt.json').read_text());assert r['status']=='PASS_REFERENCE_EXECUTED' and r['primary_hypothesis_passed'] is True
 for n in ('receipt.json','pre_decode_seal.json','attempt.json'):cp(rr/n,'不同公式复核/'+n)
 cp(ROOT/'work/S29_root_numeric_reference.py','不同公式复核/root_numeric_reference.py')
 for n in ('contract.json','run_s29.py','validate_s29.py','getter.diff','EXECUTION_NOTES.md'):
  cp(ROOT/'work/S29_scale_control_preparation'/n,'合同与代码/'+n,md=n.endswith('.md'))
 cp(ROOT/'work/S29_launch/receipt.json','执行/launch_receipt.json')
 cp(ROOT/'work/S29_independent_review/final_pre_review.json','执行/independent_pre_review.json')
 # Exact existing phase caller receipts; no attempt is launched here.
 for folder in ['C2t','C2a','validation']:
  q=ROOT/'work/S29_execution'/folder/'receipt.json'
  assert q.exists(),str(q)
  cp(q,'执行/'+folder+'_caller_receipt.json')
 for n in ('review.md','sources.json','source_comparison.json','completion_receipt.json'):
  cp(ROOT/'work/S29_upstream_baseline_comparison'/n,'上游对照/'+n,md=n.endswith('.md'))
 # Confirm copies of the same four RGB photos against the original frozen parent.
 old=WS/'outputs/S28_梯度修复负结果与下一步_2026-09-07'
 parent=ROOT/'work/S26B_preparation/run_manifest.json';ph=sha(parent);frames=json.loads(parent.read_text())['candidate']['frames'][:4]
 photo=[]
 for row in frames:
  name=f"frame_{row['index']:02d}_{Path(row['path']).name}"
  src=old/'真实照片_本轮仅前4帧'/name;assert sha(src)==row['sha256']
  q=cp(src,'真实照片_本轮4帧/'+name)
  photo.append(dict(index=row['index'],rgb_time=row['rgb_time'],original_rgb_path=row['path'],original_manifest_sha256=row['sha256'],copied_sha256=sha(q),copied_file=str(q.relative_to(OUT)),immediate_copy_source=str(src)))
 assert sha(parent)==ph
 write(OUT/'真实照片_本轮4帧/照片来源.json',dict(recorded_utc=datetime.now(timezone.utc).isoformat(),parent_manifest=str(parent),parent_manifest_sha256=ph,previous_snapshot=str(old/'manifest.json'),previous_snapshot_manifest_sha256=sha(old/'manifest.json'),frames=photo,scope='Four original real RGB images, unchanged copies matched to original frozen records; no sensor depth/image decode/model generation'))
 big=[]
 for arm in ('C2t','C2a'):
  base=ROOT/'results/S29_scale_control'/arm;r=json.loads((base/'receipt.json').read_text())
  for n in ('initial_raw.npz','initial_decoded.npz','prefix_raw.npz','alignment.npz'):
   q=base/n;assert q.is_file()
   big.append(dict(arm=arm,path=str(q),bytes=q.stat().st_size,expected_sha256=r['outputs'][n],sha_source=str(base/'receipt.json'),copied=False,payload_read=False,verification='Only exists/stat checked here; SHA inherited from successful sealed producer'))
 write(OUT/'大型数组_仅链接.json',dict(recorded_utc=datetime.now(timezone.utc).isoformat(),files=big))
 (OUT/'大型数组_仅链接.md').write_text('# 大型数组：只链接，不复制\n\n本轮打包只检查下列文件存在与大小，SHA 沿用已封存的 producer 回执；没有读取、解码或重新核算数组。\n\n'+'\n'.join('- '+link(x['arm']+'/'+Path(x['path']).name,x['path']) for x in big)+'\n')
 readme=f'''# 先读我：S29 初始化尺度的真实证据

**S29 已确认：原初始化约 0.173 倍的尺度，确实按同一比例影响了全部深度。** 在相同4帧、相同预测和旋转下，把初始化尺度设为1后，深度约为原来的5.77倍；只改公共平移则深度基本不变。全部786432个像素通过预定门限，不同公式复核也通过。

这证明的是初始化的数值行为，**还不能说改完更准**。S29实际做了两次初始化、6次PnP和两次无梯度目标求值，没有400步优化、传感器深度评分或视频生成；单位尺度的初始目标和相机中心残差反而更大，这些负面量完整保留在报告中。

建议打开：

1. {link('完整报告和数值表',OUT/'S29_RESULTS.md')}。
2. {link('本轮四张真实 RGB 照片',OUT/'真实照片_本轮4帧')}，从S28快照逐字节复制，并再次匹配原冻结输入 SHA。这些是已有实拍照片，不是生成图。
3. {link('全部比较',OUT/'全部比较与验证/comparisons.json')}、{link('16个实际消费张量的身份检查',OUT/'全部比较与验证/consumed_identity_checks.json')}、{link('验证回执',OUT/'全部比较与验证/receipt.json')}和{link('不同公式复核回执',OUT/'不同公式复核/receipt.json')}。
4. 两组真实初始化回执：{link('C2t',OUT/'实际初始化/C2t/receipt.json')}、{link('C2a',OUT/'实际初始化/C2a/receipt.json')}；{link('合同与代码',OUT/'合同与代码')}和{link('上游 DUSt3R 对照说明',OUT/'上游对照/review.md')}。

**S30在本快照交付截点仍处于准备，尚未执行。** 计划让两臂各做原400步，并对零步与终点统一进行共同深度评分；准备计划不算实际结果，也不能承诺更准。S29自身没有新图，本快照以实测数值表为主，没有把S28图当成本轮图。

快照开始时间：{START}（UTC；北京时间加8小时）。S29真实初始化及验证于UTC17:52:48–17:53:10完成，不同公式复核于17:53:40.909909–17:53:41.631262完成；完整精确时点与资源见报告。这里的状态是此交付截点，后续S30进展不会自动写入本快照。

报告的原相对证据链接已改为绝对本机路径；跨电脑搬运时需保留原项目或重映射。{link('大型数组清单',OUT/'大型数组_仅链接.md')}只提供已存NPZ的链接，未复制或解码。打包新增模型／GT读取／评分／GA／数学重算／绘图均为0；本项目创新、跨场景和完整生成链路仍未完成。
'''
 (OUT/'先读我.md').write_text(readme)
 links=[]
 for doc in OUT.rglob('*.md'):
  for m in PAT.finditer(doc.read_text()):
   x=m.group(2).strip();x=x[1:-1] if x.startswith('<') else x
   if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',x) or x.startswith('#'):continue
   q=Path(urllib.parse.unquote(x));assert q.is_absolute() and q.exists(),f'{doc}: {x}'
   links.append(dict(document=str(doc.relative_to(OUT)),target=str(q),exists=True))
 write(OUT/'本地链接核查.json',dict(status='PASS',checked_utc=datetime.now(timezone.utc).isoformat(),scope='All active local Markdown links in snapshot .md files; metadata string paths are provenance, not active links',count=len(links),links=links,rewrites=rewrites))
 for r in records:assert sha(Path(r['source']))==r['source_sha256'] and sha(OUT/r['path'])==r['sha256']
 known={r['path']:r for r in records};files=[]
 for q in sorted(OUT.rglob('*')):
  if q.is_file():
   rel=str(q.relative_to(OUT));files.append(known.get(rel,dict(path=rel,sha256=sha(q),bytes=q.stat().st_size,source='Generated snapshot navigation/provenance from existing metadata only',byte_identical_to_source=False)))
 manifest=dict(status='PASS_SNAPSHOT_COPY_AND_LINK_CHECK',started_utc=START,completed_utc=datetime.now(timezone.utc).isoformat(),root=str(OUT),source_report_sha256=sha(report),payload_file_count=len(files),total_file_count_including_manifest=len(files)+1,payload_bytes=sum(q['bytes'] for q in files),copy_count=len(records),copies_source_and_destination_sha_verified=True,active_markdown_links_checked=len(links),all_active_local_links_exist=True,script_path=str(Path(__file__)),script_sha256=sha(Path(__file__)),command=[sys.executable,str(Path(__file__))],state_cutoff='S29 actual initialization and validation complete, root independent formulas passed; S30 preparation only, no executed S30 claim',limits=['Four seen real RGB frames; no novelty/generalization/video improvement demonstrated','S29 is initialization-only mathematical behavior, not sensor-depth accuracy','NPZ contents not copied, read or rehashed; identities inherited from sealed receipts and existence checked','Absolute external evidence links depend on canonical local source files and may change after this snapshot','No new model, GT, scoring, GA, math recomputation, or plotting'],files=files)
 write(OUT/'manifest.json',manifest)
 assert len([x for x in OUT.rglob('*') if x.is_file()])==manifest['total_file_count_including_manifest']
 result=dict(status=manifest['status'],completed_utc=manifest['completed_utc'],snapshot=str(OUT),manifest_sha256=sha(OUT/'manifest.json'),file_count=manifest['total_file_count_including_manifest'],payload_bytes=manifest['payload_bytes'],active_local_links_checked=len(links))
 write(HERE/'receipt.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
