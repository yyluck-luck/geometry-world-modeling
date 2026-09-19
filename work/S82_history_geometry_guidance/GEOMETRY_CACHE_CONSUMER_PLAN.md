# S82 四历史原始 heads 的几何缓存接入方案

记录时间：2026-09-10T18:19:45.527373+00:00；本次定向读源始于 2026-09-10 18:13:52 UTC。证据范围是本地 `surfel_inference.py` / PointCloudOptimizer / 初始化与优化循环相关函数，以及创新岗位已完成的人工 autograd 诊断。**没有读取即将产生的 heads、预处理 NPZ、GT 相机 NPZ 或新 RGB，没有运行模型、优化器、渲染或诊断复跑。** 未改原 VMem、当前 raw runner 或其冻结合同。本文是下一次计算的架构稿，不是已完成对齐或新实验的收据。

## 决策摘要

可以只从封存的四份 heads 和既有相机读取构建下一输入，无须再跑 CUT3R。保留原 helper 的三个首帧 star edges，按历史 [12,13,18,19] 对应局部节点 [0,1,2,3]。但**不能直接调用原 `prepare_output` 就声称完成固定 P/K 的深度优化**：它没有 K 预设参数，且当前 `get_depthmaps` 与注册深度参数断连。

最小改动是一个 S82 局部 consumer：复用原 PointCloudOptimizer 与原初始化/目标函数，局部覆盖 `get_depthmaps` 的取值一行；构造时 `optimize_pp=True`，马上通过现成接口赋值并冻结全部历史相机、焦距、主点；保持原 MST 初始化并读回固定量。不要更换模型、不补新匹配、不增加或对称化 edges。先做一次固定预算的 100 步优化诊断，保存原始/初始化/优化后/清理后的分离状态。

100 步是先验选定的有限计算预算，用于验证接线与产生可检查候选，不是收敛保证或“最强几何基线”。不根据本次损失/可视效果延长、换初始化或重跑；若不足，只据保存轨迹重新设计后续合同，不能据 100 步失败否定几何引导。

## 1. 只用封存缓存建立三个 edges

输入必须绑定 raw 阶段不同作者验收的 SHA；当前还没有在本稿中读取或接受这些未来产物。

- `execution_geometry_01/head_00_history_12.npz`
- `execution_geometry_01/head_01_history_13.npz`
- `execution_geometry_01/head_02_history_18.npz`
- `execution_geometry_01/head_03_history_19.npz`
- `execution_geometry_01/PREPROCESSED_INPUTS.npz`：使用其中实际归一化图像、history_ids、K 和变换元数据。
- 必要时保留 `PREDICTED_CAMERAS.npz` 作原始预测身份对照；下述原 MST 初始化不直接使用该 decoded pose。不能假称它被喂入优化器。
- 既有 S69 `optical_cameras.npz` 中仅取 ID12、13、18、19 对应的光学 c2w。文件含其他相机条目是既有 archive 事实，应如实登记；本次计算不使用目标相机来拟合几何，更不读目标 RGB/深度。

对 j=1,2,3，原 helper 做 `view1=views[0]`、`view2=views[j]`、`pred1=head[0]`、`pred2=head[j]`。三个 edges 固定为 `(0,1),(0,2),(0,3)`。所有帧都是同次 recurrent inference 的缓存，不是又运行了三个独立图对网络。生成槽仍在使用时才重排为 [19,18,13,12]，不在这里改变推理身份。

最小 views 可由预处理缓存恢复为每张 `img [1,3,384,512]`、整数 idx、`true_shape [1,2]=[384,512]`；不需重读原 PNG，也不需 NaN ray map。BasePCOptimizer 实际读取 idx/img；原 `collate_with_cat` 可保留 true_shape。不要把保存 head 的 predicted `rgb` 当颜色输入：`scene.imgs` 应来自真实历史图像的预处理缓存。

