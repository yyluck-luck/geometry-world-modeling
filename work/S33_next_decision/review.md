# S33 后唯一下一决策：共用旧图的 4→8 真实消费者 pilot

**建议停止在 S32/S33 三个已见短窗上调参。唯一下一项是复用 S26B 的 fr2_desk 首 8 配对帧，将同一份旧四帧预测和已提交地图固定，比较零步、普通自由尺度 400 步、普通共同配对尺度 400 步，再实际经过原 Surfel append、renderer 和来源票权。** 这是消费者衔接与强基线检查，不是创新方法；当前只完成源码/保存 JSON 决策审，没有新推理、MST、优化、数组或 GT 读取。执行须由根任务另行形成并冻结最小合同。

## 当前证据与必须收束的主张

S33 主评分 JSON 中，三个可用窗的新条件在 AbsRel、RMSE、δ1 均优于各自零步及事后 k 对照。下表为四帧等权的 AbsRel 百分比；完整精确数值、其他指标和所有 NA 见本目录 `evidence_excerpt.json`，直接摘自既有评分，不是本轮重新评分。

| 固定窗口 | 零步 | 自由 400 | 自由 400 后 k | S33 普通尺度约束 |
|---|---:|---:|---:|---:|
| fr2_desk_j1 | NA | NA | NA | NA |
| fr2_desk_j2 | 11.49439 | 40.00581 | 12.33071 | 10.82468 |
| fr1_xyz_j1 | 13.20508 | 17.45834 | 13.19783 | 12.63547 |
| fr1_xyz_j2 | 10.16412 | 19.30582 | 10.20706 | 9.05079 |

全分母仍为 4 窗、16 组、64 帧条件行：48 有评分、16 NA。NA 不是好结果也不是零误差。本审接到任务时不同作者数值核验尚待；这里的判断限定于主评分与生产回执。若根随后收到复核，以新正式报告为准，不在这里假定已通过。

Supervisor 2.2 要求从最强基线的剩余失败推进。S33 已说明普通公共尺度约束能修复这个局部设置的一部分问题，不能继续把它写成“现有方法解决不了”。idea-evaluator 的致命缺陷审仍判**创新声明不通过**：公共尺度归一化已有 DUSt3R 原文/代码覆盖；本轮没有新的实质机制；约 0.1 秒、已见场景、给定 GT 相机、所有深度可训练，均限制外推。本地 Claude 科学批判技能用于下面的替代解释：原消费者已有冻结旧深度，它本身可能就足够阻止该失败。Scal3R/LASER 的既有排重边界沿用 S32 决策稿，不再泛列候选。

## 为什么旧四帧冻结必须重新问一次

