# S34 后唯一决策：停止尺度方法试探，回到真实生成缓存闭环

完成记录 UTC：2026-09-06T22:01:49.742474+00:00。**本轮只有固定源码与已有 JSON 阅读、判断和文档写入；0 新数组/GT/模型/GA/渲染/实验。** 原 proposal 仍是 Geometry-aware World Modeling。本文不修改已完成结果，不启动下一轮。

**决策：Reject 当前“公共尺度约束是新方法、可提升长期生成”的叙事。收束短窗尺度实验。下一项科学执行只保留既有 S20 原 VMem 两批真实生成与缓存回流基线；现在标为 NOT_READY_RESOURCE，不另造可执行代理来填空。** 这是必要的基线闭环，仍不是新方法或 PhD／CCF A 验收。

## 已解决什么，未解决什么

| 同一新4帧等权均值 | 零步 | 自由400步 | 公共尺度约束400步 |
|---|---:|---:|---:|
| AbsRel（%）↓ | 4.605911664509 | 4.347382601427 | 4.322076250691 |
| RMSE（米）↓ | 0.238581619313 | 0.232023921613 | 0.230830910885 |

原旧4预测固定后，自由优化自身已降低 AbsRel 0.258529 个百分点，约束仅再降低 0.025306 个百分点。这是一个已见、约0.236秒的八帧窗口，共同 GT 相机是给定控制；不是无 GT 部署实验。index7 的 AbsRel 两个400臂均略差零步，不能写“四帧全胜”。[完整主结果](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S34_depth_scoring/metrics.json)、[另一作者深度/raw核验](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_independent_numeric_review/receipt.json)均已 PASS。

自由臂有效 pair log-scale 均值漂移最大 0.33065718692717944，但准确率组均值仍改善；约束臂均值偏移约 8.34e-8。因此“发生尺度漂移”不是这里的精度失败判据，更不是记忆遗忘判据。S30–S33 全深度可训练的损害不能直接搬到旧深度冻结任务。普通 getter 修复与尺度控制保留为工程对照，不再寻找一个名字把它们变成创新。

地图616/651/650、可见域和来源票权确有变化，但三臂候选均为有序[0,1,2,3,4,5,6,7]、每来源quota1。渲染外参相同，历史平均焦距却为402.086105347/406.636479696/405.876960754，再乘0.65；渲染变化同时含几何与内参差异，不能归因于几何单独变好。[另一作者consumer保存量报告](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_consumer_numeric_review/executed/saved_quantity_report.json)仅证明保存量与来源数学，没有证明可见性正确或生成质量。

## 当前代理为何没有通向生成的已证收益

固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 的依赖路径有一个明确边界：

1. 原票权函数设 `n=min(context4+10,k)`，配额函数在 `n=k` 返回每项1，再按来源 ID 排序。本次k=8；权重变化不会改变有序候选。k=0时仍保留原空返回，不能补假候选。[原配额与排序](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L411-L502)
2. 随后排序与NMS只读取该候选、共同历史/目标相机、配置及原NMS状态；实际 latent 数量约束最大 context 数。**在同一合法历史状态、相同候选和缓存可用性条件下**，这次仅改变地图/票权不会改变最终ID。该结论是确定性源码依赖推论；S34没有合法len5历史及真实缓存，因此未运行NMS、未观测具体context ID。[原排序/NMS](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L663-L754)
3. 选定ID之后读取实际 `latents/encoder_embeddings/c2ws/self.Ks`；`self.Ks`追加的是请求 `target_Ks`，不是用于渲染的 `surfel_Ks`。生成条件和translation scaling使用这些选中缓存与请求相机/K，未发现S34的raw depth/focal另一路直接进入sampler。[缓存选择](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L517-L522)、[条件与采样](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L1249-L1284)、[真实缓存写入](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L1286-L1298)

所以，在同一真实缓存、合法NMS状态、模型/RNG/目标请求下，相同context数据将给出相同条件；S34没有展示能改变该事件生成条件的机制。**这不是所有历史或更大候选池上的无效证明，也不是数值复现或已经生成了相同视频。** 该推论以本次query7已观察的候选不变为条件；S34未执行完整新4目标请求，不能断言一个未来合法生成请求重新渲染后仍返回这些候选。 不新加focal臂，不减少context+10，不直接添帧跨过14，不伪造latent/阈值去制造一个检索差异。

