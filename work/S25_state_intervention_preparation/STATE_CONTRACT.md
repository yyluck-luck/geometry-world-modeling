# S25 状态分支草稿：可执行能力与边界

状态：完成静态派生及普通容器检查；**模型初始化 0 次，模型前向 0 帧，数值兼容未验证，S25 实验未获执行决定**。本目录不读取 S24 结果、RGB 数组或 GT，不修改 S22/S24 已冻结源码，也不改主账。日期与文件 SHA 以 `static_preparation_receipt.json` 为准。

本轮沿用 R1 的因果问题及 Supervisor handbook 2.3 的“先拆基本假设”，再用 idea-evaluator / 本地 Claude scientific-critical-thinking 的“先排致命混淆”审实现。这里没有提出新方法、没有声称创新已成立，也没有重新拓展泛泛文献。

## 实际具备什么能力

`state_intervention_adapter.py` 在内存中从指定 FILT3R `forward_recurrent_lighter` 派生一个独立函数，不替换模型的原方法，不改源文件。源绑定继承 S22 的 124 个文件及其 manifest，包括已控制的 CPU RoPE FP16 适配；另绑定 `scripts/cut3r_rope_compat.py` 的 SHA，并检查实际 RoPE forward 已安装该 signed helper、base=100、F0=1。导入和静态派生只用 Python 标准库；调用运行接口时才需要已有的真实 FILT3R 模型及 torch。

它支持：在同一进程、同一模型上运行一个正常 prefix；只在最后一帧的写入处生成四个完整 checkpoint；随后每条分支读取完全相同的真实 RGB suffix，并继续正常 FILT 更新。也可以只保存 prefix checkpoint，之后再接一个事件帧。不支持在线门控策略、连续多帧冻结、跨进程 checkpoint 恢复、混合 batch reset、GPU 或自动挑选事件。

**当前不能运行实验。** 父任务须先依据 S24 的自然失败证据决定是否值得执行，再冻结事件、prefix/suffix、指标、兼容判据和资源预算。人工扰动产生的失败不能作为自然失败证据。S24 保存的 head/pose 预测并不是 recurrent checkpoint，不能从那些预测文件直接恢复本适配器需要的局部状态。

## 捕获时刻

冻结源 `src/dust3r/model.py` 的实际顺序是：图像编码 → 用旧 M 读 pose feature → 用旧 S 和该 feature 计算 candidate/decoder → 计算 new M → 生成 head → `ress.append(res_cpu)` → FILT 更新 S/P/EMA → 提交 M → reset → `_advance_prev_buffers`。

1. **pre-write**：位于 `ress.append(res_cpu)` 的下一条插入语句。此时当前 head 已经生成，S、M、P、EMA、prevCandidate、prevFeat 尚未提交当前写入。必须深克隆；Kalman helper 后面会原位更新 `kalman_stats['delta_ema']`。
2. **post-write**：位于 `_apply_stream_reset`、`prev_reset` 赋值和 `_advance_prev_buffers` 全部完成之后。它是下一帧实际读取的完整局部状态。
3. 在循环外把 pre/post 组合为四个 checkpoint；**不回头改当前 head**。每个 checkpoint 的 `next_index=i+1`，恢复使用 `enumerate(..., start=next_index)`，不会把切片首帧误作全序列 `i==0`，因此不会重建锚点或再使用首帧 pose token。入口要求 index 是真正的 int（拒绝 bool/float）、≥1，且恰等于完整且不重复的 prefix frame_ids 数量；dataclass 禁止直接重赋字段，但内部 tensor/dict 仍不得被调用方篡改。

四条分支共用唯一一次事件帧 head。研究中若报告“事件帧输出因冻结写入而改善”，即违反本合同。效果最早从下一帧出现。

## 四个写入动作

| 动作 | S 及其辅助量 | M | 保留的事实 |
|---|---|---|---|
| `normal` | post | post | 原 FILT 更新 |
| `freeze_s_aux` | pre | post | 撤销当前 S 整组写入 |
| `freeze_m` | post | pre | 撤销当前 pose-memory 写入 |
| `freeze_all` | pre | pre | 撤销两组写入；该帧依然被消费 |

S 整组固定为 `state_feat, state_cov, kalman_stats, prev_candidate_state_feat, prev_feat_i`。冻结 S 却仍写入 P/EMA/候选缓存，是另一种干预，不能标为这里的 freeze-S。