固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`。原 `surfel_inference.py:174–218` 按 `preset_depth → preset_pose → MST/GA → clean` 调用；原 pipeline 把历史 depth 传给下一次重建（`modeling/pipeline.py:976–996`）。实际优化器是 `cloud_opt/dust3r_opt/optimizer.py`。

| 变量/路径 | S33 已实测设置 | 下一消费者设置 |
|---|---|---|
| 图数、star | 4 图、3 边 | 8 图、7 边；anchor0 self/conf_self，后续 other/conf |
| depth 参数 | 四个全部可训练 | 旧 0–3 冻结，新 4–7 可训练 |
| 相机、pp | 全部冻结 | 全部冻结；相机为同一已封存光学 c2w 条件 |
| focal | 全部可训练 | **仍全部可训练，包括旧四个**，不顺手再加 focal 冻结 |
| pair pose/scale | 自由或共同有效 log-scale 均值固定 | 同两种普通对照，但对全部七条边取均值 |
| 历史地图 | 没有 | 共用同一份实际构建的 old4 Surfel 状态 |

原 `preset_depth:218–224` 将四份米制 depth 依次写入前四个参数并设 `requires_grad=False`。MST 在 `init_im_poses.py:131–139` 确实会尝试调用全部八个 `_set_depthmap`，但该 setter 的 `optimizer.py:239–242` 仅在 `requires_grad or force` 才写；原 MST 没传 force。因此源码预期是旧四个不会被 MST 重置，不能凭“调用了 setter”就判被覆盖，也不能免去实际冻结检查。

S28 的唯一 getter 修复必须原样保留为可微 `torch.stack(...).float().exp()`：旧叶保持 False，新叶保持 True。不能搬来 S33 的“全四个都有 grad”、33 个状态或三边断言。下一次要核八帧/七边的实际完整参数与 buffer 名单；旧 grad 为 None 且原 log 参数逐字不变，新四个 400 步 grad 有限且非 None（真零梯度合法）。固定旧深度已破坏“全体 depth 一起缩放”的可行路径，故 S33 的 all-trainable 机制不能直接外推。

## 唯一输入与复用证据

采用**已经用于 S26/S26B 的 fr2_desk 首 8 配对帧**，历史 0–3、新增 4–7，时间 1311868164.363181–1311868164.599061，共 0.235880 秒；该 pilot 的分母是一个已见历史、三个条件、每条件全部新四帧。它不替换或改写 S33 的四窗分母，不称未见泛化。原始给定相机也已被评分阶段使用，这是显式 oracle 相机条件。

1. **八帧消费头**只用 S26B manifest 中 `candidate.archives.cut3r`，即 S21 `cut3r/frame_0000…0007.npz` 的完整既有前缀，保留历史 anchor0；不混入 S32 fresh4、不截取其他长序列中段当新 anchor、不另跑模型。S26B `compatibility_receipt.json` 已实际验证此来源的完整头无损拼装、star 和八张原 PIL 预处理；它明确不宣称“新的八帧 embedded 模型数值等价”。这里称原消费者的保存头重放，不称整机 VMem 原推理复现。
2. **共同旧 depth**只用 `results/S29_scale_control/C2a/initial_decoded.npz` 的已封存零步 depth；它来自 S21 `original4/frame_0000…0003.npz`、原消费者 MST 的 C2a 单位尺度初始化，无 sensor depth 输入。S30 的 `C2a/s29_reference_gate.json` 已实际确认其新起点完整 33 raw 状态、objective、alignment 与该 S29 起点逐字相同。选择这份已知较强零步作为固定旧图，是事后研究决策，不能伪装此前盲选。**不重用 S26 原坍缩的 common_old，也不把 S30 优化后的 depth 当零步。**
3. **旧四帧头与八帧头不等同。** 前者是 S21 original4 源，后者是 S21 cut3r/TTT 源 CUT 路由；前四个 archive SHA 分别不同。既有四帧跨源码兼容是容差级证据，不是八帧前缀逐字证据。S26B 的 all-head/star exact 是“各来源自己的保存值→consumer”，不是“这两来源相等”。合法性在于原 pipeline 就会把已经提交的旧 depth 作为外部约束再次传入；本 pilot 固定同一 old packet 给所有条件。**不设置一个已知不成立的跨源 byte-equality 门，也不把不等说成实验故障。**
4. 相机身份有直接既存证据：S29 `inputs_seal.json` 的 `control_sha256` 与 S26B control receipt 的八帧文件 SHA 都为 `c004c415b5bca43ae9a22cf63b542e7171eec29e31bf985c7e36327d1f5c0194`，共同父 manifest 为 `147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c`。S29 使用它的前四个，八图使用完整同一个；未来运行仍须核实际数组身份、旧 decoded c2w 与同前缀容差一致，不能仅比较字符串。TUM 光学 c2w 直接给 `prepare_output`，不再次翻转；pipeline 表示才右乘 diag(1,-1,-1,1)，调用原转光学函数后回到共同 world。
5. 原 S26 adapter 有可复用的 `derive_original_functions/load_saved_predictions/load_original_views/assemble_saved_output`。但 `CommonOldDepth` 和 `run_original_ga` 目前硬要求旧来源名 `original_cut3r_saved4_given_pose_no_depth_ga400`（adapter:156–205）：新文件必须显式支持 `S29_C2a_saved_MST_zero_step` 的真实 provenance 与 seal，不能给 S29 结果贴假的 original400 标签以绕过检查。只改新 adapter，不改旧冻结源。

共同 old4 packet 同时从 S29 `initial_decoded` 和完整 `initial_raw` 恢复 depth/world/focal/pp/c2w/raw conf；它是未 clean 的初态，不能伪造已 clean receipt。未来只在独立副本上调用一次原 `base_opt.py:581–... clean_pointcloud`，记录这次新 clean，保存实际结果；不运行 common4 MST/Adam。通过 S18 已验证的 `OriginalGeometryKernel` 原点图缩小、pointmap-to-surfel 与 merge 路径构建**一次**旧地图并封存。三条件分别深复制完整地图及可变 source 列表、c2ws、K 历史，不能共用可变对象。

## 最小执行顺序与真实消费者边界

只有三个端点：`old_fixed_zero`、`old_fixed_free_400`、`old_fixed_common_scale_400`。两条 400 臂各 fresh CPU8 进程、同一原 seed/PIL/star/MST/C2a 初始化、修 getter、原目标/Adam 400/.01/linear 与原 clean。自由臂不加尺度 factor；约束臂仅在同一 MST 后取七边 `m0=ell.detach().mean().clone()`，factor=`exp(m0-ell.mean())`，当前 mean 不 detach，原 norm_pw_scale=False；原完整 3×4 变换一起乘 factor，不能只缩旋转或改 translation 单位。初态 factor=1。

- 两次重新 MST 是为了合法创建两个可训练实例，**必须在第一步前核本次两臂完整 raw 名/shape/dtype/flags/bytes 及 decoded/objective 相同**。不是与旧四图 S29 的 33 个状态逐字比较；它们不是同一优化问题。零步直接保存自由臂该内存初态，原 clean 在副本上执行，不能让 zero clean 修改训练实例的 conf/权重。最小新增总数为 2 MST、14 PnP、800 Adam/反传，0 模型；old4 一次 clean 加三个端点各一次 clean，总 4 次新 clean。沿原 observer 每 400 臂保留 403 objective，零步复用已有初态 objective，不追加优化或挑步。
- **冻结门在 preset 后、MST 后、400 后、clean 后均核。** 注册旧 log-depth 与全相机/pp 参数保持同名、同对象、同值；旧 depth 输出经过 `log→exp`、c2w 经原编码解码，和输入按预冻 `atol=rtol=1e-5` 核对，不要求米制文件值逐字相同，也不允许覆写输出来通过门。记录旧 depth 重新 log 存储与反 exp 的最大差。旧 decoded world 可随 focal 改变，不能误当旧 depth 破坏。
- 对每个最终八图结果，真实执行 pipeline:990–1082 的消费者语义：原 all8 focal 追加到旧 4 项 `surfel_Ks`，故长度从 4 变 12；原 all8 depth cache 替换。原降采样倍率 .05、conf 阈值/分位数、normal、radius、Octree merge 均保持。旧地图非空时 `start_idx=8-4=4`，仅新四帧候选进入地图；重建旧四帧 world 不覆写已提交旧位置/normal/radius，匹配新观察只能追加 source IDs，未匹配再 append。保存真实新增/匹配数量、source lists、完整最终地图以及旧几何不变门。**不同时修 focal cache 重复追加或重建旧地图**，否则不再是这一个对照。
- 用同一八帧里预定的最后一个给定相机作为唯一自查询视角，固定为 `target_c2ws=[C_pipeline[7]]`。不读取其 RGB/GT 去选查询、不扩未来窗。该视角已在输入内，标签是**同视角消费者自查询诊断**，不是 novel-view 或未来预测评测。三条件都走原 render 和 process_retrieved_spatial_information，保存 depth、surfel_index_map、cosine、来源票权和 candidate 配额。不能以不同地图的整数 surfel ID 差异直接解释几何改善；要保留它所指向的真实 world/source 对应。

原接口没有问题的部分已由 S18 的真实几何→原 Surfel/renderer/来源投票验证，复用 `src/s18_original_kernels.py`、`src/vmem_memory_kernel.py`、`src/vmem_retrieval_kernel.py` 中对应原函数。S18 runner 的二帧计数/每源只计一次等断言不适用于八帧，不直接复制。下一轮只核必要的新混合 depth 冻结、两臂同初态、实际 append 与查询输出，不再重复 S18 旧实验或增加交叉交换/focal/步数扫描。

**默认最终 context IDs 在本 pilot 中明确未执行。** 原 `pipeline.py:674–708` 只在 `len(pil_frames)==5` 时建立 NMS 的 initial_threshold，4→8 人工冷启动缺少这段历史；`671` 又用实际 latent cache 数量，`753–765` 取真实 latents/encoder embeddings。`src/vmem_retrieval_kernel.py:244–335` 也保留这些依赖。不能随意设阈值、关 NMS、伪造 latent 或把 candidate 配额叫最终选图。原生 1→5→9 轨迹或已封存合法 cache/NMS 状态是继续默认最终选择的真实必要条件，**不是本轮又加的第四臂或另一实验**。本 pilot 能证明实际 map/render/选图前票权有没有变化；最终 context 和生成收益仍为 NA。

## 判别、停止与资源

主要科学比较只评新 4–7 的原尺度 depth：两条 400 臂及零步全部封存后，复用 S26B 原四张 GT 规则，完整有效 GT 分母、逐帧和四帧等权 AbsRel/RMSE/δ1；无 GT 拟合、conf 丢点、远距截断或选 best step。原 S31 对全部八图乘 k 会改动冻结旧 depth，**不合法，所以不增加 k 端点**。所有条件共享 old4 的质量；不将共用旧四帧混入均值稀释差异。

renderer 使用原 512×288 画布及方法自己的平均历史 focal×.65；它的 depth 是 Surfel 多边形渲染量，不是 TUM 相机原像素的传感器深度。因此本轮只做实际可见像素/来源票权的**描述性差异**，不将 sensor depth 简单 resize 后称可见性准确率。若将来确要“选图更好/可见性更准”，必须在合法默认选择状态、正确虚拟射线与传感器标定对应、真实生成之间补足证据，不能拿这次变化当质量标签。

| 预先可反证结果 | 唯一判断与停止动作 |
|---|---|
| 自由 400 在旧 depth 冻结后已经不损坏零步，且尺度约束不再优于它 | 旧图约束就是足够强的普通对照，收束 all-trainable 失败的外推；不再调 m0/focal/步数寻找胜例。 |
| 约束仅改 depth 指标，地图/实际可见来源票权相同或不足以区分 | 深度改善不足支持原 proposal 的记忆/选择主张，记录消费者未传递；不以更多代理迭代替代它。 |
| 地图/渲染/来源票权有变化，但正确性、默认 context 或生成没有验证 | 只报告真实消费变化；不能说更优检索或更优视频，转回所缺合法消费状态/生成资源。 |
| 三指标结论混合、无效/NA、预算或身份/冻结门失败 | 全部保存，单窗口不足判别，不临时选图、换旧图、改容差或自动重跑。 |

这里只承诺局部机制可否传到消费者；哪怕三指标胜出，也没有独立场景统计、长期记忆或新方法证据。最强反例是“冻结旧图后自由尺度 400 已足够好”，必须首先让它赢的机会公平存在。

建议待根冻结的预算：CPU8 顺序执行；共同旧 packet+原 clean+map 120 秒/4 GiB；每条八图 400 臂 240 秒/8 GiB；三端点 append/render 合计 120 秒/4 GiB；最终评分 120 秒/2 GiB；启动空盘至少 10 GiB。合计上限 840 秒，不是耗时预测。旧 S26B CUT 八图原作业记录约 34.9 秒，说明该组件曾可执行，不能据此保证新 getter 或 renderer 的时间。超过预算保留失败、不降分辨率或改步数。

本机有可用 CUT/GA 与原 Surfel 工具；暂无远程 GPU。完整 VMem 生成权重/原 VAE 最后官方复核在 2026-09-06 14:47–14:48 UTC，受限入口未取得实际载荷；本轮没有重查其当前可用性。真实 latent/encoder/生成资源并未由几何组件成功自动具备，视频尚未生成。根任务最终决策后才能实现/执行本 pilot；本报告不是执行许可或项目完成证书。

证据入口：[S33 原主评分](../../results/S33_pair_scale_scoring/metrics.json)、[S33 协议](../S33_preparation/PROTOCOL_CANDIDATE.md)、[S25 消费者路径](../S25_consumer_relevance/consumer_relevance.md)、[S26 已提交几何源码审](../S26_commit_consistency_source/audit.md)、[S26B 复用协议](../S26B_preparation/plan.md)、[S18 真实原 kernel 结果](../../docs/S18_RESULTS.md)。精确本地文件、行号、SHA、记录时刻与读取范围见 `sources.json` 和 `completion_receipt.json`。