| 拼接后的字段 | pred1（3 条边重复 head0） | pred2（heads1–3） | 优化器实际用途 |
|---|---|---|---|
| pts3d_in_self_view | float32 [3,384,512,3] | 同形状，保留 | 只取 pred1 此字段为 `pred_i` |
| pts3d_in_other_view | float32 [3,384,512,3] | 同形状，保留 | 只取 pred2 此字段为 `pred_j` |
| conf_self | float32 [3,384,512] | 同形状，保留 | 只取 pred1 此字段为 `conf_i` |
| conf | float32 [3,384,512] | 同形状，保留 | 只取 pred2 此字段为 `conf_j` |
| camera_pose | float32 [3,7] | float32 [3,7] | 本局部原目标函数不读；保留溯源 |
| rgb | float32 [3,384,512,3] | 同形状，保留 | 本局部原目标函数不读；不替代历史颜色 |
| view.idx | [0,0,0] | [1,2,3] | 必须连续局部节点，不能直接填历史 ID |
| view.img | float32 [3,3,384,512] | 同形状 | 场景颜色与尺寸身份 |

禁止把第 j 帧的 self head 擅自替换 pred2 cross head，也不把 `decoded_c2w × self` 冒充原 cross 输出。两者由不同 DPT heads 预测，原源码没有严格相等保证。

## 2. 固定 P、K，并明确仍优化什么

P 取 S69 的 optical c2w，经明确 float32 转换后按 [12,13,18,19] 传入。这里用原 optical 世界平移单位；不乘 VMem 的 `diag(1,-1,-1,1)`，不套 27.322… 的条件平移尺度。原 raw pose 是 translation+wxyz；优化器内部 quaternion 由 roma 另行编码。必须通过 `preset_pose(c2w)`，不能把 raw 的 7 维 token 直接写进 `im_poses`。

建议构造与锁定顺序：

1. 在本地派生类上构造同一个 PointCloudOptimizer，固定 `optimize_pp=True`、`dist='l1'`、`conf='log'`、`min_conf_thr=3`、`base_scale=.5`、`allow_pw_adaptors=False`、`pw_break=20`、`focal_break=20`。这些是已读原默认值，只有 optimize_pp 的初始化状态显式改变。
2. `preset_pose(P4)`；`preset_focal([420]*4)`；`preset_principal_point([[255.6,191.6]]*4)`。只支持本组 square pixels 的 fx=fy；不假称该 scalar-focal 接口可表示任意非等焦距 K。
3. 确认 `im_poses/im_focals/im_pp.requires_grad=False`，`norm_pw_scale=False`，`pw_adaptors.requires_grad=False` 且初值零。四张 `im_depthmaps` 保持注册叶、requires_grad=True。**不要调用 `preset_depth`**：它会冻结深度，与本次优化深度的目的相反；传入 raw 预测深度也不等于传感器测量。
4. 记录输入 P/K、编码后的参数、`get_im_poses()` / `get_intrinsics()` 的读回值及最大差，之后在初始化后、每次 optimizer step 后或至少末尾精确检查冻结参数字节未变化。解码表示本身是 float32，P/K 初始读回允许预注册的表示误差，不能要求与 float64 GT 位级一致。建议技术容差 P 元素 1e−5、K 元素 1e−3 px；这些仅是编码读回容差，不是科学准确性门槛，不得据执行结果调宽。冻结前/后的参数应 exact。

参数集合要如实称为“固定图像相机和 K，优化深度与每条边的相似变换”。原 `pw_poses` 仍有 3×8 个可训练标量（四元数、平移参数、scale 参数）；四图 log-depth 共 4×384×512 个标量。不是只有深度一种变量。`pw_adaptors` 是冻结的 XY/Z 微调参数，默认零对应 adaptor=1。初始化/最终都保存这些参数与梯度统计，不能以相机固定推断所有尺度已自动正确。

### 主点 preset 的精确陷阱

默认 `optimize_pp=False` 时，`_set_principal_point` 因 requires_grad=False 不赋值；随后 `_no_grad` 还会 assert requires_grad。因此正常 Python 断言开启时，默认直接 preset 预期会报错，不能把它描述成保证“静默成功”。此前输入可行性指出“可能仍留中心”是未赋值风险，不是对成功运行的断言。

最小方案是**构造时暂时 optimize_pp=True，再立即 preset 并冻结**，无需改原函数。所有 presets 的输入长度必须等于4，避免 zip 截断；读回 K 确认真的得到 [420,420,255.6,191.6] 的允许表示，而非中心 [256,192]。

## 3. 局部修复 get_depthmaps 的梯度连接

创新岗位的人工诊断已于 2026-09-10 18:11:40 UTC 执行。其已存结果说明：在所提取的本地函数链上，注册 ParameterList 的两个 log-depth 叶 grad=None，一步 Adam 不改变值；临时 ParameterStack 叶收到梯度却不在 Adam 参数列表。该结论只来自两张 1×2 人工输入，不是 S82 真实优化或对历史 S26 效果的重新判决。本稿读回其 JSON/源码报告，没有复跑。

