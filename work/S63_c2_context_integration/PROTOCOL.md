# S63：C2 原失败输入到真实缓存条件的有限检查

本协议在此次新缓存载荷读取前固定。作者只读源码及事件/descriptor 元数据、完成静态编译；root 在不同作者源码审查后负责一次真实执行。使用原 C2 V9 第一批完成后、第二动作失败前的保存状态；不生成图像、不补填原失败 C2 或原 cohort。

问题是：固定 S61 单位组件能否让这份真正失败的输入通过原选帧函数，返回与真实历史缓存逐 slot 相同的条件？这比已有 S61 renderer 组件检查多走原 context/NMS/缓存返回；不是生成质量检验，也不是新方法。

## 固定来源与读取范围

唯一档案为 `results/S47B_C2_confirmation_generation_v9/archive`，在源码 `ARCHIVE` 中固定，并作为显式参数传给 `Decoder`。S62 的 decoder、指纹和 AST 数值提取 helper 复制用于此新文件；旧 S62 runner 只核来源 SHA，不导入其 B0 输入、oracle 或 main。程序内 `PINS` 固定 11 个原源码/元数据身份，包括 C2 V9 manifest/archive、原 pipeline/util/配置及 S61 adapter 最终源码票。

- seq50 `map_commit.cache`：五份真实 c2w/K/latent/embedding/surfel_Ks。首 c2w 为 float64[4,4]，其余四份 float32；K 为 float32[3,3]，latent 为 float32[4,72,72]，embedding 为 float32[1024]，focal 为 float32[1]。只数 pil_frames 长度五，不读图片。
- seq56：float32[4,4,4] 目标、原 None NMS 参数及空 kwargs。
- seq58：515 份 surfel position/normal/radius/source_ids、surfel_to_timestep、实际 renderer query pose/focal/kwargs。seq58 focal 描述符须与 seq50 相同；实际求均值使用 seq50 focal，不能使用 map 构造前的 seq44 focal。位置/法线保持 float32[3]，半径 float64 标量，不提前改精度。
- seq60：原 depth/index/cos 三张空数值图；seq62：原空权重/配额；seq64：精确 Python float64 阈值及 NMS 元数据；seq65：异常类型、消息和 phase 元数据。

按已读元数据，联合 1,496 个唯一 blob、1,631,256 B；该统计包含已见几何和原空图，不能写成全部首次接触的数据。runtime 对每个实际 blob 核 SHA/大小/声明 dtype/shape/finite，以原 little-endian/C 布局解码；唯一读取立即落 `readlist.jsonl`，重复 descriptor 仍核同一字节身份。实际总数/字节必须与上述范围一致。禁止选择 `surfel_depths`、RGB/pil_image 或 color 分支；没有重新编码需求。

另在修复臂成功返回后读取已经见过的 S61 `execution_01/recorded_length_unit.npz` 作为数值参考，固定 SHA `1b2fefa8c44eeca818f4aab979b95b176fee4875df1e6c3538615477b8b23bfe`。该 NPZ 的实际读取字节和 SHA 单列在 `seen_reference_read`，不混入 archive 的 1,496 项。它不是未见答案，也不存在 C2 成功 context 参考。

## 原计算保持不变

只 AST 原样提取 pipeline 六个方法：render_surfels_to_image、get_frame_distribution、process_retrieved_spatial_information、geodesic_distance、get_transformed_c2ws、get_context_info；再提取 util 的 average_camera_pose。沿用 SciPy 平均 pose、原 y/z 列翻转、focal×0.65、CPU/FP32 NMS 距离及 Python 阈值除 1.2。config 固定 context_num_frames=4、translation_distance_weight=0.1、surfel 512×288、NMS=True、visualize=False，Torch2.7.0/NumPy1.26.4/CPU8。root 外层记录 Python/SciPy 版本，当前环境延续 S62。

不导入完整 pipeline、不实例化模型或 Navigator、不调用 get_cond/编码器/去噪/采样。每臂用独立输入深拷贝建立轻量对象，五个 None 只提供 pil_frames 的长度；四类真实条件始终来自 seq50 数组。

