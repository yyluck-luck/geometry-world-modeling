from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parents[2];O=Path(__file__).parent
s=json.loads((R/'results/S15C_bonn_scores/scores.json').read_text())
meta=json.loads((R/'results/S15C_bonn_scores/run_metadata.json').read_text())
calmeta=json.loads((R/'results/S15C_bonn_calibration/run_metadata.json').read_text())
ind=json.loads((R/'results/S15C_independent/verification.json').read_text())
assert meta['status']=='SUCCESS' and ind['status']=='PASS' and ind['checks']==612
rows={m:{r['index']:r for r in s['rows'] if r['method']==m}for m in ['model','constant']}
model=s['means'][0]['available_frame_descriptive_means'];constant=s['means'][1]['available_frame_descriptive_means'];pool=s['pixel_weighted']
table=['| 帧 index | 有效 GT 像素 / 50176 | 模型 δ1 | 常数 δ1 | δ1胜负 | 模型 MAE（米） | 常数 MAE（米） |','|---:|---:|---:|---:|---|---:|---:|']
for i in range(4,20):
 a,b=rows['model'][i],rows['constant'][i]
 if a['delta1_all_gt'] is None:vals=['NA','NA','无法评分','NA','NA']
 else:vals=[f"{100*a['delta1_all_gt']:.6f}%",f"{100*b['delta1_all_gt']:.6f}%",'胜' if a['delta1_all_gt']>b['delta1_all_gt'] else '平' if a['delta1_all_gt']==b['delta1_all_gt'] else '负',f"{a['own_mae_m']:.9f}",f"{b['own_mae_m']:.9f}"]
 table.append(f"| {i} | {a['gt_valid_count']:,} | "+' | '.join(vals)+' |')
