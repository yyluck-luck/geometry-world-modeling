from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys
ROOT=Path(__file__).resolve().parents[2]
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.now(timezone.utc).isoformat()
metrics=read(ROOT/'results/S26B_consumer_baseline/scoring/metrics.json')
diag=read(ROOT/'work/S26B_commit_diagnostic/results/summary.json')
numeric=read(ROOT/'work/S26B_root_numeric_review/receipt.json')
assert numeric['status']=='PASS'
names={'cut3r':'CUT3R','ttt3r':'TTT3R','filt3r':'FILT3R'}
table='\n'.join(f'| {names[k]} | {v["absrel"]*100:.4f}% | {v["rmse_m"]:.6f} | {v["delta1"]*100:.5f}% |' for k,v in metrics['primary_new4'].items())
dt='\n'.join(f'| {names[k]} | {v["all4_world_displacement_m"]["mean"]*100:.5f} | {v["all4_world_displacement_m"]["p95_linear"]*100:.5f} | {v["all4_remaining_displacement_m"]["max"]:.3e} |' for k,v in diag['old4'].items())
runtime=[]
for mode in names:
    r=read(ROOT/f'results/S26B_consumer_baseline/{mode}/receipt.json')
    c=read(ROOT/f'work/S26B_execution_attempt2/{mode}/receipt.json')
    runtime.append(f'| {names[mode]} | {r["ga_with_observation_seconds"]:.3f} | {c["wall_seconds"]:.3f} | {c["peak_rss_bytes"]/1024**3:.3f} |')
