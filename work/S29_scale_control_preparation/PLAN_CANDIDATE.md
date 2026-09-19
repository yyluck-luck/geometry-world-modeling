# S29：同一消费头的初始化尺度对照（候选协议，未实现／未运行）

记录：2026-09-06 17:23:31 UTC／2026-09-07 01:23:31 北京时间（工具实时时钟）。作者仅在本目录写本文件；未读取真实 NPZ／RGB／sensor GT，未执行模型、MST、GA、反传或新评分，未改历史冻结文件及主账。Root 负责主账与后续冻结。本轮应用 Supervisor handbook 2.2 的“已复现基线→失败根因→最少变量对照”，以及本地 Claude scientific-critical-thinking 的因果混杂与构念边界；沿用已读技能，不以新增技能数量替代实验。

**问题：原消费者先把局部点图缩到约 0.173 倍，这个初始化缩放是否解释最初的深度偏小？** 先用两个零优化控制检验源码预测，不把普通初始化修改包装成新方法。Root 已选定 C2t 和 C2a；本轮不实现或执行后续 400 步。

## 1. 已知依据与尚未证实的事

Root 转交 S28 实际完整 PASS：两个全新匹配初态各 400 Adam 步，17:17:35–17:18:37 UTC，0 网络；修复后 400 步注册 depth grad 均非 None 且有限，但深度继续缩小，AbsRel 83.3382%→87.4762%、RMSE 1.72577→1.80345 m，postfinal objective 0.01593796→0.00510682。这里只引用 root 实测摘要，**本作者未重新读取／计算这些数组**。S28 独立结果复核与文档闭环由 root 完成；S29 正式合同应绑定正式回执，不用此摘要代替封存证据。原 S28 成功阶段不重跑。

源码与已读分析支持：同步相似变换点图和 MST/PnP 相机，再用后者的逆变换取 z，公共 R/T 理想相消，s 保留。它还没有证明“把 s 设 1 必然准确”，更没有证明只改初始化后 400 步仍能保持正确尺度。约 130° 是 mapped predicted 与 given 朝向差，不能直接说它导致深度缩小。

