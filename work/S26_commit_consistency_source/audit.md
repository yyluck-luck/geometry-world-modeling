# S26：旧几何提交之后的焦距、点图与查询缓存一致性（SOURCE ONLY）

**源码支持两条可检验的潜在不一致：①旧 depth/pose 冻结，旧 focal 仍可改变，因此重新计算的旧 world pointmap 不必等于已提交几何；②查询 focal 缓存追加每轮全部历史估计，其均值包含重复的旧帧快照。尚未证明任一效应实际发生、造成错误或影响生成。** 本轮只读固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`，不读 S24/S26 数组、GT、评分，不跑模型或 GA。遵循 Supervisor 第2章先确认 baseline failure 的路径；不先包装新方法。S19 已否决的“后代覆写旧 Surfel 字段”仍保持否决。

源根目录：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`。下文文件/行号均指该固定目录，字节与 commit 的一致性见 `receipt.json`。

## 1. 持久对象与实际调用顺序

| 对象/事件 | 精确源码行为 | 对假设的约束 |
|---|---|---|
| 生成相机与 intrinsics `self.c2ws/self.Ks` | [pipeline.py:174](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:174>)–185 初始化；1245–1246取本轮 target 切片；1293–1298只追加保留的 target 相机/K/PIL，排除padding；517–522按选中frame ID取 `self.Ks`。 | 这些 K 是生成条件的完整矩阵，**不是** GA 的 `surfel_Ks`。没有用 GA focal 覆写 `self.Ks` 的路径。 |
| 全历史几何调用 | [pipeline.py:1305](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:1305>) 传全部 `self.pil_frames`；976–988 传全部翻转后的 c2w、此前完整 `surfel_depths`；不传旧 focal，也不传 `self.Ks`。 | 每次估计的输出含全部历史 N，旧深度是此前历史长度的prefix约束，不是末4帧切片。 |
| Dense depth 缓存 | [pipeline.py:990](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:990>)–996拼接全部结果，将 `surfel_depths` **替换**为本轮全部 N 深度。 | 旧深度在原优化器中不训练，但 log/exp 编码可带FP32舍入；跨调用不能要求返回值与上轮输入字节相同。 |
| Focal 查询缓存 | 同文件995对全部 `focal_lengths[0:N]` 执行 `surfel_Ks.extend`；[637](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:637>)对整个列表取均值，642用其×0.65作为查询fx/fy。 | 正常连续调用积累的是“所有重建轮次的全部 focal 快照”，并非当前每帧一份。固定repo所有Python中的 `surfel_Ks` 仅122/141初始化清空、637均值、995追加；没有正常去重、替换或按来源版本索引。 |
| 旧/新 pointmap 的提交 | 同文件998–1022重采样**全部**pointcloud/depth/conf；[1026](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:1026>)空地图从0开始，非空地图从 `N-target_num_frames` 开始转候选。1031–1038用对应本轮point/focal/depth/conf和给定相机生成 Surfel。 | 满新4帧的非空地图调用只提交末4新帧；重建并缩小后的旧pointmap不替换旧对象。若本轮实际仅新增1–3帧，固定尾4会包含旧帧新候选，须另记；不能一概说旧候选全部丢弃。 |
| Merge 与已提交字段 | [pipeline.py:799](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:799>)–830读取旧position/normal，匹配只追加来源ID；1082追加未匹配对象。 | 正常merge没有修改旧position/normal/radius。旧字段不变与新一次GA的旧pointmap变化可同时为真。旧点图只是旧Surfel生成的原材料；本页未实际构造/比较Surfel。 |
| 查询时机 | [pipeline.py:1249](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:1249>)先检索→1270采样→1293保留target→1305重建/提交→下一次1249再检索。 | 追加后的 focal 均值影响**后续**查询，不能倒因为当前已完成的生成。渲染637–647、可见来源投票479–494、选择context是后续真实传递需测的环节。 |