本地 `get_depthmaps` 每次调用 `ParameterStack`，内部 `.stack().float().detach()` 再造临时 nn.Parameter，切断了注册叶。最小 S82 局部覆盖可把取值行替换为：

```python
res = torch.stack(list(self.im_depthmaps), dim=0).exp()
```

保持原 `raw=False` 的逐图 reshape/返回逻辑。固定四张同为384×512，stack后的 [4,384,512] 与原本组形状相同；不 `.detach()`、不新建 nn.Parameter、不改变注册 ParameterList、不泛化到异尺寸输入。此处仅给局部修复方向，未落实现文件、未执行。

在真实优化之前，最少用已有人工输入核该覆盖的梯度能到达注册叶且 Adam 更新叶，并核 P/K 全冻结。真实一次运行中还要记录四个注册深度叶的 grad 是否 None、finite/norm，以及初始化至最终的参数差值；None 是接线错误，零值可能是该次目标函数状态，不能统一伪记为“优化成功”。梯度接通也不是几何准确性证明。

## 4. 保留 MST，不直接换 known_poses 初始化

原 `prepare_output` 固定 `init='mst'`。其路径先用当前三个 star edges 的预测与置信度建立初始化，含基于现有 pointmap 的焦距估计/PnP，再将估计轨迹通过四个已知历史相机做相似对齐，初始化每条边变换与四个深度。随后 `_set_pose/_set_focal` 遇到已经冻结的图像 P/K 不会覆盖它们。初始化用过预测相机/焦距猜测，不能说整个计算从未估计过这些量；最终实际固定的是图像优化参数。

具体预注册：`init='mst'`、`niter_PnP=10`，并固定 Torch/NumPy/OpenCV seed，例如82；PnP现有 reprojectionError=5 与 SOLVEPNP_SQPNP 是初始化内部规则，不是新评估阈值。MST 在 PnP失败时有 identity 初值回退；下一实现至少记录这些返回状态/回退次数，不把回退默认为已估准相机。不能看到结果后换 seed、补边或重跑PnP来挑好结果。

**新增静态阻碍：不能直接切到 `init='known_poses'`。** 当前 `init_from_known_poses` 只按每条边 i端写 `best_depthmaps[i]`。三个 star edges 的 i都是0，所以随后 n=0..3 索引 best_depthmaps 时后三图缺键。即使 P/K 全部已知，也不能从函数名推断该初始化适合此图。最小路线保持原 MST，避免为此增加对称边或另写一套初始化。

## 5. 固定一次小预算及原目标函数

建议本次独立 optimizer 计算合同冻结 **100 个 Adam step、lr_base=.01、lr_min=1e−6、schedule='linear'、betas=(.9,.9)、CPU float32、Torch8线程、OpenCV1线程、seed82**。每一步 n=0..99 使用 `t=n/100`，最后一次实际学习率 .00010099，不能声称恰好走到1e−6。300步是原 standalone helper 默认、pipeline可能1000、旧S26B实际400；本稿选择100是明确的受限诊断变体，不暗称原基线完整复现。

外层预算建议 300秒 / 8GiB（不加载网络权重；仍须实际监控），独立输出 `execution_alignment_01`、一次尝试、没有按损失提前选择最佳检查点或自适应延长。若失败，保留初始化与实际完成的步骤；不回滚成漂亮结果。尚不将该提议称已冻结的执行合同。

原 `dist='l1'` 实际函数是向量欧氏范数 `(a-b).norm(dim=-1)`，不是坐标绝对值相加。令 P=384×512，X_i为从固定K/相机与当前深度反投影得到的世界点，T_e为每条边的相似变换，原目标为：

`L = sum(e,p)[log(conf_self0[p]) * ||X_0[p] - T_e self0[p]||2] / (3P)`

`  + sum(e=(0,j),p)[log(conf_crossj[p]) * ||X_j[p] - T_e crossj[p]||2] / (3P)`。

首帧被重复三次，这是原 star edge 权重，不是三个独立样本。全部像素进入上述目标，conf log 是学习置信度权重，不是概率或真值；`min_conf_thr=3` 用于其他初始化/mask逻辑，不能说优化损失只用 conf>3 的点。值必须finite且conf>0才能计算log；不靠丢掉失败像素改分母。

