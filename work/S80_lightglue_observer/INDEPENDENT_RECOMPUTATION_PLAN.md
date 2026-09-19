# S80 保存输出的最小独立复算清单

编写者：原 `run_observer.py` 作者 `s77_science_closure`。实际开始：2026-09-10T15:45:23Z；首次落盘后实测时钟：2026-09-10T15:48:16Z。本文件是给 root 不同实现使用的源码数学说明，**不是已完成的独立验收**。没有读取原图、提取特征或执行新匹配；不改冻结源码/合同。针对源码 SHA `99b65cde2e0604b7179907e9a40e52d6d5240c7c670290ad5232a4e6f44a68cd`、合同 SHA `ba89adbcdd246e60c02d75a5e1ca29c7db202a607885ccb4f48c0d3b50a14251`。

建议 root 独立写短脚本，从下面的保存数组重算；不要导入原评分函数，否则只是在重复同一实现。哈希/索引/计数应精确相等；浮点算术用预先记录的数值容差，另外列最大绝对差与临界点，不把数值容差当新的科学精度阈值。

## 1. 先判实际执行是否完整

读取 `STARTED.json`、`EXTERNAL_RECEIPT.json`、worker `receipt.json`、`FEATURE_MANIFEST.json` 和 `ROWS.json`。检查源码/合同身份、实际时间、外部 returncode/stop_reason、实际 13 个 feature attempt、12 BF/最多 12 LG forward、24 个唯一 row_id 与合同顺序。确认没有超预算后仍称资源门通过。监督 RSS 是带 ps 开销的采样峰值，不是瞬时峰内存保证。

中断可能没有 `ROWS.json`/最终 worker receipt，应改从 `pairs/*_{BF,LG}.json` 与 events/外部终态列已完成/未完成项；不能把缺少最终文件推测成零匹配或完整运行。失败/缺失行可以有技术终态，但不是科学成功。

## 2. 特征身份与分母

对每个成功 feature NPZ 用 `allow_pickle=False` 读取：

- `keypoints`: N×2；`descriptors`: N×128；`scales`、`oris`、`keypoint_scores`: N；`image_size`: [576,576]。均为有限 FP32，N≤1500；核每个数组 C-order 原字节 SHA、dtype/shape、文件 SHA 与 manifest。
- 同一图用于 BF 和 LG 的 feature 文件身份应完全相同；源 anchor19 为同一新 N。不能要求新 N=旧 S73 的1239，也不能继承 S73/S79 的 source IDs。
- **唯一性检查针对数组行索引，不针对像素坐标。** 重复位置/描述子可能存在；不得因两个不同 feature 行落在相同 x,y 就自行删除或拒绝结果。

这一步确认封存的特征和分母身份；不独立证明原 PNG→官方 SIFT 的真实提取过程或物理关键点身份。

## 3. 匹配索引、双方唯一性与被拒绝分数

每行先读 `<row_id>_raw_matcher.npz`，再对照 `<row_id>.npz` 和 JSON。设源 N、目标 T，完整 `matches0` 长 N、`matches1` 长 T；元素为 −1 或合法对方索引。定义：

\[
I=\{i:m_0(i)\ge0\},\quad P=\{(i,m_0(i)):i\in I\},\quad M=|P|.
\]

每个 P 元素须满足 `matches1[j]==i`，并核反向所有有效项恰好为 P 的转置；源索引及目标索引各不重复。NPZ `accepted_indices` 等于上述按源索引升序的 P；LG 原 compact `matches` 也应相同。不要用 score>0 重建 P。

对所有接受 (i,j)，核 `source_xy=source_features.keypoints[i]`、`target_xy=target_features.keypoints[j]`，转 FP64 只改变表示类型，不改变 FP32 数值。完整 M 与两向有效索引数一致；未匹配源=N−M、未匹配目标=T−M，各比例分母分别为 N/T，不混淆。

LG 的 `matching_scores0/1`、compact `scores`、`prune0/1` 和 JSON `stop_layer` 应保存。只验证接受项符合官方阈值与分数映射，**被拒绝但有正分数的项应保留**。禁自适应条件下非空真实 forward 应 stop_layer=9，prune 数组为9；这些是程序配置/输出一致性，不是匹配物理正确性。

BF 的 `matching_scores0/1` 是原最近邻 L2 距离，数值越小越近；它们与 LG 分数没有共同概率含义，不可直接平均或横向比较。

## 4. BF 接受规则可以独立复算到哪一步

从保存的 `knn_ids0/1` 和 `knn_l2_distances0/1` 分别复算：每方向至少两个邻居、`d1 < .75*d2`，随后正反最近索引互指。检查双方候选合法、两个返回邻居不同、距离非负且按近到远排列，源/目标索引不能越界。只有一个邻居时不能通过 ratio。重复零距离时 0<0 为 false。

**数值语义注意：** 当前冻结实现把 OpenCV DMatch 距离保存为 FP32 后，使用 NumPy FP32 数组执行 `.75*第二距离` 与严格比较。独立 checker 如果全部提升 FP64 再乘，会在精确贴近 ratio 边界的人工例子中改变接受决定。应明确重建这一 FP32 乘法的舍入，或同时报告 FP32/FP64 边界差而不擅改原输出。LG `.1` 的比较同样发生于 FP32 tensor；不得把 FP32 `.10000000149…` 与 Python 精确近似 .1 的比较当成原阈值计算。

