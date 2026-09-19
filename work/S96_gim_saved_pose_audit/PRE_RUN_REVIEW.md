# S96：GIM-World 保存位姿核查的运行前审查

- 审查时间：2026-09-12（Asia/Shanghai）
- 审查角色：独立运行前审查（不是作者代码复现，也不是 GRC-Memory 方法验证）
- 审查对象：使用本地已保存的 TUM `freiburg1_xyz` ground-truth 位姿，运行 GIM-World 官方仓库固定 commit `6d9b2090569e7d450d3baedc09ff82f662ad9ea2` 的核函数/剪枝实现，禁止新增数据集网络下载。
- 运行目标：检查不同固定 16 位姿池的核矩阵谱、默认 jitter 后谱、协方差 PSD 条件、逆矩阵对角项和贪心选择；不计算视频质量、未来误差、GRC 风险，也不把结果写成 GIM-World 作者实验结果。

## 审查结论

**CONDITIONAL PASS：满足以下修正后可以运行一个有边界的保存位姿数学审计。** 它可以回答“官方实现的 pose-time kernel 在这组公开保存位姿上是否数值 PSD/可作协方差，以及 `_greedy_mi` 是否产生异常诊断量”，不能回答“GIM-World 在 MIND 上是否错误”，也不能支持 GRC-Memory 的方法性能或创新成立。

## 已核实的官方实现语义

1. 官方 `gim/utils/pruning.py` 的 `pose_time_kernel` 从 12-D pose 中读取位置和 row-major 旋转矩阵，并用 `R[:, :, 2]` 作为相机 +Z 方向；位置先除以 `POSITION_SCALE`。
2. 官方 `gim/utils/camera.py` 固定 `POSITION_SCALE = 100.0`，语义是 MIND 的厘米坐标转米。
3. `pose_time_kernel` 的 `sigma_p` 和 `sigma_r` 默认使用正距离的 median heuristic；`sigma_t` 为 `None` 或非正时不启用时间项。
4. 高层 `information_guided_pruning` 在 `sigma_t` 未显式给出且 `time_sigma_scale=1.0` 时设置 `sigma_t = (max(pool)-min(pool))/k`；因此本审计的**主条件应使用时间项**，而不是把无时间项当成默认行为。
5. 高层调用固定 `force_first=True, force_last=True`；主条件必须记录这两个锚点规则。
6. 源码的时间量 `t` 是 `indices` 的数值差，即帧/池索引差，不是 TUM 文件里的秒时间戳。使用 TUM 行号作为索引是本审计的明确适配约定，不能冒称为 GIM 的原生 MIND 时间语义。

## 固定输入和采样冻结

输入文件固定为：

`work/S93_ALT_TUM01/downloads/freiburg1_xyz-groundtruth.txt`

- 3000 条有效位姿行，字段为 `timestamp tx ty tz qx qy qz qw`。
- 位姿池固定为以下四组，每组 16 行；程序必须保存实际整数索引和对应原始 TUM 时间戳：
  - `linspace16_all`：在 `[0, 2999]` 上取四舍五入后的 16 个等距行号；
  - `first16`：`0..15`；
  - `last16`：`2984..2999`；
  - `stride60_first16`：`0, 60, ..., 900`。
- `first16` 与 `stride60_first16` 在第 0 行重合，且四组并非独立轨迹样本；报告必须明确“4 个固定池/不是 4 个独立序列”，不得把它们用于跨场景显著性或重复实验统计。
- 不从这些池之外选择样本，不按照谱结果重新挑池，不调参后回填；若要增加敏感性条件，另写冻结协议。

## 坐标、单位和方向的必要披露

### TUM 位姿转换

TUM ground truth 的 `tx,ty,tz` 是以米给出的相机光学中心位置，四元数顺序为 `qx,qy,qz,qw`。程序必须：

1. 归一化四元数；
2. 以明确库/公式把 `qx,qy,qz,qw` 转成 3×3 旋转矩阵；
3. 明确把 TUM 方向解释为 camera-to-world（相机坐标中的光轴方向经旋转进入世界坐标）；
4. 保留原始行号、秒时间戳、转换后的 12-D pose 和转换代码版本。

TUM 官方页面确认 translation 是颜色相机光学中心在固定世界坐标中的位置，并给出四元数格式；但它不是 GIM 的 MIND 数据协议，也没有替本审计证明 GIM 的 +Z 方向约定。因此报告中必须把“使用 `R[:, :, 2]` 作为 camera-to-world +Z”标作**与官方 GIM 源码一致的适配假设**，不能写成 TUM 官方已经验证了该实现语义。

### 厘米/米适配

GIM 源码的 `POSITION_SCALE=100` 假设输入位置是厘米；TUM 位置是米。运行前必须选且记录下列唯一一种路径：

- **推荐路径**：将 TUM 米坐标乘 100 作为输入 pose，交给官方函数除以 100，得到与 GIM 源码的单位路径一致的米坐标；或
- **显式适配路径**：保留米坐标并绕过 `POSITION_SCALE`，复制等价 kernel 计算，明确这是 cross-dataset audit，不是未改动官方调用。

不能把米坐标直接传入官方函数后仍声称“原生默认单位”；否则会产生单位语义错误。median heuristic 下整体缩放可能部分抵消，但这不能替代对输入协议的记录。

## 主条件和敏感性条件