qa=dict(status='PASS_STANDALONE_REPORT',reviewed_utc=now,reviewer='/root',images_actually_viewed=['new4_depth_scores.png','all_new4_real_photos.png'],findings=['All four new frames and all methods shown','Both score axes start at zero and retain all data','Colors plus distinct markers; legends and labels readable','Photos are all prespecified new real RGB frames, not generated or selected by performance'],scope='Current report size; not camera-ready scaled-font certification')
(HERE/'visual_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
report=f'''# S26B：真实地图优化结果与下一步诊断

报告写入UTC：{now}；北京时间=UTC+8。

**三种已有方法的真实几何优化已经完成，但本次8帧组件的深度质量很差，不能据此宣称新方法或记忆改善。** 更关键的是，共同旧地图本身已有83.3382%的相对深度误差，后续所有方法都继承这份被固定的旧深度。下一步应先定位这个共同起点的问题，再讨论三方法差异与创新。

## 本次究竟做了什么

真实TUM fr2_desk先前已见的连续8帧，首尾0.235880秒；0–3为共同旧帧，4–7为新帧。复用S21/S22实际神经预测的六个头，原VMem几何优化器执行star anchor0、400 Adam步、lr.01、CPU8。8个GT相机是显式共同oracle控制输入，不是算法预测，也不是深度答案。旧depth来自原4图GA，不是GT传感器depth。

共同旧depth、给定相机和pp保持固定，所有focal及新4depth按原程序优化。每方法完整封存后才读取8张已见传感器depth评分。原像素单位/5000、中心最近邻映射、不拟合尺度、不切远点、不按置信度筛选。只新增3次GA共1200步，0新神经前向；共同旧图400步是此前已做的历史运行。

## 全部新4主结果

AbsRel是逐像素相对深度误差的帧内均值，再对四帧等权平均；RMSE也是四个帧RMSE的均值，不是所有像素合并RMSE。δ1为预测/答案比值落在1.25倍范围内的像素比例，越高越好。

| 方法 | AbsRel，越低越好 | 逐帧RMSE均值（m） | δ1，越高越好 |
|---|---:|---:|---:|
{table}

每方法新4的有效GT像素访问共547012，缺失239420；所有786432网格位置纳入缺失统计。有效GT上的预测均为正且有限，无无效预测替代或删除。8张相邻照片和像素不是独立实验重复，没有显著性、泛化或长程结论。FILT和CUT在这里很接近，不能把小幅数字差写成已达成proposal。

![全部新4深度误差](../work/S26B_reporting/new4_depth_scores.png)

![全部新4原始实拍](../work/S26B_reporting/all_new4_real_photos.png)

图中是全部预定新帧，不按误差挑图。旧4共同AbsRel83.3382%、逐帧RMSE均值1.725768m；三方法返回的旧depth仅有预定log/exp数值往返差，旧4分数基本相同。**当前不能把失败归因于新观测破坏记忆：共同旧图在新8优化之前就已经很差。** 尺度/坐标转接、短片段条件和原目标的约束必须先排查；目前没有确定根因。

## 锁住旧深度，旧点的位置仍变化了吗

预先写好的描述诊断验证旧depth/pose在原容差内、pp完全相同，所有28帧的world point均符合自身depth/pose/pp/focal反投影。随后保留每方法旧4全部786432像素。结果如下，单位和范围不能与GT误差混淆：

| 方法 | 旧world点位移均值（cm） | 位移P95（cm） | 去除focal算术项后剩余最大范数（m） |
|---|---:|---:|---:|
{dt}

公式为`X=R[d(u−cx)/f,d(v−cy)/f,d]+t`。仅代入变化后的focal，已可解释这里绝大部分保存点位差，余量约1e-7m。**这只是保存字段的算术分解，不是冻结focal后重跑GA的因果实验，也不是几何伤害。** TTT点位变化更小却深度更差，正说明“变化小”不能自行充当正确性指标。

S26B没有实例化或提交Surfel，没有运行query/cache/选图或视频生成。另做的历史12份focal与当前8份的均值算术重放，相对差CUT1.7702%、TTT0.3969%、FILT1.6401%；它是对源码列表行为的假设两轮计算，不是实测缓存错误，当前8均值也不是已证明正确的策略。原common4与CUT8同时改变头上下文、3/7图边、初始化和联合目标，不能把差异称单变量作用。

## 失败与复用如何处理

1. 原S26共同旧4完成400步及clean后，独立NumPy clean参考在12/786432值失配而FAILED。11个半像素取整翻转与1个传播差异已逐点解释；独立dense-gather参考保留原Torch FP32矩阵运算顺序后全值字节相同，没有放宽容差或豁免边界。
2. 29项保存量复核允许IMPORT_VALIDATED导入。原FAILED保留；历史未保存的PnP细节、module inventory、原postfinal标量等明确NOT_RECORDED，新纯函数重算不冒充原记录。
3. S26B首次启动在读取数据前因未显式导入importlib.util失败，0新GA/GT。新启动合同只显式预加载标准库，用runpy执行同一冻结worker；原失败和所有科学源码保持。成功的独立外控在work/S26B_execution_attempt2，16:17:18.533534–16:19:06.814613UTC。

| 方法 | GA连同观察/校验秒数 | 外控总秒数 | 观察到的峰值GiB |
|---|---:|---:|---:|
{chr(10).join(runtime)}

每臂400次Adam、1次MST和1次clean完整；真实clean全像素与新参考完全相等，固定参数阶段检查和中间observer日志均落盘。不是优化后的速度benchmark。

不同作者的OpenCV/逐行全网格复算已实际完成28行及10组×4均值，共5505024网格像素访问、3802488有效GT访问；主指标最大差2.23e-16。它是同一已见数据的团队内不同实现复核，非外部复现。不是把所有JSON辅助字段都独立核了一遍。全旧点描述诊断另耗约24.53秒，0模型/GA/GT。

## 科研决策与技能落实

遵循Supervisor第2章的强基线→具体失败→根因→方法：本轮已找到需要解释的真实组件劣化，但先审输入契约，不能把程序转接或弱约束误当研究发现。S27正准备保存数据的尺度诊断与原程序坐标审计，先区分原头是否已错、优化后是否改变尺度、共同旧depth是否把错误固定给后续。

本地Claude科学批判技能用于区分数值变化、真实误差、因果与外推。近邻原文已排除泛化“同步旧地图/缓存/按变化优先修图”的新意：[BAD SLAM](https://openaccess.thecvf.com/content_CVPR_2019/papers/Schops_BAD_SLAM_Bundle_Adjusted_Direct_RGB-D_SLAM_CVPR_2019_paper.pdf)、[BundleFusion](https://arxiv.org/pdf/1604.01093v3)、[ElasticFusion](https://roboticsproceedings.org/rss11/p01.pdf)、[DSO](https://arxiv.org/pdf/1607.02565)。具体对象与适用范围见[原文排重](../work/S26B_commit_prior_check/review.md)，不把这四篇说成穷尽所有近邻。

完整视频生成仍未完成，新机制与跨场景确认尚缺；PhD深度/CCF A质量仍是目标，不是本报告已达到的状态。

## 复查入口

- 原S26失败：results/S26_consumer_baseline/common_old；[保存量恢复](../work/S26_clean_recovery/DIAGNOSIS_AND_IMPORT.md)。
- S26B父合同SHA `147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c`，work/S26B_preparation/run_manifest.json。
- 第二启动合同SHA `15912f6f012cad51986bb67669997da1a9fc4fae08d16eb0c3d88c9cf9a7cb46`，work/S26B_execution_attempt2_preparation/contract.json；成功回执work/S26B_execution_attempt2/receipt.json，原dispatch仍FAILED。
- 所有真实输出与评分：results/S26B_consumer_baseline；不同作者复算work/S26B_root_numeric_review。
- 旧点完整描述与逐像素NPZ：work/S26B_commit_diagnostic/results；固定协议与执行三SHA同上级目录。
'''
(ROOT/'docs/S26B_RESULTS.md').write_text(report)
package=WS/'outputs/S26B_真实地图优化与失败诊断_2026-09-07'
assert not package.exists()
for sub in ['图表','真实照片','数值与复核']:(package/sub).mkdir(parents=True,exist_ok=True)
(package/'完整结果报告.md').write_text(report.replace('../work/S26B_reporting/','图表/').replace('../work/','/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/'))
for p in HERE.iterdir():
    if p.suffix in ['.png','.pdf','.svg']:shutil.copyfile(p,package/'图表'/p.name)
for row in read(ROOT/'work/S26_consumer_baseline_preparation/candidate_inputs.json')['frames']:
    source=Path(row['path']);assert sha(source)==row['sha256'];shutil.copyfile(source,package/'真实照片'/f'frame_{row["index"]:02d}_{source.name}')
for source,name in [(ROOT/'results/S26B_consumer_baseline/scoring/metrics.json','depth_metrics.json'),(ROOT/'work/S26B_commit_diagnostic/results/summary.json','old_geometry_summary.json'),(ROOT/'work/S26B_root_numeric_review/receipt.json','numeric_review.json'),(HERE/'visual_qa.json','visual_qa.json'),(ROOT/'work/S26B_execution_attempt2/receipt.json','execution.json')]:shutil.copyfile(source,package/'数值与复核'/name)
(package/'先看这里.md').write_text('''# 地图优化已实际完成，结果暴露了一个需要先解释的问题

三种方法均完成400步真实优化。新四帧平均相对深度误差约67.8%、93.5%、67.6%；共同旧地图已有约83.3%误差。现在先查共同起点为何偏差大，不能把这组结果说成创新成功。

旧深度固定时，焦距变化确实伴随旧点位置变化；这里尚未测实际记忆提交、选图或视频。普通地图同步已有先例。

- [完整报告与全部曲线](完整结果报告.md)
- `真实照片/`保存这8张未经生成的原始照片。
- `数值与复核/`保存分数、描述统计和验证边界。

下一步是原始预测→几何优化→共同旧地图的尺度诊断。此目录为结果快照，不是完整项目验收。
''')
(package/'manifest.json').write_text(json.dumps(dict(created_utc=now,canonical_project=str(ROOT),scope='S26B real consumer result snapshot, not full proposal completion',files_sha256={str(p.relative_to(package)):sha(p) for p in package.rglob('*') if p.is_file()}),indent=2,ensure_ascii=False)+'\n')
sys.path.insert(0,str(ROOT/'scripts'));from research_log import append_event
append_event('S26B三个真实GA及独立评分复算完成，发现共同旧图质量问题', '成功外控16:17:18–16:19:06UTC；三次400GA共1200新步，0新网络。新4 AbsRel CUT67.8259/TTT93.5431/FILT67.5730%，共同旧4 83.3382%。28行/40均值不同作者数值复算通过；全旧4点位变化可由focal算术项解释，未测真实Surfel/cache伤害。真实图表已实际查看，快照含8实拍。优先定位共同旧图/尺度约束，不把局部变化包装创新。',evidence=['docs/S26B_RESULTS.md','work/S26B_execution_attempt2/receipt.json','work/S26B_root_numeric_review/receipt.json','work/S26B_commit_diagnostic/results/summary.json',str(package/'manifest.json')],next_step='S27先做尺度/坐标源审与保存数据诊断，区分输入契约错误和原消费者局限；暂不启动新GA。')
print(json.dumps({'report':str(ROOT/'docs/S26B_RESULTS.md'),'package':str(package),'written_utc':now},ensure_ascii=False))