固定来源：VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`，实际执行的内嵌副本为 `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/`。以下相对行号均指该副本：

| 原源／已有材料 | 本轮使用范围 |
|---|---|
| `cloud_opt/dust3r_opt/init_im_poses.py:78–93` | 原 MST/PnP 先返回局部点图、focal、预测相机，再进入 `init_from_pts3d`。这里的预测相机不是原网络七维 camera head。 |
| 同文件 `:103–139` | 已知相机 Sim(3) 对齐→同步变换点图／预测相机→原 pair registration→归一因子→用 mapped predicted camera 取 z／设置初始深度。 |
| 同文件 `:367–382` | 原 `align_multiple_poses` 对 center 与 epsilon-z 增广点拟合自由 s/R/T；T0 不是只对真实 center 均值拟合。 |
| `base_opt.py:266–285`，`optimizer.py:102–121` | 给定 image pose 使 `norm_pw_scale=False`，公共归一因子为 1；仍不等于每个 pair scale 被固定。 |
| `optimizer.py:227–249` | 原 `_set_depthmap` 做 log/nan_to_num 存储；S28 唯一 getter 修复保留原叶子梯度，S29 保持它。 |
| `work/S28_initialization_prior_analysis/analysis.md` | R/T 相消推导、C2a 同消费头与直接 raw-self 额外头的区别、普通尺度约束近邻。 |

本轮源字节身份：`init_im_poses.py`=`b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21`；`base_opt.py`=`edd07a0d04e72c5687149f9dd90c36bfebcdac365c424e3ba9161fc73c495134`；`optimizer.py`=`f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`。分析文件 SHA=`3d0ac0dabd33fe69eece9b06c62e6f9fa33ef00bda4e72667258c9275b16906d`。S28 冻结合同 SHA=`7a80b96b0c75a97987b527ee214263bf1308e78f7f97cfb382bfc76355b7fbd4`；执行脚本 SHA=`d8553d5086bba1b922835fb55a225efe3d04175c63e64eeee7f98644c9d771d8`。正式实现后需另冻完整身份，不能只凭本表运行。

## 2. 两个新条件，共享输入与明确的一个尺度因子

同 S28：原 S21 original4 已保存六头、原 8 张 PIL 准备顺序但只前 4 图入原 star(anchor0→1,2,3)；只使用原 GA 消费的 anchor self／其余 other pointmap 与对应 conf。不给额外 self 头、网络 pose 头、新照片、传感器深度或任何由评分答案得到的比例。共同相机仍是已封存的 TUM optical c2w oracle 输入，`depths=None`，所有 image pose／pp 固定；focal、pairwise 参数和注册深度保持 S28 B 的原可训练设置。CPU8／FP32／seed0、原 MST/PnP 和给定相机转换全部保持。

在**原** `align_multiple_poses(src_poses,target_poses)` 入口保留输入，先调用原函数得到 `(s0,R0,T0)`。令 `c̄=mean(src_poses[:,:3,3])`、`ḡ=mean(target_poses[:,:3,3])`。四个中心等权；不使用 sensor depth，均值在原 dtype/device 求取。

| 条件 | 返回给原 `init_from_pts3d` 的值 | 与哪一项比较 |
|---|---|---|
| 已存 B 初态，历史参考 | 原 `s0,R0,T0`。使用 S28 `gradient_only/initial_raw.npz` 和 `initial_decoded.npz`，不重新跑 B。 | 仅用来检查平移控制是否保持局部深度，并显示与已执行优化的关系。 |
| **C2t：中心均值平移控制** | `s=s0`，`R=R0`，`T=ḡ−s0·R0·c̄`。 | C2t 对 B 只改变全局平移截距；理想初始化局部 z 不变。 |
| **C2a：单位初始化尺度控制** | `s=1`（原 dtype/device），`R=R0`，`T=ḡ−R0·c̄`。 | C2a 对 C2t 只改变中心均值对齐这一变换族内的 s；T 随 s 按同一固定公式变化。 |

这里是**均值对齐**，不是每一帧中心都精确匹配。原 T0 来自增广点拟合，因此 C2a 相对历史 B 还改了平移条件；未来若要归因优化后收益，必须以 C2t 为匹配尺度控制，不能跳过它直接把 C2a/B 全差异称为尺度因果效应。R0 保留原返回值，不改成已知朝向平均，不换旋转、不移除原 epsilon-z 构造、不把给定相机逆乘点图直接取 z。

单位 s=1 的含义是保留原消费点图的名义尺度，是一个普通模型尺度假设；不是已知真实尺度。它可能保留有偏的预测，形状、focal、射线／相机不一致也不会因 s=1 自动消失。

## 3. 第一阶段严格止于初始化：两个控制各 0 Adam

建议两个独立新进程，各执行一次完整原 MST/PnP，唯一变化为上述 `align_multiple_poses` 的返回条件。两次是两个此前没有执行的新初始化控制，不是重新执行 B 的成功优化。避免现在新增复杂的对象克隆／优化器恢复实现；保存共同中间输入的逐字比较即可确认两次重复的原前缀没有差异。预算：**2 原 MST／每臂原 PnP 调用数如实记录、0 模型、0 backward、0 Adam、0 clean、0 sensor-depth 读取**。

边界以原 `init_minimum_spanning_tree` 返回后、`global_alignment_loop` 进入前的 sentinel 为合法终点。像 S27M 一样守住 `Adam.step` 和 clean 禁止门，但这次不加反传。S28 已证明的 getter 修复继续采用；在原 MST 完成后启用，保持原初始化数学路径，记录 active 状态。可在每臂 stop 前一次 `no_grad` 原 objective 求值用于描述，必须计作额外 objective forward；它不是优化一步，也不能把跨条件 loss 高低当深度准确率。

每臂建议 CPU8、60 秒、4 GiB RSS；顺序执行，输出总预留 1 GiB。预算只是待冻建议，不是已测耗时。若正式实现需要超出此最小边界，先改候选合同说明理由，再冻结，不能执行中追加 400 步。

### 首先确认真正共享的前缀与原路径

1. C2t／C2a 保存原 `minimum_spanning_tree` 返回、进入相似对齐**之前**的每图 pts3d、PnP c2w、focal、相关 scene 原始参数／buffer、输入头与相机身份。两条件前缀的完整名字／shape／dtype／flags／raw tensor bytes 应相同；跨进程不比较 Python id 或压缩文件 SHA 作为数值相等证据。原函数返回的 s0/R0/T0 也逐字相同。若不相同，两个控制不构成匹配比较，停在初始化，不评分后再调参数。
2. 保留 s0/R0/T0 和实际替换后的 s/R/T、输入/输出相机中心均值、mapped predicted 相机与 given 的完整中心／朝向残差。s0 要有限且严格为正；原源码自带的 near-zero→1 分支保留并单独记录是否触发，不另外截断或按 GT 选择范围。
3. 原后续 pair registration、`_set_pose` 编码、`_set_depthmap` 和 focal 初始化继续逐 statement 执行。记录原公共归一因子确为 1、给定 image pose／pp 原参数冻结并不变；不要误要求 pair transform 的数值不变，它必须随新的全局初始几何相应改变。
4. 在原 `_set_depthmap` 写入前保存每帧原始轴向 z，以及写入后的 registered log-depth／getter depth、world、focal、pp、c2w、pair scales／poses和全部 raw 参数／buffer。这样可以发现原 `log().nan_to_num()` 对非正深度的替换，不能只见最终正 depth 就称原 z 全部有效。

### 可证伪预测与预先固定的核验

令同一 pre-Sim3 点图 P 与 MST/PnP 相机 `(Q_i,c_i)` 给出 `z_pre=[Q_i^{-1}(P−c_i)]_z`。同步变换后在 mapped predicted 相机取 z：

`z_C2t = s0·z_pre`，`z_C2a = z_pre`，故 `z_C2a = z_C2t/s0`；R/T 在精确算术下相消。

这是一项数值实现预测，**不是对 sensor 深度误差的胜负预测**。两条件前缀匹配后，在所有原始有限 z 上报告逐帧最大／均值绝对差、全部像素分母、非有限／非正数量；不按置信度筛点或拟合比例。正式门建议沿已有 FP32 几何核验 `atol=1e-5, rtol=1e-5`，必须预冻。getter 经过 log/exp 的比例另列，不与 pre-log 原式混为逐位等式。

- C2t 的初始化 depth 应与 B 已存初态相同至预定数值容差；仅前缀数据身份与不变的 focal／pose／pp／权重确认后，才把它作为平移无影响的实际检验。B 没保存的 pre-log z 不补造历史值。
- C2a 对 C2t 的 z 应按上述比例变化；s0 使用本次原函数返回值，不硬编码历史 0.173 或拿 GT 比例反算。全部条件的 focal 和 given pose／pp 应不变；不同的 pairwise 变换与世界点是预期后果，完整保存。
- 若任一条件出现原始非有限／非正 z，保留全部计数和存储前后结果；原比例原式只在定义域报告，且该条件不进入后续“有效尺度控制”优化。不能用 `nan_to_num` 后的正值掩盖这一失败。
- 同时原样保存无 GT 的 depth 分布、初始 objective、世界点与边界 residual 描述。中心均值匹配在原 FP32 下按预冻容差核；单帧中心误差允许变化并完整报告。

## 4. 何时停止，什么结果值得下一阶段

1. 原输入／前缀／R0 不匹配，冻结参数改变，原源／依赖身份变化，或触发任何 Adam/clean：执行控制失败，保存 FAILED；不进行后续优化或 sensor 评分。
2. 在正确定义域内，C2t/B 深度不等或 C2a/C2t 比例不符：先核真实路由、归一因子、原始 z、数值精度和 storage 变换；它可推翻“本实现只有所述公共缩放作用”的假设。不能直接把差异当作新物理机制。
3. 比例预测得到支持：只证明原公共 s 确实传到初始化局部深度，普通 s=1 控制按设计保留 pre-Sim3 z。**不据此宣布深度准确率恢复**；本阶段不读 sensor depth。
4. Root 根据两个初始化是否有效、前缀是否匹配、S28 已有下降轨迹，以及“只换起点能否抵抗原目标的后续缩小”这一剩余问题，决定是否另冻后续实验。不能因为初始 objective 更低或深度看起来接近以往 GT 就自动选择控制／增加步数。

若后续有必要执行 400 步，应另立合同：C2t 和 C2a 都沿 S28 B getter、原 objective／权重／Adam／linear/.01／400 步，无其他修正。初态差异应严格属于上述尺度族诱导的 depth/pair geometry 变化；其余共享内容逐字核验。复用本轮已封存的完整初始化状态是否可行须实际核“参数对象与 optimizer 新建”恢复边界，不能把 decoded 参数逆编码冒充 raw 恢复。需要新进程原样再初始化时，给出理由并核封存初态，不能偷偷重复历史 B 400 步。**此后续 400 步现在没有实现、冻结或执行授权。**

未来尺度初始化控制即使改善，只是普通工程控制。若有效 getter 下 C2a 仍沿目标缩小、准确率仍坏／更坏，应保留负结果，说明“改初始尺度”不足；不能继续在这 4 帧已见答案上临时追 lr、prior 或挑更好步数。

## 5. 初始化尺度和全程固定尺度是不同实验

S29 的 s 仅是 `align_multiple_poses` 的一次公共初始化量；随后原每条 edge 的 `pw_poses` log-scale 和 depth 等参数仍按原合同可训练。原 `norm_pw_scale=False` 也只是关闭公共归一化，**不代表 scale 固定**。本轮零步没有检验任何训练期尺度保持能力。

全程固定尺度会改变优化可行集合，属于另一个工程对照：必须事先说清固定哪条 edge 的哪一个 raw scale、是否重新编码 translation、depth 如何允许改变，以及 optimizer 状态如何处理。简单把整个 `pw_poses` 冻结会连带冻结旋转和平移；它不等于“只固定 scale”。冻结 edge scale 也不自动固定所有 depth 的绝对尺度。因此现在不实现这种控制、不混用“init s=1”与“全程 metric scale 被约束”的说法。

## 6. Oracle 与创新边界

- 所有条件仍共享原 GT camera control；它是本已声明的 oracle 输入，不能描述为真实部署中的估计相机。s0 和中心均值只读取该允许输入与原消费头生成的 MST/PnP 几何。
- `s=1` 不是 GTdepth 拟合，T 只由允许的相机中心均值给出；禁止读 sensor-depth、其中位比例、最优缩放或按 sensor 误差选择 s/T。将来评分也要等所有预定输出封存，复用原有效像素、AbsRel/RMSE/delta1，不拟合尺度、不按 conf 筛选、不挑改善帧。
- 原 anchor self／其余 other 的消费集合不变；若后续切换到每帧 raw-self 深度，要明确新增了原 GA 没使用的 self 信息，不能归入这次同输入控制。
- 这个小片段是已见的 common4 组件诊断，不是盲测、长期一致性、Surfel 选图、生成视频结果或论文创新。Supervisor 强基线流程要求先理解并修复普通基线失败；只有这些简单控制之后仍有重要、跨场景且传入真实生成消费者的剩余问题，才进入新的方法机制讨论。

下一步：root 完成 S28 独立结果／文档闭环，审定本 S29 仅初始化协议后，再安排最小实现、另一作者前审与冻结。本文件不触发任何运行。