这可独立检查**从已保存近邻结果到接受索引**的规则。没有重新计算所有描述子两两距离，就不能独立确认返回的两项确为全体最近/次近邻；本轮清单不要求再跑 BF/LG，也不声称独立验证神经匹配器的前向结果。

## 5. 固定 F 和错标签

核 `geometry_receipt` 为合同绑定的 S72 receipt SHA，取其中 `pairs[target_id].Fraw`。对 target t，correct 使用 F_t；wrong 固定映射 20↔23、21↔22。分别与每 pair NPZ 的 `correct_F`、`wrong_F` 精确核对，不从这些图片/匹配拟合 F，也不根据结果改错标签。

这沿用已接受的 S72 相机输入；不是本次独立重建 GT/K 或物理标定。尤其不能把错标签相对较低解释成估计出生成相机。

## 6. 用标量公式独立重算所有接受点

对 P 中每个点，\(p=(x_0,y_0,1)^\top\)、\(q=(x_1,y_1,1)^\top\)。采用标量求和或 `math.fsum`，避免直接复用原 NumPy 行矩阵路径：

\[
\ell_1=Fp,\quad \ell_0=F^\top q,\quad a=|q^\top Fp|,
\qquad d_1={a\over\sqrt{\ell_{1x}^2+\ell_{1y}^2}},\quad
d_0={a\over\sqrt{\ell_{0x}^2+\ell_{0y}^2}},\quad e={d_1+d_0\over2}.
\]

原实现有效条件：a 和两向线范数有限，且两范数都严格大于 1e−12。核所有 M 项的掩码、NPZ 三列 `to_target,to_source,symmetric_mean`；invalid 应留在匹配集合和掩码中，三列为 NaN，不进入有效残差统计。不能使用平方 Sampson、单方向距离或 e²替换。

依次对 correct/wrong 计算。双方均 valid 的索引集合 V 上核 `wrong_minus_correct_px=e_wrong−e_correct`，注意这是逐点差后取分位，**不是两个分位相减**。核正/零/负计数及 joint_valid_count；非 V 项应 NaN。不要新增 all4 成功事件。

## 7. 分位、阈值与覆盖的最小复算

对 n 个已排序有效值 \(z_0\le\dots\le z_{n-1}\)，分位 p∈{.25,.5,.75,.95}，h=(n−1)p，k=floor(h)，α=h−k；取 \((1-α)z_k+αz_{\min(k+1,n-1)}\)。同样公式用于逐点 wrong−correct 的有效值；核最小/最大值。

2/5/10 px 计数是有效值中 **e≤阈值** 的项数；分别除以 valid_count 与全部源 N。M=valid+invalid；all-anchor 比例不是匹配准确率或无条件全图几何正确率。若另式算术在某个阈值边界两侧产生舍入差，应单列该点，不偷偷放宽阈值使计数一致。

覆盖使用全部接受坐标以及全部提取特征分别算：每轴 `clip(floor(coord/size*4),0,3)`，二维索引去重得到 occupied_4x4_cells；span=(最大坐标−最小坐标)/size，分别用宽/高576。不是包围盒面积比例；几何 invalid 的接受点也仍在 accepted coverage 中。核 source/target 和 all_feature 四份覆盖，不只核残差较低子集。

## 8. 空集和缺失必须区分

| 保存状态 | 应核的含义 |
|---|---|
| N/T>0、M=0、`EMPTY_MATCH_SET` | 匹配器已执行而没有接受匹配；两标签 valid/invalid 都0，分位/min/max 为 null，阈值计数0，fraction_of_valid 为 null，fraction_of_all_anchor 为0，occupied=0、span=null。不能填误差0。 |
| feature 真空 N=0、`EMPTY_FEATURE_SET` | 当官方输出能正常封存空特征时，相关 row 为 `MISSING_FEATURES`，M/几何为 null，不调用 LG。不是已运行后 M=0。 |
| `EXTRACTION_ERROR` | 官方提取异常，N 未知而非0；保存异常类型/堆栈与相关 missing 行。官方 empty 输入如果在返回前报错，也应保留这个实际错误，不能推测出未保存的0特征。 |
| `PAIR_ERROR` / 中断 / 外部失败 | 保留原始 matcher NPZ（若已写完）、已生成 row 和错误/外部终态。部分统计存在不表示该行已完整验收；没有完整汇总不能声称24行都已完成。 |

## 独立性与 Gemini 意见核读

本文件由原实现作者写，只能作为可检查的公式和 schema 说明。作者不能把自己的合成测试、同函数重算或源码解释签成“不同作者独立结果接受”。root 应以另一个实现完成保存量算术和身份复核，实际记录开始/结束、读取范围、最大误差、失败和未核部分。即使这些全通过，也没有独立重提特征/重跑 LightGlue、证明物理对应真值或完成外部复现实验。

本次完整读了 `work/S79_workflow_accuracy_audit/gemini_observer_review_01/ROOT_CRITIQUE.md`，没有读取原 Gemini 全答。其关于官方默认 RootSIFT、近似 K 的归因限制、不得由错标签/匹配数量唯一归因、本轮不加 RANSAC 的处理与冻结实现相符；未因此发现需要改当前提取器或增加计算的接口遗漏。上面的 FP32 ratio/阈值说明是独立复算时应保留的实现精度，不改当前冻结代码。