## 唯一下一实验与反证

要回答的最小未验证问题是：**原作者完整生成器在本机透明CPU适配后，能否通过原地图→渲染→默认NMS，实际把第一批生成的缓存送入第二批采样？** 这是原proposal后续研究的真实工作台，不是新增尺度假设。已有源审和地图桥接无法替代它。

直接续用[既有 S20 最小闭环协议](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md)，不另铺十套代理：作者changi初图，原相机入口，默认576×576/T8/50步/context4/target4/seed42，原Navigator两次独立 `turn_left(5)`、`turn_right(5)`。原历史1→5→9；第二批在len5合法初始化NMS。四组件必须是真实原权重，生成latent必须来自原 `samples_z`，不能重编码PIL顶替。两批之间不重播种。先跑原数学；S33约束和S34 mixed8断言不带入原基线，第二批是旧5/新4。

最少新增量是两次原采样（共100主模型前向预期，须以实测计数为准）及原5/9图几何更新；不能用一批或少步替代。保存真实条件、选中ID、latent/embedding/K来源、原NMS初值、padding去留、模型/采样计数与两批提交边界。唯一闭环通过条件是：完整第二批完成，至少一个generated ID的真实缓存实际进入该批条件，所有历史ID与原缓存一致。失败即反证“本机该预算下已能完成真实闭环”；若只进地图没进条件，不能报告缓存回流。它不检验票权连续敏感性，也不证明长期一致性质量。两批成功后先检查自然失败再决定方法；不能预言会失败或预先宣布收益。

沿S20建议上限：CPU8/FP32，第一批含加载1800秒、45GiB进程树RSS；第二批同一worker再1800秒、同内存上限，两批预算须在执行前一起冻结。上限是保护界，不是已测耗时或可运行保证。身份/非有限/空候选/不足合法context/设备算子失败、超时或超RSS均保留部分文件并停止；不事后改seed、步数、分辨率、NMS或权重来“完成”。生成目标没有sensor答案，不套TUM GT、无虚构逐帧质量指标。

**目前执行门未过。** 原主VMem与指定VAE尚无项目验收的齐备身份/加载回执；最后官方资源检查是2026-09-06 14:47–14:48 UTC，本轮没有重查网络或大权重，不能说今天仍必然401或永久不可用。[原资源记录](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_DEPENDENCY_ACCESS.md)、[最后有界官方复查](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S25_official_resource_recheck/report.md)。只有合法原权重齐备且环境/观察器就绪后才能冻结执行。若资源仍缺，完成S34交付、明确挂起这项生成依赖即可；不重复401/导入检查，不单独下载暂不能使用的大组件，不改用别的VAE冒充原基线。替换生成器会改变研究基线，需要另立范围，不是本次自动备选。

## 技能判定与停止标准

Supervisor2.2要求从强基线的实际剩余失败出发：这里普通自由优化已改善，原动机被更贴近消费者的对照明显削弱。idea-evaluator致命项先行：F1，公共尺度规范和梯度修复已有明确上游方法/源码亲缘，换常数不构成新机制；F6，短窗深度与票权不能验证长期生成主张。复用[DUSt3R原文/源码排重](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S29_upstream_baseline_comparison/review.md)及[Scal3R/LASER定点排查](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S32_nearby_literature/novelty_exclusions.md)，不重新堆文献或声称本轮全领域检索。更高只有本地普通基线微增；更快/更强/更省/更广均无新方法证据，不能评分为新颖贡献。

Claude科学批判用于保留焦距混杂、组均值与逐帧反例、GT相机条件、小样本和“条件链存在≠真实被消费”的构念边界。当前判定 **Reject and Pivot（退出尺度创新叙事，回到原生成基线）**。现在没有已成立的新方法，也没有可据现有短窗直接承诺的PhD/CCF A成果。该决定完成后停止本目录工作，不运行上述实验、不改主账；父任务负责资源决策与正式执行授权。