边界：`undo_latest_move` 在1357–1369删除frame/K/pose/depth，1393–1401筛除Surfel，但不维护 `surfel_Ks`。这使撤销后的查询缓存另有潜在过期记录；**不是本次S26连续4→8组件路径，不扩展为已发生的撤销bug**。配置 shrink_factor=0.05 与查询处固定×0.65有不同用途（候选降采样/查询投影）；这里只记录原策略，不从常数不同直接判错。

## 2. 哪些参数真正固定，为什么 world frame 可比较

原 [surfel_inference.py:174](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/extern/CUT3R/surfel_inference.py:174>)–203 每次建立新scene，只 preset depth 与 pose，再MST+GA+clean。`cloud_opt/dust3r_opt/optimizer.py:22–57` 每次新建全部focal与depth；默认 `optimize_pp=False`，pp保持图像中心；35–38、53–55中旧focal也在可训练的整栈。MST在 `init_im_poses.py:133–139` 对所有允许写入的focal重设初值；没有从上轮 `surfel_Ks` 初始化。

| 参数 | 原受约束GA策略 |
|---|---|
| 全部 image pose | `optimizer.py:102–121` preset后整栈冻结，`norm_pw_scale=False`；`base_opt.py:243–247`使MST不能覆写被冻结pose。 |
| 旧 prefix depth | `optimizer.py:218–224` 按 `zip(range(N), old_depths)` 只写并冻结旧prefix；227–246保存log并exp还原。新帧depth继续可优化。 |
| 旧/新 focal | 全部可优化，并随新一次MST/GA重新估计；166–176定义log-focal写入与解码。原 wrapper **没有**调用 `preset_focal`。 |
| principal point | 默认固定中心（22、39–57、190–191），相同预处理尺寸时跨调用相同。 |
| pairwise pose / adaptors | `base_opt.py:163–169` pairwise pose可训练；adaptors默认 `allow_pw_adaptors=False`（113、169）。二者不要混称为给定image pose。 |
| clean | `base_opt.py:349–359`重算投影/深度后只改conf，不冻结或覆写world点。 |

旧点位置的原公式（`optimizer.py:251–261,291–300`）为

`X_i(u,v)=R_i·[d_i(u,v)(u-cx_i)/f_i, d_i(u,v)(v-cy_i)/f_i, d_i(u,v)]ᵀ+t_i`。

所以固定 d、R、t、pp **不足以固定 X**。若f改变，离主点的像素一般沿相机横向移动，光轴深度可以完全不变。最强反例同样明确：f不变、差异仅在舍入内、或只看主点/退化像素，不能宣称显著旧几何变化；f变化也未必使真实几何更差。

比较不是把不同的全局坐标系强行相减：生成时 `torch.cat` 新建 `all_c2ws`（pipeline1263），中心化/缩放/翻轴只作用这个生成条件tensor（1089–1131），1297保存的是未被这份新cat修改的 `target_c2ws`；976与查询636均通过同一 `get_transformed_c2ws` 的deepcopy/翻列（950–955）。跨次GA使用相同历史给定相机的world坐标；MST拟合到known poses后不能再写已冻结image pose。仍需在未来输出中实际核旧pose一致和内部参数冻结；不能仅凭本页断言任意运行都满足。

## 3. 不增加GA即可做的最小判别（未来，尚未计算）

输入限定为全部S26作业封存后的 `common_old/output.npz` 与三个8图 `output.npz`；只取旧索引0–3的depth/focal/pp/c2w/point_cloud。**GT不需要、新网络前向0、额外GA0**。这些计算若另行冻结，应独立记录为“保存预测的提交一致性诊断”，不混入新4深度主评分。