`prev_feat_i` 当前在 FILT gain helper 内被丢弃，但循环仍维护它；为保留完整循环状态和避免未来路由歧义，本合同仍捕获并随 S 整组冻结。`state_pos/init_*` 不属于当前可写动作，但必须进入 checkpoint。`prev_reset` 也必须保存；本适配器明确拒绝任何 reset 事件，不能把 reset 和 freeze 的优先级默默决定掉。

## 跨帧字段合同

| 字段 | 作用 | capture/restore |
|---|---|---|
| `state_feat` | S，下一帧 decoder 的旧 state | 深克隆；按动作取 pre/post |
| `mem` | M，下一帧 pose-retriever 的旧 memory | 深克隆；按动作取 pre/post |
| `state_cov` | FILT P，下一次 gain 的先验 | 随 S 深克隆，包括 None |
| `kalman_stats` | EMA 字典，现有键 delta_ema | 递归深克隆全部键；随 S |
| `prev_candidate_state_feat` | 上次 candidate，用于 delta | 深克隆；随 S |
| `prev_feat_i` | 上次编码特征缓存 | 深克隆；随 S |
| `state_pos` | state token 位置 | 深克隆，包括 None；结构量 |
| `init_state_feat` | 初始 S 锚点 | 深克隆；结构量 |
| `init_mem` | 初始 M 锚点 | 深克隆；结构量 |
| `prev_reset` | 是否走初始化 pose/gain 路由 | 保留布尔值；这里要求 False |
| `device` | 循环中更新为 tensor.device | 保留；只允许 CPU |
| `next_index` | 全局循环时刻，控制 i==0 | 单独保存 i+1；不可重置为 0 |
| `update_type/need_attn_for_update` | 本模型的更新路由 | 重新解析并核对 FILT3R/False |
| `frame_ids` | 已消费输入的 caller 提供标识 | append-only tuple，拒绝重复标识 |

`ress/all_state_args` 是输出累积器而非下一帧计算依赖。恢复调用只返回本次 suffix 的预测，不能把其局部输出下标当全局 i。上游 lighter 虽接受 `ret_state=True`，但 `all_state_args` 从未 append，实际返回空列表；本草稿另行提供完整 checkpoint。

`feat_i/new_state_feat/new_mem/dec/current head` 是当前帧临时量，不在下一帧读取；需延续的候选和特征已经进入 `prev_*`。四臂组合 post checkpoint 后不会再使用这些临时量。

## 循环局部状态之外

上述字段是完整**循环局部状态**，不自动等于整个 Python 进程的状态。实现额外捕获并恢复 named buffers、已审查的 RoPE `cache`、PositionGetter `cache_positions`、CPU torch RNG、Python RNG，以及已加载 numpy 的 RNG。cache 按共享对象去重，恢复时为分支深克隆；它们不是第四种可干预的记忆。

源码核查发现 LocalMemory `update_mem/inquire` 只操作/返回局部张量，不覆写 `self.mem`；decoder residual 使用 `x = x + ...`，没有就地改入参。RoPE/position 缓存是显式的模块外推理副作用。`to_gpu` 虽名为 GPU 工具，此处目标是 CPU：它新建 dict 并对张量 clone；它忽略 `true_shape` 等 metadata，后续原函数按图像形状重新构造 shape。`to_cpu` 新建容器但 CPU tensor 可能保持同一 storage；本实验不得在调用返回后修改预测张量并期待它是另一个分支的证据。

运行 guard 保留创建 adapter 时每个 module 的原始 training flag，**不会调用 eval()**。这与 S21/S22/S24 的既有模式保持一致；实际活跃的 Dropout、stochastic depth 或训练态 BatchNorm 会拒绝运行，而不是自动改模式。守卫还要求 CPU 8 threads、FP32 权重和输入、`torch.no_grad()`、关闭外层 CPU/CUDA autocast、原 FILT helper 路由、无 observer hook/实例方法替换，并绑定参数 version/identity 与全部 effective hparam。

仍须由后续独立数值兼容验证确认：外部库实现、编译/线程行为、未注册的自定义 hook/全局状态，以及 clone/restore 后 tensor layout 是否改变数值路径。参数 identity/version 是进程内防误改检查，不替代正式权重 SHA；运行方必须绑定权重、包版本、输入文件 SHA/顺序、预处理和输出 SHA。caller 的 frame_ids 不是自动核验的 RGB checksum。本文件不能诚实声称“捕获了所有可能的外部副作用”。

