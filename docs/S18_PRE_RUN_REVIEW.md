# S18 第三作者执行前审查

状态：**READY_FOR_ROOT_FREEZE_ONLY — 最终 producer、kernel、正式协议与 independent verifier 已完成第三作者执行前审查；可以交 root 冻结真实运行。** 精确完成时刻与全部最终身份见 `work/S18_review/ready_receipt.json`。这不是 S18 实测成功或真实独立核验 PASS。本文由 `/root/s15b_prefix_runner` 维护，只写本审查与 `work/S18_review/`。未改 producer、verifier、原源码、主账或记忆。

本轮应用 Supervisor `vibe-research-workflow` 的小步实现/源码核验与本地 Claude `sci-scientific-critical-thinking` 的条件和证据审查；没有调用 Claude 模型。这里只检查 S17C 最终 512 场景到原记忆的**新接口**，继承 S0–S11 既有证据，不把已有 first-write/首项双加/候选配额包装成新发现。

## 已完成的原数学检查

`work/S18_review/original_probe.py` 在 `.venv-cut3r` 的 NumPy 1.26.4 / Torch 2.7.0 / CPU8 下实际执行 **21 项人工检查，PASS_ARTIFICIAL_ORIGINAL_ONLY**。它从固定原作者源码 AST 提取六个完整方法及 Surfel/Octree 类，没有 import 原 pipeline 或模型、没有读真实 NPZ/RGB/GT。时间、实际值和源码 SHA 见 `original_probe_receipt.json`。

| 检查 | 实际结果与对合同的含义 |
|---|---|
| 41×61 人工线性平面，原 scale_factor=.05 双线性 | 2×3 输出为 `[[28.5,48.5,68.5],[68.5,88.5,108.5]]`，反向尺度是 20；不能用输出尺寸重新计算缩小比例 |
| 2×3 平面原 normal/radius | 右叉下方向正确；末行/列零法向仍保留；零法向半径使用分母 .2，原 Surfel 的 color=None |
| .999 depth 分位与 conf>=1 | 原 FP32 quantile=5.994999885559082；人工最大 depth 和低置信像素被排除，等于 1 的 confidence 保留，剩余候选按行优先顺序 |
| 两旧锚点的原 merge | 第一个满足原树遍历次序的 ID 获得来源，虽另一个更近；旧几何不动。此案例只检查新接口所需的顺序，不重新验证/修复 S0 已知 Octree 缺陷 |
| 两来源的原投票 | 三像素 `[0,0,1]`、cos=1、depth=1 返回权重 .6/.4（首项双加），候选各 1；不声称原算法按该权重重复抽样 |
| NumPy1.26 原 renderer 与 z-buffer | 两个完全相同 raw-depth 的人工 disk 可被第二个覆盖，见下述草案更正；不引用 S10 的 NumPy2.3 行为代替本机实测 |

另应 independent verifier 请求，以 `promotion_probe.py` 实际做 **4 项新增标量类型检查，PASS_ARTIFICIAL_ONLY**，实际 UTC 2026-09-06T11:58:34.621326–11:58:34.625856。它只计算原表达式，不读取已保存数据或执行模型。

1. `np.dot` 对 FP32 normals 返回 FP32；值 `np.float32(.6)=0.6000000238418579` 与 Python `.6` 比较为 **True**。NumPy2.3 独立代码要显式复现 1.26 的比较提升，不能直接照搬隐式规则。
2. 原 radii mean/std 归约仍为 FP32，`.5 * std` 和最终 mean+halfstd 升为 FP64。不能将全部归约提前改成 FP64，也不能最终阈值强制成 FP32。
3. 原逐像素 cos/depth 是 FP32，`1+depth` 与 `cos/(1+depth)` 为 FP64；例 `.7f/(1+.3f)=0.5384615243539304`。累计顺序与每来源第一项双加需保留。

## 对准备草案的必要更正

`S18_MEMORY_BRIDGE_PREPARATION.md` 中“同深度原顺序先占位保留”表述过强。**正确规则是：原 raw Python float 平均深度与当前已舍入 FP32 缓冲，按 NumPy1.26 原标量 `<` 比较；只有比较为 False 时才保留旧 ID。**

人工例：x=1.0000000894069672；FP32(x)=1.0000001192092896。`x < np.float32(x)` 为 True，但 `x < np.array([x],dtype=float32)` 为 False。原两片 renderer 在中心像素实际返回第二片 ID=1。这不是新的几何机制或原 bug 修复，而是当前环境必须保留的原行为。旧草案保留作为历史，本审查与正式执行协议覆盖这句话，不能在 producer 中引入额外 tie 规则。

另明确：模型/输入及 Torch 几何是 FP32，原 NumPy merge/render/vote 存在混合精度，不能将整条路径统称“全 FP32”。相机组装已与 producer 协调固定为 S17C R/t 对应的 FP32 optical c2w，原 R 的 inverse 先以 FP32 计算，再进入原 FP64 extrinsics。焦距均值保持 `(1,)` FP32 数组，`target_K * .65` 先按原数组规则 FP32 舍入；不能先 `.item()` 再乘 .65。

## 新 kernel 静态同源性

`work/S18_review/check_original_asts.py` 已实际完成 **10 项 PASS_STATIC_ONLY**，绑定文件见 `original_ast_receipt.json`：

- 新 `pointmap_to_surfels`、`estimate_normal_from_pointmap` 与固定原函数完整 AST 相同。
- 继承的 merge、render、source voting、candidate distribution 四方法与原完整 AST 相同。
- resize 的 9 条语句、store 的 3 条顶层语句（包括整个 for 循环）与原 `construct_and_store_scene` 相应片段相同。
- 继承的整个 Octree 类与 Surfel initializer 与原 AST 相同。