1. **先核条件**：同旧frame ID与像素网格；旧depth/pose与共同输入在已冻结容差内，pp一致；使用运行日志核preset后旧log-depth/pose参数确实逐值冻结。条件失败则停，此时点差不能归因于focal。
2. **逐帧报告实际变化**：`Δf_i=f_i^8−f_i^4`、`|Δf_i|/f_i^4`；逐像素 `||X_i^8−X_i^4||₂` 的均值/中位数/P95/max，另报告全有效像素分母及超过预先数值容差的比例；不按confidence筛选让变化消失。点差是状态不一致量，**不是GT几何误差**。
3. **检查解释是否闭合**：由每份保存的d/R/t/pp/f独立重建X；再只把A的f换成B的f，其他A字段不动，算“仅f变化预测的ΔX”。比较实际ΔX与该分量/残差，显式保留preset编码/浮点差异。不得对两份点云做事后SE3/Sim3对齐来掩盖横向变化。只有新f可解释的非微小ΔX，才支撑这个局部机制发生；也仍不证明有害。
4. **缓存机制独立计算**：若以受控两次4→8构造的源码语义回放，查询焦距是 `0.65·mean(concat(f^4[0:4], f^8[0:8]))`，对比“仅当前8份” `0.65·mean(f^8)`，并列每个frame的快照计数2/1。即使每帧f从不变，只要早/晚frame focal分布不同，重复权重也可改变均值；若各轮均值相同，则不改变。这只是**源码算术回放**：S26尚未调用construct，不能称已观测到其真实cache或query变化。

最有解释力的初步比较是common原CUT4→CUT8，但它仍包含原CUT与TTT仓库CUT模式的既有容差兼容边界、图从3条边扩至7条、新联合目标与初始化；**不是只改变历史长度的严格因果实验**。TTT/FILT共同使用CUT旧图是当前消费者公平条件，不能把它们相对CUT旧图的更大偏移自动称为方法更差。真实原生成输入一般还有历史长度/目标数量/图像分布差别，8帧pilot不代表自然长生成失败。

否决/升级门槛：四旧frame f/X无超容差变化则当前pilot不支持第一机制；pool/current查询f相同则该pilot不支持第二机制。只有非微小变化仍不足立项：至少还需实际原Surfel快照、同query相机/K下的depth/index/cos及context IDs，和独立几何或生成一致性判据证明有害传递。变化有益或不影响消费者时不得包装成失败。

## 4. 必须先打败的普通修复/对照

| 对照 | 实际要固定/更新什么 | 本页的评判 |
|---|---|---|
| 冻结旧focal | 保存旧focal，与旧depth/pose联合固定；新focal仍按原优化。 | 首选简单控制；原 `preset_focal` 123–131要求完整mask且最后冻结**整栈**，直接传旧4会把新4也冻结，不能冒充只冻结旧focal。实现需独立审查参数策略，不在本轮改源。 |
| 重建/重积分旧map | 若允许重标定，则让已提交map与当前d/K/pose同步重建，并维护来源、候选mask与预算。 | 常规地图维护控制，不应把重建旧点本身当创新；额外成本必须等预算或完整报告。 |
| 当前每帧一份focal缓存 | 将查询缓存作为frame→当前focal映射，替换或只追加新帧，撤销同步删除。 | 明确缓存语义的工程修复；须区分“当前快照均值”与原历史估计均值可能有意平滑的偏好，性能收益未证。 |
| 相机标定/地图版本的一致性控制 | 固定共同标定，或每次标定更新后同步更新依赖地图与查询参数；只把这类常规SLAM控制作为应比较的配置。 | 本轮没有文献新颖性调查，不声称SLAM中没人解决；若普通冻结/重建/缓存修复已解决且无更深剩余失败，按普通bugfix结束，不立新方法。 |

**当前处置：保留为可证伪的 baseline 消费者一致性问题，等待S26已保存数据的零GA诊断；不运行新实验、不预言数值。** 它与S/M latent干预没有必然联系：若症结仅在消费者标定/缓存提交，就先修/控制消费者，避免在无关 recurrent state上继续加方法。
