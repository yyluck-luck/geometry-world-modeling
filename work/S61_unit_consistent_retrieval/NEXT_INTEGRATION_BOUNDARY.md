# 下一步：用一份成功档案检查选帧与缓存索引接线

**可以不加载模型，离线检查到 `get_context_info` 返回的缓存条件。** 最小对象选 **B0 的第二次动作 `turn_right(5)`**：它已有 567 个 surfel、5 帧历史以及全部中间记录。源码身份已与 C2 V9 核对相同。下一步只需这一成功输入，不需要扩大到 C1 或再做一轮尺度矩阵。本文件是只读定位，尚未运行此接线检查。

## 准确接线位置

固定 `work/S20_environment/isolated_vmem_source/modeling/pipeline.py`：

| 原位置 | 实际输入 → 输出 |
|---|---|
| 635–645 | `target_c2ws` 的固定尾部 → `average_camera_pose`；4 个 context 对应这里只取最后 1 个目标姿态。636 行按源码翻 y/z 列，637–645 行从全部 `surfel_Ks` 求均值、乘 0.65，调用 renderer，尺寸 512×288、主点 (256,144)。 |
| 228–409，调用点 639 | surfel 位置/法线/半径、转换后相机、焦距/主点/尺寸 → 原 depth/index/cos 三图。**S61 只接在这个调用边界**；其 dimensionless depth 必须原样传下去，同时另存单位回执。 |
| 462–502，调用点 647 | 三图与 `surfel_to_timestep` → `timestep_weights, frame_count`；484–485 行含原 `cos/(1+depth)` 累加。原 411–460 配额函数保持原样，不能顺手修别处。 |
| 655–753 | 按 frame_count 展开候选；以原 `geodesic_distance` (191–226) 排序并做 NMS。使用全部原缓存 c2w，**不能把 S61 的临时归一化相机写回这里**。 |
| 517–522、754–764 | 最终 indices 同顺序读取 `c2ws / latents / encoder_embeddings / Ks`，分别转 CPU FP32/stack，返回五项 `context_*`。这就是本次建议停止点。 |
| 1250–1268 | 调用者解包结果，再拼接目标相机/K、计算 translation scaling、mask 并调用 `get_cond`；1271 后进入真实采样。此段与采样不属于本次最小索引检查。 |

`average_camera_pose` 位于 `utils/util.py:601–637`，依赖 NumPy、Torch、SciPy quaternion 平均；`get_transformed_c2ws` 在 pipeline 950–956。可仅从已核 SHA 的源码 AST 提取这些函数及 renderer、检索/配额、距离、`get_context_info`，绑定到一次性假对象。**不导入整个 pipeline、不实例化 VMemPipeline、不调用 initialize/编码器/模型。** 既有数值依赖足够；不需要新依赖。

## 最低输入及已有覆盖

来源固定为 `results/S40_declared_variant_generation/archive/events.jsonl`，下列都是成功动作 `operation_index=2`：

| 最低字段 | 已有 capture / 处理方式 |
|---|---|
| 四个原 target c2w、原 NMS 参数 None | seq 56 `context_input`。 |
| 567 个 surfel 位置/法线/半径、来源映射、五个 surfel 焦距 | seq 58 `render_input.map`；不读 color/RGB 或 `surfel_depths`。seq 58 同时保存实际 renderer pose/focal/kwargs，可独立比对入口。 |
| 原 renderer 三图、原权重/配额 | seq 60 / 62。原配额为来源 0–4 各 1。 |
| 阈值、候选、距离、排序、最终 indices | seq 64 `nms_threshold` / 66 `nms_selection`。候选和排序均 `[0,1,2,3,4]`；初始阈值 `0.04363296926021576`，结束阈值 `0.021042134095397264`，最终顺序 **`[0,2,4,1]`**，max_frames=4。trace 的 batch_2 seq 165 也保存同一顺序。 |
| 五份原 c2w/K、五份 latent/embedding 的 shape 和顺序、历史长度 5 | seq 68 `context_output.cache`。选择函数不改这些缓存，所以这份返回时快照可重建该次读取输入。 |
| 已保存的实际 context 条件/indices | seq 68 `context_info`，seq 70 `batch_input` 可交叉对应。 |

假对象最少有：`surfels, surfel_to_timestep, surfel_Ks, c2ws, Ks, latents, encoder_embeddings, pil_frames`；`pil_frames` 只需五个占位对象，因为这里仅用长度。配置：context=4、translation_distance_weight=0.1、NMS=True、surfel 512×288、device=cpu、dtype=float32、visualize=False。最后一项沿用 `work/S35_generation_integration/runtime_factory.py:82–84` 的实际覆盖；无需载入图片。长度为 5 且 NMS=True 会在本函数内重算 initial_threshold，无需伪造前次阈值。

本轮只核元数据及文件大小：最低数值集合 1666 个唯一 blob、1788224 字节，未发现缺失或大小不符；payload 内容尚未读取/再验 SHA，必须在实际使用时核描述中的字节身份。完整来源见旁边 `NEXT_INTEGRATION_SOURCE_INVENTORY.json`。

## 最小可执行检查与不能越过的边界

先让假对象调用原 `get_context_info`，原 renderer 的输出应对应 seq 60，原选帧顺序应为 `[0,2,4,1]`。latent/embedding 可各用按 frame ID 编码的固定人工数组，保持真实 shape `[4,72,72]` 与 `[1024]`，在输出逐 slot 查到同一 ID；原 c2w/K 仍用真实小数值。这能验证**选帧到四类缓存索引的接线**，不证明人工数组等于真实图像编码或模型条件。

随后仅把这个假对象的 renderer 依赖换成已审 S61 的调用适配，保留其余原函数和同一份输入，检查有效索引域/顺序与 gather 一致，并记录相对原结果变化。新单位会改权重和裁剪，不能事先要求所有选帧必然与旧顺序相同；若变化，需要如实解释，不能挑成功的子集。两个路径只是一份已有成功输入的局部回归，不是新场景或新矩阵；本轮未执行它们。

若要进一步证明“真实缓存条件逐值相同”，seq 68 已覆盖五份真实 latent、五份 embedding 以及两个 stack 输出，共另有 12 个唯一 blob / 783360 字节；当前只核存在和大小。它们是已有编码的数值载荷，不需模型，但不能用人工标记冒充已读/已比对。停止在人工 gather 即可完成当前最小索引问题，更强逐值检查由 root 另定范围。

仍不能由这一步验证：encoder 是否重新正确产出缓存；`get_cond` 的真实 concat/CLIP mean/Plücker 条件数值；改后条件如何影响去噪、第二批视频及质量；几何 producer/缓存尺度是否被修复。S61 的渲染副本归一化也未处理 NMS 中带平移权重的距离单位，不能宣称整个流程尺度不变。这里只交付明确入口和档案覆盖，无生产补丁、模型/RGB读取、新方法或 C2 完成声明。
