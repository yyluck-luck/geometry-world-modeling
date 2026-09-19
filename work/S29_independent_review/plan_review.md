# S29 初始化尺度控制：独立协议／源码评审

时间：2026-09-06T17:37:13.684450+00:00。范围为指定候选协议全文及其直接相关原源码；0 真实数组／GT 图片读取，0 MST／模型／GA／backward。本文件是实施前评审，不是实验通过回执，不另加审批层，也未修改作者文件或主账。沿用已读 Supervisor 第 2 章的“强基线 → 真实失败 → 最少变量对照”和科学批判性思考的因果混杂检查。

**结论：设计可进入最小实现。C2t/C2a 的尺度对照成立；冻结前须把下列三点落实到实现或明确表述。没有理由因 S28 负结果更换评分／参数。**

## 必须落实的三点

1. **pre-Sim3 快照必须拥有独立内存。** `init_from_pts3d` 先以 `img_pts3d[:] = geotrf(...)`，后以 `img_pts3d *= s_factor` 原地修改 MST 返回的点图。只保存 list／tensor 引用、`detach()` 或 NumPy 共享视图会污染 `z_pre` 与跨臂前缀证据。进入 `init_from_pts3d` 前，把每个点图、PnP 相机、focal 和 raw 参数／buffer 分别 clone/copy；后续 `z_pre` 只读这些不再变化的副本。全前缀按名字／形状／dtype／flags／内容 bytes 匹配，不比较压缩 NPZ 文件 bytes。原函数后续 pair registration 使用新的全局点图，pair 参数随条件改变是预期后果，不能误设“全部终点 raw 参数相同”门。

2. **保留原 near-zero 分支与类型，不能从最终值推断分支。** 原 `align_multiple_poses` 中 `if abs(s) < 1e-6: s = 1.0` 会把返回量变为 Python float；原估计恰为 1 与被替换为 1 不是同一证据。应只读捕获原 `roma.rigid_points_registration` 返回的 s 及分支条件、原返回 s0/R0/T0，不为记录再调用注册。C2t 返回原 s0 对象／值；构造 C2a 的 1 时以相机／R 的 dtype/device 为准，避免 `torch.ones_like(s0)` 在 float 分支崩溃。捕获只限本次相机对齐调用，不能误把后续三条 pointmap pair registration 当成 s0。原分支不改门限、不再额外 clamp。若不便捕获，分支状态必须写 UNKNOWN，不能写未触发；但本协议既已要求真实记录，优先做上述只读捕获。

3. **历史 B 的证据边界要写清。** S28 B 有 post-MST `initial_raw`／`initial_decoded`，没有此次需要的 pre-Sim3 点图快照。C2t/C2a 可以独立核前缀逐位一致；C2t/B 只能在共同输入、原源码与条件身份基础上，对 B 已存初态 depth、focal、pose、pp、权重作完整比较。不能把该比较写成“B 的 pre-Sim3 前缀已逐位核验”，也不能补造 B 的 pre-log z。协议末尾关于“前缀身份确认后”的句子建议明确为 C2t/C2a 的实际前缀与 B 的源输入身份两种不同证据。

## 因果解释与门限

- 同一变换族 `T(s)=g_mean−s R0 c_mean` 下，C2t 与 C2a 只有独立变量 s 改变；T 随 s 按同一公式联动，是该控制定义的一部分。C2a 相对历史 B 同时改变原增广点拟合截距，因此后续优化效果应以 C2t 为直接比较，不能跳过 C2t 归因。
- 在精确算术中，`P'=sRP+t`，`Q'=RQ`，`c'=sRc+t`，则 `Q'^{-1}(P'−c')=s Q^{-1}(P−c)`。这甚至不依赖 R 严格正交，只要求矩阵可逆。原源码确实同时变换点图与 predicted pose，去除旋转块内的 s 后，先用 **mapped predicted camera** 取 z，再调用 `_set_pose`；固定 given pose 不会被此 setter 改写。因此公共 R/T 理想相消，局部 z 留下 s；这不证明给定相机反投影形成的最终 world 几何全体也是同一个全局 Sim3。
- `atol=rtol=1e-5` 可作为预先冻结的 FP32 实现核验门，需使用明确的逐像素条件 `abs(actual−expected) <= atol + rtol*abs(expected)`；4 帧原始网格都保留，不用均值通过代替所有有效像素通过。它是可失败的操作门限，不是已经证明 FP32 所有输入必然满足的误差上界。失败应保存最大误差、失配数／分母与数值路由，再诊断；不执行后放宽。
- 三个代数比较应明确 expected 一侧：C2t 对 `s0*z_pre`；C2a 对 `z_pre`；C2a 对 `z_C2t/s0`。C2t/B 的存储后 depth 比较单列；不能把 `log/exp` 的舍入或 `_set_depthmap` 两层 `nan_to_num` 的替换混入 pre-log 定理。非有限／非正原始 z 全计数保存；空定义域不能“真空通过”，不作为有效尺度控制进入后续优化。
- 相机中心均值匹配用相同预定容差可保留，但需用 **mapped predicted** 中心核 `mean(mapped_centers)` 对 `mean(given_centers)`；用最终 `get_im_poses()` 会因 given pose 原本固定而变成无意义的恒等检查。每帧中心与朝向残差保留描述，不设“全部相机必须逐帧重合”的错误门。

## 最容易遗漏的执行边界

原 `compute_global_alignment` 在 `init_minimum_spanning_tree` 之后直接调用 `global_alignment_loop`。用明确 sentinel／停止分支在二者之间终止；不要以 `niter=0` 模拟零步初始化。深度 getter 修复放在原 MST 完成后、保存解码量和一次可选 no_grad objective 之前，原初始化语句不替换。分别记录 MST、PnP、objective forward、backward、Adam、clean 次数；禁止后 3 项，有额外 forward 就如实计数。固定 image pose／pp 的 raw 参数字节应不变，focal 跨臂一致即可，它本身仍按原设定声明可训练。`norm_pw_scale=False` 只让本次公共归一因子为 1，不会冻结 pair scale。

## 可以保留的局限

仅两次新的零步初始化、同一既见 common4、共享 oracle camera、无 sensor depth，足以检验“原尺度是否按代数传到局部深度”这一窄问题；不能证明恢复准确率、优化稳定性或跨场景泛化。保留原朝向估计和固定 s=1 的模型尺度假设是当前单变量设计所需。后续 400 步须另立条件且保留 C2t/C2a 两臂，普通修复／单位尺度仍不是科研新颖性。当前不需要追加更多数据、合成门限试验、文献综述或重复大依赖审计来完成这份协议前审。

## 实际审读身份

- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S29_scale_control_preparation/PLAN_CANDIDATE.md`
  SHA256 `3518f1b3a9ee6edf77637f4a0d89293e6666ea4ba4739f9adbb07c2f10f95c04`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py`
  SHA256 `b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`
  SHA256 `f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py`
  SHA256 `edd07a0d04e72c5687149f9dd90c36bfebcdac365c424e3ba9161fc73c495134`

审读范围：协议全文；`init_im_poses.py` 的 MST→init 路径、点注册／Sim3 构造、known-pose 选择与 `align_multiple_poses`；`optimizer.py` 的 pose preset、focal／pp／depth setter/getter 与反投影入口；`base_opt.py` 的 pose 编码、scale 归一与 GA 入口。未声称本轮重读整个仓库或运行实际值。