## 两臂固定顺序和判据

每臂原 renderer、原 retrieval 各调用一次；原函数自己根据五帧历史重算 initial_threshold，不提前注入保存答案。renderer hook 首先对原函数构造的 query pose/focal 逐值、dtype、shape 精确核 seq58，kwargs 精确相同。三图即时保存，然后核 keys、shape[288,512]、depth/cos float32、index int32、全部 finite；index 在[-1,514]，depth 非负且有支持处严格正、背景 depth/cos 为零，cos 在[-1−1e-6,1+1e-6]。这些检查失败不能被算成预期 IndexError。

1. **original：预期原异常。** 三图须对 seq60 逐值精确重现且无支持，权重/配额须对 seq62 精确为空。完整原 get_context_info 必须抛出 `IndexError: list index out of range`，最内层 traceback 的 code object 必须就是抽取的 get_context_info、filename 必须为原 pipeline 路径加 `[six-methods]`、行号 711；固定原源码该行须是 `selected_indices.append(sorted_frames[0])`。该帧 locals 中 sorted_frames、candidates、frame_count 均空且 max_frames=0；pairwise_distances、percentile_idx、is_second_step、NMS 模式与 seq64 精确相同，initial_threshold 也精确一致。保存这次实际 traceback 和 locals 证据；seq65 只存类型/消息/phase，不能声称它含原完整栈。只有全部满足才记 `PASS_EXPECTED_ORIGINAL_FAILURE`，不能生成成功 context 文件。任意别的异常或意外成功返回均失败，停止后臂。
2. **canonical_units：修复路径单独判定。** 只把 renderer hook 换成固定 S61 render_in_canonical_units，其余完整原函数不变。组件复制换算所有 position/radius/camera translation，depth 单位票必须保留。任何异常，包括相同 IndexError，均记该臂 FAIL。原 get_context_info 必须返回四个 int64、0–4 内、互不重复的 ID，记录实际顺序，不预设 B0 或其他具体 ID。四类输出须为原 FP32 结果，shape/逐值精确等于这些 ID 对应的 seq50 真实缓存，各输出 finite。记录全部权重、配额、ID、单位票、initial_threshold；不改变 NMS 或添加 fallback。对已见 S61 数值参考，index 精确比较，depth/cos 固定 atol=rtol=1e-6，报告最大绝对差。

两臂分别核原输入、独立副本及对象实际挂接缓存的前后字节指纹，包含所有 target、geometry/source ID/mapping、五帧四类缓存和 focal；不得因临时单位换算修改这些缓存。允许原函数更新自己的 initial_threshold，该派生状态不是保存缓存。只有第一臂精确复现预期原失败、第二臂完整通过，顶层才是 `PASS_C2_SAVED_CONTEXT_INTEGRATION`；原失败通过不能覆盖修复失败。

## 一次运行与停止边界

root 在项目根目录使用现有环境并设置外部 120 秒总时限：

```sh
.venv-cut3r/bin/python -B work/S63_c2_context_integration/replay_context.py
```

`execution_01` 必须不存在，程序 create-only 建立，不重试。每臂即时保存数值 maps NPZ；仅真正返回的 context 保存对应 NPZ。最终 `receipt.json` 记录实际 UTC/耗时、源身份、各臂状态、异常/返回、调用次数、数值校验、读清单总量、前后指纹、各产物 SHA；成功和失败文件均保留并设 0444。外部硬终止若阻止 finally 留票，root 外部终态及已落盘部分文件描述失败，不能把缺票算通过。

即使通过，证据仍只到同一份已见 C2 输入的 get_context_info 返回，不核 get_cond 的 CLIP/射线拼接、后续采样或画质，不证明跨场景鲁棒性或完整生产修复。普通单位工程不是创新。后续生产接入与完整生成须另建明确变体，原源码、V9 失败和原 cohort 缺失状态保持不变。
