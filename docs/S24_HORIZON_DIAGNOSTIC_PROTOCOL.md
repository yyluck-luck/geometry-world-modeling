# S24：多时间跨度轨迹误差的描述性诊断

状态：代码准备与人工数学检查，待根任务静态审查。**本轮作者不执行 prepare/run，不读取 S24 真实预测、GT 或分数。** 正式冻结时点、脚本/协议/父 manifest SHA 由新的 manifest 记录；不能用本文或人工检查代替真实运行回执。

## 范围与身份

沿用 CUT3R、TTT3R、FILT3R 三个已有方法，不提出新方法，不设失败阈值，不自动选择干预事件。不修改 S24 原预测、主表、评分器或原冻结文件。多个时间跨度用于描述局部运动误差与较长区间误差；曲线变差本身不证明记忆遗忘或生成视频变差。fr1_xyz 此前用过，仍非盲测，重叠窗口不算独立实验。

入口：scripts/s24_horizon_diagnostic.py。准备目录：work/S24_horizon_preparation；新结果目录：results/S24_horizon_diagnostic。父 manifest 唯一允许身份为 work/S24_baseline_expansion/run_manifest.json，SHA 95b2c749fddefc432472b0aae56c1602fb3110940a86fedc5047b201049924b7。

## prepare：只冻结时间配对

prepare 仅读父 manifest JSON 字节及其中的 schema、方法列表、帧数、帧索引、RGB 时间，以及本脚本和本协议的哈希。不访问父 manifest 指向的 RGB、GT、预测、模型、主评分文件。父 JSON 虽含 GT 路径/哈希等元数据，此程序不使用 GT 时间重配对，不读取 GT 文件。

读取 JSON 中 RGB 时间数值字面值为 Decimal；比较、加 1/5 秒、减首帧及 floor 均按这些十进制值进行。这样规则不依赖大 epoch 浮点时间的取整近似。新 manifest 同时保存时间/实际间隔的十进制字符串和供绘图的 float 数值；索引选择以 Decimal 为准。

全部原帧索引 i 均保留，每个方法都使用同一套三组配对：

- adjacent：j=i+1。
- 1s、5s：j 是满足 RGBtime_j ≥ RGBtime_i+lag 的最早后续索引。无插值、无最近邻替换、不设最大间隔排除；实际 dt 必须保存，所以时间缺口不会假装正好 1/5 秒。
- 没有这样的 j 时，保存 j=null、TAIL_NA_NO_ENDPOINT、误差 NA。不能用 0 代替缺失，索引 0 和真实零误差必须保留。
- 所有起点按 floor(RGBtime_i−RGBtime_0) 分到不重叠 1 秒箱。包括没有起点的空箱、没有有效终点的箱，以及末尾不完整箱。一个跨箱配对归起点所在箱，不截断。末尾恰在整数秒的单点箱也不声称覆盖完整下一秒。

保存全部配对索引、RGB 时间、实际 dt、起点箱、三方法域、脚本/协议 SHA 和父 manifest SHA 到新的 run_manifest.json。已有该 manifest 或结果目录即拒绝覆盖；冻结前后检查控制文件和父 manifest 未变。prepare 不读取任何 S24 分数，因此不能按误差删配对。

## run：先核父评分门槛，再读已对齐轨迹

run 必须显式传入 prepare 输出的子 manifest SHA。先核其哈希、当前脚本/协议身份、父 manifest 身份，并从父 RGB 时间重建配对验证新 manifest。然后按顺序：

1. 读取主 scoring/receipt.json，要求 status=PASS、父 manifest SHA 一致；主 metrics.json 字节 SHA 必须等于回执中的 metrics_sha256。
2. 主 metrics 也须 passed=true，三方法完整，帧数/相邻对数一致，且各方法的原数值比较通过。任一不符都不打开 aligned NPZ，也不创建结果目录。
3. 此后新建唯一结果目录，记录读取开始，再读 scoring/cut3r_aligned.npz、ttt3r_aligned.npz、filt3r_aligned.npz 的字节并为三者建立本诊断的新 SHA 快照；完成此快照才解码 pred 与 gt。它们来自父评分的一次全轨迹 Sim(3)，本脚本不重新对齐、不按窗口或方法分支重拟合尺度，不再打开原 GT 文本或原模型输出。
4. 严格检查 float64、N×4×4、有限值、齐次末行、旋转正交与行列式；不静默正规化、补帧或剔除。三档案 GT 必须逐值相同。由 aligned pred/gt 重建整体位置 RMSE 和相邻 RPE 标量，按父既定 atol=1e-6、rtol=1e-5 与主 metrics 的 independent_matrix 对照，确保没有明显错档案。
5. 完成输出后重新核新旧 manifest、脚本、协议、主回执/metrics 及三个输入 NPZ SHA 均未变，才写本次 PASS。失败保存本结果目录与 FAILED 回执，不覆盖、不自动调容差重跑。PASS 只指诊断计算完成。