text=f'''# S15C：真实深度评分完成，缺测让主结果保持 NA

**本轮已将真实照片的模型预测与真实传感器深度逐像素对照；预定的完整16帧等权主成绩无法计算，因为 index12 整张原始深度图没有一个有效深度。** 该帧保留为 NA，没有换帧、删帧或补造答案。其余15帧中，CUT3R的 δ1 对常数基线为11胜、4平、0负，平均绝对误差为15胜、0平、0负。这是已有模型的观测视图诊断，尚不是新算法收益。

根任务已用不同实现完成独立核验，612项检查全部通过。它重新读取20张原始 depth PNG，用整数最近邻索引、Python `statistics.median` 和 `math.fsum` 复算，GT与mask逐像素一致；检查通过说明结果可核查，不能当成612次独立实验或准确率提升。[独立回执](../results/S15C_independent/verification.json)

## 1. 用新手能理解的话说，这次做了什么

S15A此前已在本机把20张Bonn实拍送入CUT3R，实际完成一次20帧历史推理并封存输出。本轮复用那些预测，新增获取与照片配对的20张真实深度图。深度图相当于相机给出的距离测量；这里“深度”是沿相机光轴的 Z，不是斜射线到物体的欧氏距离。

前4帧的传感器深度仅用来统一单位：将所有有效像素的 `模型Z/传感器Z` 一起取中位数，得到 `s={s['calibration']['s_model_per_meter']:.15f}` 模型单位/米；后续预测统一除以这个s。常数基线在每个像素都猜 **{s['calibration']['constant_depth_m']:.3f}米**，这个数只由同4帧深度确定。第4..19帧的答案在校准和全部预测封存后才打开，之后没有按帧重拟合单位、平移或阈值。

这20张照片都已经是模型输入。因此本轮是“看过照片之后判断其深度”，没有产生未见照片的新视角，也没有训练新方法或生成视频。GT相机姿态和Bonn未知的光学外参未被使用；保持原生配准像素网格，无去畸变重采样。作者说明深度与RGB配准，官方CUT3R的Bonn深度评测路径也不需要GT轨迹；我们的224裁切、static_close_far序列和前4帧尺度校准是本地明确的诊断设置，不能冒称复现其512官方评测表格。[Bonn发布页](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/) · [CUT3R视频深度评测](https://github.com/CUT3R/CUT3R/blob/main/eval/video_depth/eval_depth.py)

## 2. 主结果与辅助结果必须分开

δ1表示在有真实答案的像素上，预测与答案的比值误差严格小于1.25的比例，越高越好；预测缺失算失败。MAE是平均绝对误差，单位米，越低越好。这里两种方法在有GT处都有有效预测，因此own和common误差相同；这不代表整张图有完整传感器答案。

| 汇总方式 | CUT3R | 常数基线 | 模型−常数 | 能否作为预定主结果 |
|---|---:|---:|---:|---|
| 完整16帧等权 δ1 | NA | NA | NA | 主结果保留NA；第12帧无答案 |
| 可用15帧等权 δ1 | {100*model['delta1_all_gt']:.12f}% | {100*constant['delta1_all_gt']:.12f}% | +{100*(model['delta1_all_gt']-constant['delta1_all_gt']):.12f}个百分点 | 仅可用帧描述 |
| 有效像素池化 δ1 | {100*pool[0]['delta1_all_gt']:.12f}% | {100*pool[1]['delta1_all_gt']:.12f}% | +{100*(pool[0]['delta1_all_gt']-pool[1]['delta1_all_gt']):.12f}个百分点 | 仅辅助 |
| 可用15帧等权 MAE | {model['own_mae_m']:.12f} m | {constant['own_mae_m']:.12f} m | {model['own_mae_m']-constant['own_mae_m']:.12f} m | 仅可用帧描述 |
| 有效像素池化 MAE | {pool[0]['own_mae_m']:.12f} m | {pool[1]['own_mae_m']:.12f} m | {pool[0]['own_mae_m']-pool[1]['own_mae_m']:.12f} m | 仅辅助 |

完整16帧的coverage、own/common MAE、AbsRel、RMSE主平均同样为null，不止δ1。原始数字、全部分母和其他误差项都在 [scores.json](../results/S15C_bonn_scores/scores.json) 与 [逐帧CSV](../results/S15C_bonn_scores/per_frame_metrics.csv)。

**65.22%与94.14%的差别说明汇总方法会改变对结果的直观印象。** 像素池化给有效GT更多的帧更大权重；index19有44,701个有效像素，而index14只有56个，前者的权重约为后者798倍。index10、11、13、14的模型δ1都是0，却分别只有61、61、109、56个有效像素，因此对池化成绩影响很小。不能只展示94.14%而隐去这段失败与缺测。

16张评分网格共有802,816个像素位置，传感器仅330,279个位置有效，占41.140062%；这还是同一段采集中的重复像素访问，不是330,279个独立实验样本。模型在无GT的灰区画出深度，表示它给了预测，无法据此判断那些预测是对是错。

## 3. 全部预定帧，含失败和无法评分帧

{chr(10).join(table)}

δ1的4个平局帧都是双方为0。模型在这些少量有效像素上的MAE仍小于常数，因此δ1和MAE的胜负不同；保留两者，不能挑更好看的定义来改结论。index12的原生640×480 PNG也有0个正深度，独立复算已确认，问题不是裁切刚好删光答案。index10/11的原图分别仅261/269个正深度，裁切后各61；这是实际缺测记录，不是删除困难像素后的统计。

## 4. 实拍和科学图

### 图1：固定四帧的空间对照

![固定实拍、GT、模型深度与绝对误差](../work/S15C_reporting/s15c_fixed_four_depth.png)

**固定的近距离图像显示，模型仍能给出完整深度图，而传感器答案在部分帧很稀疏。** 四帧按index4/9/14/19预定选择，不按分数排名；左列是真实RGB，仅用模型固定LANCZOS resize/crop显示，原图不修改。传感器与预测同用0–5米色域，绝对误差0–1米，超范围由色条三角和专门颜色表示；灰色是无效/缺失，误差只在有效GT处计算。图为观察输入的诊断，不能从灰色区域推断几何准确。[PDF](../work/S15C_reporting/s15c_fixed_four_depth.pdf) · [SVG](../work/S15C_reporting/s15c_fixed_four_depth.svg)

### 图2：16帧成绩和每帧答案覆盖

![全部16帧δ1及传感器答案覆盖](../work/S15C_reporting/s15c_all_sixteen_metrics.png)

**低δ1与严重稀疏的GT出现在同一段时间；第12帧保留明确的NA断点。** 上图按固定顺序显示两方法δ1，以颜色、线型和标记共同区分；下图是每帧传感器有效比例，柱上标完整像素数。全范围纵轴、零起点与缺测帧都保留，未插值越过空帧，没有把少量像素或相邻帧当独立样本画误导性误差条。[PDF](../work/S15C_reporting/s15c_all_sixteen_metrics.pdf) · [SVG](../work/S15C_reporting/s15c_all_sixteen_metrics.svg)

本轮使用Matplotlib和figure-designer的实验图范式、双重编码、统一色域、图注自明与实际看图检查。照片和深度面板保留其真实栅格属性，图中文字/坐标同时导出PDF/SVG；不把套了矢量容器的照片谎称原生矢量数据。按7.6英寸全宽显示设计，最终字号至少9pt，不宜直接缩成单栏小图。

## 5. 时间、成本与实际问题

| 实际阶段 | UTC时间 | 完成情况 |
|---|---|---|
| S15A已有真实模型历史推理 | 2026-09-06 10:04:29.206155—10:04:46.670719 | 20张RGB；外层调用耗时20.779秒；本轮复用 |
| 本轮20张depth获取 | 2026-09-06 10:26:22.205542—10:26:40.997314 | 41次请求尝试，40个206成功、1次TLS失败；1,714,929响应字节，20成员核验通过 |
| 本轮尺度校准 | {calmeta['started_utc']}—{calmeta['completed_utc']} | {calmeta['wall_seconds']:.6f}秒；4 depth，20 self-pointmap数组解码，只消费Z |
| 本轮16帧评分 | {meta['started_utc']}—{meta['completed_utc']} | {meta['wall_seconds']:.6f}秒；16 depth，2已校准预测数组解码 |
| 根独立复算 | {ind['started_utc']}—{ind['completed_utc']} | 20 depth重读、612项检查PASS；无新模型推理 |

以上UTC均加8小时为北京时间；是进程/访问时刻，不是学生工时。校准/评分进程峰值RSS分别为{calmeta['process_peak_rss_bytes']:,}与{meta['process_peak_rss_bytes']:,}字节，两者都低于8 GiB门槛。这不是与其他算法匹配条件的速度实验。没有新增模型调用、没有GPU训练，也没有重新下载约3GB的既有权重。

一次TLS连接失败按已固定有界策略恢复，失败响应与回执保留于 `data/bonn_s15c_depth/`；不是科学假设失败。真正影响本轮主结论的是完整GT缺失帧和严重稀疏帧。代码准备阶段还修正了评分seal身份范围并补齐协议要求的像素加权辅助汇总，均发生在真实校准/评分之前；原代码快照和人工失败检查保留，不把人工检查写成实测。

绘图做了3次版式生成，初稿和第二稿保留在 `work/S15C_reporting/layout_v1/`、`layout_v2/`：依次修正色条文字拥挤、图例遮线和页脚裁切。始终是同4个固定、已公开的RGB文件，累计12次**可视化**解码、6次数值评分数组解码；没有多12张模型输入或再跑模型。最终图已由制图agent实际查看，核验回执另见 `work/S15C_reporting/visual_qa.json`。

## 6. 这对创新路线有什么价值

有支持的结论是：在这一段Bonn的有效传感器像素上，已有模型经4帧尺度校准后优于弱常数基线；同时，GT稀疏性让像素平均与帧平均出现很大的差距。新增发现首先是**测量和证据可用性问题**，没有证明一个原创算法。

照片显示相机靠近纸箱时这段GT很稀疏，但目前不能把它唯一归因为量程、材料、配准误差或模型机制。也不能将模型画出的平滑平面当作无GT区域的真实答案。后续若研究“后来照片能否可靠支持旧几何的改写”，应同时记录证据覆盖、独立性、接受/拒绝和缺测条件，并在相同信息、同候选、同预算的强基线上验证。当前已看过的Bonn答案不能再作为调阈值后的未见确认集。

下一步由根任务继续S15B的照片见证与强对照实验，并决定如何独立确认这里暴露的缺测问题。新方法机制、最近工作差异、跨场景复现和完整视频质量仍待完成。CCF-A/PhD级别与老师反应是质量目标，不能由这一次基础组件测量保证。

## 7. 复核与接手入口

- 固定合同：`docs/S15C_OBSERVED_DEPTH_PROTOCOL.md`；接口：`docs/S15C_OBSERVED_DEPTH_INTERFACE.md`。
- 实际校准：`results/S15C_bonn_calibration/`；实际评分：`results/S15C_bonn_scores/`；独立复算：`results/S15C_independent/verification.json`。
- 真实数据获取：`data/bonn_s15c_depth/receipt.json`；原20RGB来源及实际推理见 `docs/S15A_RESULTS.md`。
- 本轮图源：`work/S15C_reporting/plot_s15c.py`；固定4帧/色域/所有读取记录：`figure_receipt.json`与`visual_qa.json`。
- 独立回执SHA：`{hashlib.sha256((R/'results/S15C_independent/verification.json').read_bytes()).hexdigest()}`。

本文只报告现有完成证据，不更改根主账、记忆或交接文件。科学主张以完整数据与限制为准，图像美观和612项核验均不替代创新证明。
'''
(R/'docs/S15C_RESULTS.md').write_text(text)
print(json.dumps({'report':'docs/S15C_RESULTS.md','sha256':hashlib.sha256(text.encode()).hexdigest(),'created_utc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False))