这里只核当前实际文件版本。最终 READY 必须重新绑定最终 SHA；若代码改动使上述身份失效，需要评估改动后的相关检查，而不是默认沿用 PASS。

## 原作者归属与最近实现的简短复查

限定固定 `runjiali-rl/vmem@39291e4f272f6b4f270691d930926ab5930f942e` 作者源码，不做大范围文献综述。本轮 .05 双线性、.999/conf 过滤、右下法向、视角半径、Octree 首匹配只加来源、disk renderer、首项双加和最多14来源配额都属于原实现；新增适配器只是将 S17C 的封存输出送到这些函数。

旧 S6 已有 224 self-Z + 固定 K 重建/stride/custom filter/cKDTree 桥接与选图检查，S7–S11已有来源机制/渲染回归。S18 的新差别只有 **原嵌入512全局优化后的 world XYZ + 配套 focal/pose/depth/clean confidence → 原 .05/normal/radius/默认 Octree**。不重新做平均位置更新、全套旧回归或提速排名，不把同两帧两个相机的可见候选当作未见查询、准确率、完整 NMS/真实 latent 消费或视频结果。

## 最终执行门已关闭

1. 已完整阅读最终 producer、kernel、root 执行协议、独立 verifier/数值 helper 与数值合同。只允许五件固定上游文件，数值解码六数组；源模块实际 `__file__` 对 manifest 角色绑定，旧 seal/PASS 对本次 metadata/final 的交叉绑定已补齐。没有递归打开旧 RGB/权重身份，非模型入口没有伪造 latent。
2. 已审 observer 的原调用顺序、完整原 store loop、pointmap/normal 调用计数、原返回时 locals 记录、default Octree 递归绑定和 break 捕获。仅以额外数组保存诊断；原返回对象控制原追加/合并。原图区域没有筛选；候选按降采样格 `(frame,row,col)` 标识，不能映成唯一原像素。空图或空候选不补点/补帧，原 NaN 失败保留。
3. 已核两幅原 512×288 宽视野查询、focal×.65/主点与 C 输出尺寸不同的解释。每次 query 的 canonical JSON 使用几何原字节和有序来源，实际 before/after SHA 由 producer 保存，独立 verifier 从最终 map 重建并核对。color 恒 None，first-writer 字段由候选到最终 ID 的完整关系另行 exact 核。实际 renderer 参数均为 NumPy，继承 kernel 的 Torch sentinel 不覆盖 Tensor-input 分支；本次不声称验证了该分支。
4. 已核 verifier 的 NumPy1.26 显式提升、连续容差与离散精确门。它先核连续值，再消费已核 producer 数组作下游离散输入；不称跨库逐位重算整个链。原 known Octree 缺陷不被最近邻替换。render_pp int64、raw 票权插入序、所有 bilinear/candidate provenance、NO_SURFELS/NO_VISIBLE_SOURCE 条件文件域、caller/metadata/counters 与真实输出清单的对接问题都在读取真实结果前关闭。
5. 最终版本和证据精确绑定见 READY receipt；下一步交 root 冻结。这一门通过仍不保证真实数组一定非退化、数值比较一定通过或科学结论成立。结果成稿审核必须等待真实运行封存与 root 放行。

## 最终版本、证据和限定

| 组件 | 最终 SHA-256 |
|---|---|
| producer `scripts/run_s18_memory_bridge.py` | `0c6b3f905cacbcc6d92905cdb88765e6cbc1adace9f6616f4d7edbdf318ddf81` |
| 新 kernel `src/s18_original_kernels.py` | `4c6feb4887fecb8d0fed37243086ff8f1087fca356ffb56b0d2dfc3b37a013e4` |
| independent verifier `scripts/verify_s18_memory_bridge.py` | `92a8269d6667bdaee23e787319a2de4e5f226407d0c19c4c5aca967eba76960a` |
| independent helper `work/S18_independent/numerical_reference.py` | `4745392876caff31bfda386363447ad39459bfe330230bfaa6ec929f79c91b8d` |
| `docs/S18_EXECUTION_PROTOCOL.md` | `dbd8fdcac8eb36ad335c5ab5dc3d8912fae334f4a5a1944dc742032b856b6156` |
| `docs/S18_NUMERICAL_VERIFICATION_CONTRACT.md` | `350a0f78b6dd40998b4124dc44e25fafeb74b6448d727e2c03ff4bddba6cac53` |

作者 v4 的 22 项人工检查绑定上述 producer/kernel；独立 helper 的原 27 项人工数学检查不重跑。独立作者另外用**此前人工输入**完成一次新增 observer/文件 schema 对接检查，63 个人工数组、4263 条判定通过；其 `real_cli_identity_gate_tested=false` 已明确，不是实测 PASS 或完整真实 CLI 演练。第三作者只读这些人工回执，未打开其 NPZ，未把检查数加总成独立科研样本。

原 producer 实际观测的是整棵树的 child-before-parent 节点表、每 query 返回邻居序列与匹配 break。独立 `visited` 是从已核结构重建的逐节点路径，**原逐节点 visited 并未直接记录，因此不声称逐项比对了原现场访问路径**。`actual_normal_visit_count` 从捕获的 break 在原邻居序列中的位置推得，不是逐 dot 调用插桩计数；所有邻居的 dot 值属于额外诊断，不能当实际执行了全部比较。数值合同已仅修改这些措辞，代码与成功人工计算均未重跑。

本审查者参与了 S18 准备草案和人工检查、提出守卫/措辞修正，未写本轮 producer 或独立数学实现。它是团队内第三作者审查，不冒称完全外部团队复现。当前 0 真实 S17C 数组/RGB/GT/权重读取，0 模型调用，0 新安装。