**封存限制：**父主回执绑定 metrics 的 SHA，却没有分别绑定 aligned NPZ SHA。上面的 NPZ SHA 是本诊断在父评分通过后的新快照；标量重建只是内容一致性守卫，不能倒推“原评分时已经逐字封存”，也不能证明文件在两次运行之间从未变化。无需修改原冻结来掩盖这一点。

## 误差定义与全部统计

令 P、G 分别为父评分已对齐的 camera-to-world 预测和 GT。对每个有效配对计算：

E_ij = inverse(inverse(G_i) @ G_j) @ (inverse(P_i) @ P_j)。

平移为 E_ij 的平移向量二范数，单位米；旋转为 acos(clip((trace(R_E)−1)/2,−1,1))，转为度。clip 仅处理旋转角计算的舍入范围，不是过滤误差。SO(3) 输入守卫 atol=1e-7，非科学失效阈值。

每方法×跨度均保存全体起点（含尾部 NA）的逐 pair CSV；对全体有效 pair 及每个起点秒箱分别给出平移/旋转的数量、全量 RMSE、median、线性插值 P90、max，并记录实际 dt 的对应统计。零有效 pair 时 count=0、其余统计 null/CSV NA，不制造零误差。无误差截断、最坏帧删除、像素加权或方法特有筛选。

输出：

- all_pairs.csv：三方法全部逐起点曲线数据，包括具体终点、实际时间跨度和 NA。
- one_second_bins.csv、metrics.json：全跨度/全秒箱统计、数量、缺失及来源身份。
- translation_m_all_pairs 与 rotation_deg_all_pairs 的 PNG/PDF：三个跨度各一面板、三方法全曲线；尾部 NA 不连线、不假装观测为零。图为离线描述，正式运行后还需要实际视觉检查。
- input_seal.json、receipt.json：输入快照及所有输出 SHA、环境与真实时点。

## 数学人工检查与文献界限

self-test 只用固定人工时间和 SE(3)，不调用 prepare/run：检查精确阈值的时间端点、epoch 小数边界、空箱/尾部 NA、索引 0、零误差、已知平移与 90/180 度、非交换旋转/平移构造。主数学路径用 4×4 求逆；另一条用 R 转置与平移差推导相对误差，用 atan2(skew,trace) 取角。两路径比较的角度 atol=2e-5 度只覆盖 acos 在零附近的舍入敏感性，不能成为真实轨迹失败阈值。人工结果、检查数和源 SHA 以自身准备回执为准；不是不同作者真实数据复算。

[Sturm 等，2012，§VII-A](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf) 给出固定间隔 RPE，并以 30Hz 的 30 帧说明 1 秒误差。本文采用真实 RGB 时间的“最早达到 1 秒”规则，非逐字复现固定 30 帧；5 秒和按起点秒分箱都是本项目提前选定的描述性规则，文献没有为它们赋予失败阈值。[Zhang 与 Scaramuzza，2018，§III–IV、VI-B](https://rpg.ifi.uzh.ch/docs/IROS18_Zhang.pdf)说明不同跨度和对齐选择的解释边界；此次保留父全轨迹对齐，与主表一致，不声称恢复了未知的在线尺度。

## 根任务静态审查后的调用

使用项目既有 Python 环境，不加载模型。以下 prepare/run 仅由根任务在静态审查后执行，本轮作者不执行：

```sh
.venv-cut3r/bin/python scripts/s24_horizon_diagnostic.py self-test
.venv-cut3r/bin/python scripts/s24_horizon_diagnostic.py prepare
.venv-cut3r/bin/python scripts/s24_horizon_diagnostic.py run --manifest-sha256 <prepare返回的子manifest_SHA>
```

self-test 的已有回执拒绝覆盖，不需无理由重跑。run 要等主评分正式 PASS；如果 prepare 已完成，不再执行 prepare。自动化不会据本诊断挑出“遗忘事件”或启动 S/M 干预。