原循环返回的是最后一步更新前的 loss；因此应另存初始loss、100个实际step前loss及更新后的最终loss，明确定义三者。额外一次目标函数读数不是新的模型推理或多次optimizer试验。损失降低只说明更贴合本预测观测，不代表更符合真实世界。

## 6. 清理与应保存产物

原 helper 优化后调用一次 `clean_pointcloud(tol=.001,bad_conf=0)`。它按跨视图前后关系与相对confidence降低 `im_conf`，不更新深度或相机，也不是独立遮挡真值。对4图检查12个有向视图对，round到像素索引；处理顺序会影响其逐次降低置信度，保持0..3顺序。

建议明确保留原一次清理，同时分别保存清理前后全部 confidence；不得只交清理后可见点，也不在这里做 sky masking、子采样、surfels、渲染或mask调参。PointCloudOptimizer缓存的损失权重来自初始 conf，清理发生在优化后；不能把清理后变化记成新优化损失的改善。

最少输出：

- 四图原始head与预处理输入SHA绑定，节点/边/原生成槽映射；真实读取清单。
- 预设P/K输入、初次读回、初始化后、最终读回与exact冻结检查；全部近似K/光学轴说明。
- 初始化后的depth/world points/edge transforms；100步loss、lr和注册深度grad/更新统计；最终未清理depth/world points/相机/K/edge parameters。
- 最终四图 `depth [4,384,512]`、`world_points [4,384,512,3]`、`confidence_before/after [4,384,512]`、`colors [4,384,512,3]`、`P [4,4,4]`、`K [4,3,3]` 及finite/非正深度计数；全场保存，不因不可靠就悄悄删点。
- 从最终depth用另一实现的针孔反投影，再乘固定P复算world_points的算术检查；只核几何计算一致性，不叫物理GT验证。
- 实际时间、RSS、完成step数、是否发生初始化回退、局部修复源码SHA、异常完整保存。不能把作者自检当不同作者验收。

完整 helper 的 list 返回形状为每图 points [1,H,W,3]、colors [1,H,W,3]、depth [1,H,W]、conf [1,H,W]，camera_info.focal [4,1]、pp [4,2]、R [4,3,3]、t [4,3]；保存成上面 stack 形式时需显式记出这次 batch 维转换。真正的消费者输出只能在 raw 阶段验收、局部修复受检、下一合同锁定后产生。

## 本次读源身份

下列是实际读取/哈希覆盖；不声称读取整个仓库。MD/JSON的人工诊断是既有证据读回，NPZ真实数组读取数0，模型/optimizer运行数0。

- `work/S20_environment/isolated_vmem_source/extern/CUT3R/surfel_inference.py` — SHA `8a348645cd387147c35635f0a6b432d85bcf844e3839bd5a000d8147a85b17d5`
- `work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/__init__.py` — SHA `8230021ec2368b3fcb6d7441d4e2c98f562d1c5696496f162919119d5c714b6f`
- `work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py` — SHA `edd07a0d04e72c5687149f9dd90c36bfebcdac365c424e3ba9161fc73c495134`
- `work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py` — SHA `f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`
- `work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py` — SHA `b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21`
- `work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/commons.py` — SHA `0f634d97d70b8656361a0e21b5c5b4d2ea0aa6515999d6c9260744ee43d60c7a`
- `work/S82_history_geometry_guidance/OPTIMIZER_GRADIENT_DIAGNOSTIC.md` — SHA `b736254c7bb5392d5ecb763582f5616d901081b63333c67d7e7ae1072ed7ceda`
- `work/S82_history_geometry_guidance/OPTIMIZER_GRADIENT_DIAGNOSTIC.json` — SHA `e3c73dc65c8e72e3476ae80bd26d4c037a4fea2cf5b044ccff6b868d4b33faa2`
- `work/S82_history_geometry_guidance/OPTIMIZER_GRADIENT_DIAGNOSTIC.py` — SHA `fad5b93b2a543e786221b1ac1b5316dd0419571db4a3a7ce96087c7c5e2e9794`
- `work/S82_history_geometry_guidance/FOUR_HISTORY_CONTRACT.json` — SHA `cb60e53793942e9356eb1935544f490dc4a86be3be330bfdb2fe5abf285b0f46`