## 零干预的证明范围

`prepare_static.py` 自动做三件事：核对 S22 124 个源文件；从源 AST 派生函数及可读 diff；删除仅新增的四个 `_s25` guard，并还原函数名/额外参数/枚举起点后，与原 AST 逐节点严格比较。**95 条原语句全部原序保留，原算术及 helper 调用改写 0 条。** `_s25=None` 时 guard 均不执行，起点为 0，走原语句路径。

有 checkpoint 的 `normal` 分支则还执行了 clone、恢复与校验；相同 AST 不能证明这些操作对数值没有影响。现有 PASS 只指结构审查及普通字典/列表的分组选值、别名隔离、reset 拒绝检查。未导入 torch，未实例化模型，未执行真实或模拟模型前向。**numerical compatibility = NOT_RUN。**

## 后续需要多少前向

令 K≥1 为事件之前的 prefix 帧数，事件占 1 帧，H≥1 为干预之后用于判别的真实 suffix 帧数。这里不选择 K/H 或具体帧，不冻结预算。

| 可复用起点/检查范围 | 所需逐帧模型前向数 |
|---|---:|
| 已有本适配器的完整 prefix checkpoint，完成四臂因果比较 | `1 + 4H` |
| 只有 RGB/已保存 head，需要重放 prefix | `K + 1 + 4H` |
| 上项再加原函数完整正常序列，对照正常 head | `2(K+1) + 5H` |
| 再加独立的未切片派生函数正常轨迹，核对 split/resume 后完整局部状态 | `3(K+1) + 6H` |

理论最短 K=H=1：四臂比较需 6 帧次；加原函数 head 对照需 9；再加未切片 checkpoint 对照需 12。它们只是调用数下界，不是足以证明重要失败的研究样本量。仅做零干预 head 兼容而不消费另外三臂时为 `2(K+1+H)`；加入未切片完整-state 对照为 `3(K+1+H)`。

事件帧只算一次，构造四个 checkpoint 不含模型前向。state/runtime 深克隆增加内存与复制耗时；不会因为冻结写入就少跑 decoder，不能据此声称加速。分支可顺序运行、共用一份模型权重，峰值额外存储约为 pre/post/四臂 state 与 runtime 包，加本次返回的 head 张量。实际耗时、RSS、state 包字节数均未测量，预算须在后续冻结，不能挪用 S24 的预算宣称已授权 S25。

## 最小兼容验收要求与可证伪边界

执行前先固定同一真实 RGB prefix/事件/suffix、S22 同源权重与模式、容许误差及比较字段。至少比较原函数和未切片派生函数所有返回 head，比较未切片派生和 split/resume 正常臂的所有 head 与完整 state。四臂必须绑定同一个事件 head 的 SHA；输入 suffix 的文件 SHA/顺序也必须相同。反向改变分支执行顺序后重复一个短正常 continuation 可检查分支污染，但是否增加这项前向由后续协议决定。

任何正常兼容不通过、当前 head 被干预改变、缺失 state 字段、共享 EMA 污染或 source/weight/input 不一致，先否决这个实现，不能拿因果分支差异解释科研问题。若实现兼容通过而自然失败中四臂没有可区分、可稳定重现的后续影响，应否决或缩小 R1 的机制假设；不能继续加重人工扰动以制造成功。

这四臂只能识别两组写入对后续几何预测的因果影响，不能单独证明哪组状态“错误”、不能分离 S 的每个辅助量贡献，也不能直接证明长视频生成一致性改善。冻结带来的收益仍可能只是少写入或缩短有效历史；创新须经过相近方法比较和进一步机制实验，当前状态仍是待判别问题。

## 本轮独立审查后的修订

- 根任务指出初稿强制 eval 与既有 baseline 的 training=True 不一致：已改为保留全部原 training flags，并拒绝真正活跃的随机/批统计层；未执行任何模型时已纠正。
- 根任务及 s14_feature_extractor 指出 signed RoPE 是源树外的 class-level 运行适配：已补 helper SHA、实际 forward 来源/identity 和 base/F0 核对。
- s14_feature_extractor 指出可变 checkpoint 可能让全局 i 被误改：已补冻结 dataclass、绝对 i/完整 prefix 长度及类型检查，并增加无模型的软件检查。
- 上述修订只改本目录草稿和合同。最后一次静态检查日期及所有最终文件身份写入本目录 receipt；没有把任何一项修订包装成科研增益。