主条件（必须先冻结并运行）：

- `k=4`；池大小 `n=16`；
- `sigma_p=None`, `sigma_r=None`（官方 median-positive defaults）；
- `sigma_t=None`, `time_sigma_scale=1.0`（由高层函数设置为 pool span / k）；
- `jitter=1e-4`；
- `force_first=True`, `force_last=True`；
- 时间索引为池中的原始 TUM 行号；
- 相机 +Z 使用转换后旋转矩阵第三列。

允许的、必须单独标名的敏感性条件：

- **no_temporal_factor**：显式 `sigma_t=0` 或禁用时间因子；不能称默认；
- 若比较 `k=2` 或 `k=8`，必须新建独立结果目录并说明这是审计敏感性，不是 S91 的预算实验；
- 若比较 chordal RBF 方向核，必须保留原始核和替代核的同一输入、同一池、同一 jitter 记录。

禁止把 toy 反例中的 `sigma_r=pi` 直接外推为这些 TUM 池的默认参数。默认 `sigma_r` 应保存实际 median 值；toy 反例只用于数学解释。

## 必须记录的输出

每个池、每个条件至少保存：

- 原始 commit、源码文件 SHA256、输入 GT SHA256；
- 池 ID、16 个行号、16 个原始秒时间戳；
- `sigma_p`, `sigma_r`, `sigma_t`, `jitter`, `POSITION_SCALE`, 时间索引约定；
- `min_eig(K)`, `max_eig(K)`, 负特征值个数；
- `min_eig(K+jitter I)`, 负特征值个数；
- PSD 判定阈值（例如 `min_eig >= -1e-10`，并同时保留原始浮点值）；
- `diag(inv(K))` 的最小/最大值、负对角数；
- `_greedy_mi` 选中行号及是否强制包含首尾；
- 若计算 Schur/posterior variance，保存最小值、负值计数和求解方式；
- wall-clock、Python/NumPy/SciPy 版本和机器信息。

程序应在遇到非有限值、矩阵维度错误、单位未声明、池索引未保存时失败退出，而不是继续生成部分结论。

## 评审风险与修复

| 风险 | 影响 | 修复 |
|---|---|---|
| 把 `t` 写成 TUM 秒而官方函数使用 indices | 改变时间核，破坏源码语义对照 | 主条件使用原始行号；同时记录秒时间戳但不用于默认核 |
| 直接把米坐标传入 `POSITION_SCALE=100` | 单位协议不一致 | 米→厘米后调用，或明确复制 kernel 适配 |
| 把 GIM 的 +Z 约定写成 TUM 官方保证 | 坐标方向过度宣称 | 标为 camera-to-world +Z 适配假设并保留转换证据 |
| 用 `sigma_r=pi` 反例代替实际默认参数 | 把 toy 反例冒充数据结果 | 保存各池 median `sigma_r`；toy 仅作解释 |
| 将 4 个池当成 4 条独立轨迹 | 虚假的统计独立性 | 报告为 4 个固定池；不做显著性/跨场景结论 |
| 看到负谱就称 GIM 论文结果错误 | 超出证据 | 只能称“该输入池/条件下核诊断异常” |
| 看到选择结果就称 GRC 性能提升 | 混淆近邻审计与方法实验 | 明确 S96 不含 RGB、depth、future target、GRC risk 或消费者 forward |
| 忽略 force-first/last | 与官方高层默认不一致 | 主条件固定并记录锚点规则 |

## 运行/停止判据

- **允许继续**：源代码、输入 SHA、四池、单位、四元数转换、时间索引、默认参数全部写入运行 JSON；无网络新数据；只输出数学/选择诊断。
- **立即停止**：需要下载完整 TUM 媒体；需要 RGB/depth 对齐；需要未来帧或模型 forward；需要按照结果改池或调参；或将结果解释为 GRC 方法验证。
- **科学表述**：即使全部池 `K` 为 PSD，最多说明该有限保存位姿审计没有发现谱异常；不提供一般 PSD 定理，也不能消除 S95 对平方角度核的理论警告。若出现负谱/负 Schur 方差，应作为近邻实现和评价合同风险记录，不能当作本项目新方法结果。

## 预运行签字

- 输入是否是保存文件：是
- 是否新增网络数据：否
- 是否使用未来 RGB-D/位姿答案：否（仅使用已保存历史/轨迹文本作数学核输入）
- 是否有完整消费者路径：否
- 是否是 GRC-Memory 正式实验：否
- 是否允许把结果用于创新成立声明：否
- 运行前独立审查结论：**CONDITIONAL PASS，须先执行上述单位、索引和方向披露。**

## 原文依据

- TUM RGB-D 官方文件格式页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats>
- TUM RGB-D 官方下载页：<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download>
- GIM-World 官方代码固定 commit：<https://github.com/nagara214/GIM-World/tree/6d9b2090569e7d450d3baedc09ff82f662ad9ea2>
- GIM-World `gim/utils/pruning.py`：<https://raw.githubusercontent.com/nagara214/GIM-World/6d9b2090569e7d450d3baedc09ff82f662ad9ea2/gim/utils/pruning.py>
- GIM-World `gim/utils/camera.py`：<https://raw.githubusercontent.com/nagara214/GIM-World/6d9b2090569e7d450d3baedc09ff82f662ad9ea2/gim/utils/camera.py>
