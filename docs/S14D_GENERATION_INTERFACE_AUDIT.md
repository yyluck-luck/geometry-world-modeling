# S14D：只给目标相机、不读目标照片的 CUT3R 接口审计

记录于 2026-09-06，北京时间；机器回执给出准确 UTC。本次只读源码和已存 metadata，没有运行模型、读取 NPZ 数组、原图或 GT。

结论：官方源码有真实的 ray-only query 接口，可以先输入20张历史 RGB，再用历史状态和指定相机的射线图预测目标视角几何。现有 S6/S8 成功记录尚未测试这个接口：四个查询仍输入了各自的 RGB，只是不允许它们修改历史状态。两者不能混称。一个新的小规模接口探针值得执行，但其成功只证明接口、信息边界和有限输出，不证明新视角质量、检索增益或完整 VMem 视频效果。

## 1. 已核身份和证据等级

- 官方 checkout：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local`，当前 commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`；`/usr/bin/git status --porcelain --untracked-files=no` 返回空。默认 PATH 的 git 先因 `worktreeconfig` 扩展报错；随后使用系统 git，未更改仓库。
- VMem 固定快照 commit：`39291e4f272f6b4f270691d930926ab5930f942e`，来自项目 `vendor/provenance.json`；本次读 `vendor/vmem_snapshot/modeling/pipeline.py`，其 SHA 同已登记值。
- 阅读30份文件的身份在 `work/S14D_generation_interface/read_identity.json`，包含12份 CUT3R 文件、18份项目源码/日志/metadata。另读 Supervisor `vibe-research-workflow` 与本地 Claude `sci-scientific-critical-thinking` 技能；只应用源码检查、信息泄漏、代理指标和证据范围区分，不调用 Claude CLI/模型，不宣称用户已经完成个人学术判断或课程活动。
- 六份 S6/S8 metadata 的 query flags 均 `img_mask=True, ray_mask=False, update=False, reset=False`，其 state audit 均通过。另误选读了三份 S5 metadata，明确保留在 `metadata_fields.json`，没有把 S5 当作 S8。九份 metadata 的 JSON 被解码；零 NPZ、零图像、零 GT 内容。
- 本报告是源码可行性审查，不是 ray-only 运行成功凭证。图示可用下面数据流表达；此轮无需另外生成科研插画。

```text
20张历史真实RGB → CUT3R → 五元历史state + 历史预测相机
                              ↓ 固定保存/精确前后核对
历史预测相机 + 固定K + 预定小偏移 → ray_map → inference_step → 预测几何/颜色
目标真实RGB、目标GT、旧query预测、旧支持评分 ── 不进入该接口探针
```

## 2. 官方接口和冻结状态

源码行号按上述 commit：

1. `src/dust3r/inference.py:220–238`：`inference(history_views, model, device)` 返回 `(result, state_args)`。`loss_of_one_batch` 的 inference 分支调用 `model(batch, ret_state=True)`。全量历史20视图的 `_forward_impl` 为每帧计算特征后按顺序更新状态，返回21份快照；取 `state_args[-1]` 或索引20作为锚点。
2. 五元组顺序为 `(state_feat, state_pos, init_state_feat, mem, init_mem)`；`model.py:817–892` 给出初始化、历史更新和保存。既往 S6 的精确检查只关注 slot 0 和 slot 3；新探针应比较五项的 shape、dtype、finite 和精确值/字节 SHA，不能仅核 flag。
3. `src/dust3r/inference.py:242–263`：`inference_step(view, state_args, model, device)` 返回 `{'pred': ...}`。它调用 `model.inference_step(view, *state_args)`；不接收新的历史照片，也不返回更新状态。
4. `model.py:902–961`：`view['img']` 只用于 batch_size；每批必须 `ray_mask=True`。输入编码器只处理射线图。内部计算 `new_state_feat` 和 `new_mem`，但不把它们赋回锚点或返回；仍应运行前后实际核五元张量，因为静态审读不能代替运行证据。
5. `viser_utils.py:510–549` 的官方 GUI 已用 NaN 图像占位、ray-only flags 和最后一个历史 state_args 调用此接口；可直接作为最小 probe 的参考。
6. 既往 `scripts/run_s6_cut3r.py:240–250, 322–333` 会 `load_images` 所有24张，query 仍 `img_mask=True`；`update=False` 只限制状态写回，不阻止 query RGB 进入图像编码器。`scripts/run_cut3r_local.py` 原版对全部图像还都 `update=True`。不要把两脚本简单改名称当作生成接口。

建议保留旧加载/权重校验/签名 RoPE/同步传输逻辑于新 runner，原冻结脚本不改。只重新处理一个块的20张历史，是建立以前未保存的可执行 recurrent state 所必需的新接口准备；不要计为新的独立场景或重复扩大旧实验样本。

## 3. view schema、shape 和兼容风险

| 字段 | 最小 probe 的值 |
|---|---|
| `img` | FP32 `(1,3,224,224)` NaN 占位，不读取目标图像 |
| `ray_map` | FP32 `(1,224,224,6)`，每像素 `[origin_xyz, encoded_direction_xyz]` |
| `true_shape` | 显式 tensor `[[224,224]]`，语义为 H,W |
| `img_mask` / `ray_mask` | bool `[False]` / `[True]` |
| `update` / `reset` | bool `[False]` / `[False]` |
| `idx` / `instance` | 独立的探针 ID，不冒充旧20–23真实目标 |
| `camera_pose` | FP32 `(1,4,4)` identity 占位；目标实际相机已编码于 ray_map，这个字段不是决定预测的相机输入 |

- **通道轴陷阱：**既往 image-only runner 的无效射线占位是 `(B,6,H,W)`，因为 `ray_mask=False` 未被编码；有效射线必须 `(B,H,W,6)`。若将历史和ray混合用 `_encode_views`，所有视图射线 shape 必须一致。建议先独立历史 inference，再单步 ray-only，避免混合 stack 风险。
- **`true_shape` 潜在缺陷：**官方 `model.py:922` 构造 tensor `shape`，下一行却向 `_encode_ray_map(raymaps, shapes)` 传 Python list。`ManyAR_PatchEmbed.forward` 要求 `.shape`，会有风险；但此处官方 `.pth` 的 `load_model:76–79` 会将 ManyAR 字符串替换成 `PatchEmbedDust3R`，后者 `forward(x, **kw)` 不消费 true_shape。现有 checkpoint_load 显示默认 PatchEmbedDust3R；所以当前加载路径无需凭想象加新 adapter。新 runner 应实际 assert ray patch class 和 head/size 并记录。若不同加载路线遇到问题，另存失败、新 adapter 和审查；不得偷偷改旧模型。
- **省略 shape 的陷阱：**`view.get` 默认从 ray_map 的 `shape[-2:]` 取得 `(W,6)`，因此永远显式传 `(H,W)`。`demo.py` 的混合视图分支还反转 H/W；正方形会掩盖错误。建议本轮用224正方形，记录未验证非正方形。
- **RoPE 和 MPS：**pose token 位置为 `(-1,-1)`。沿用已验证的 signed RoPE adapter，先核其文件和验证回执身份；同步 staging 是现有兼容措施。CPU FP32 为首轮，保留8线程、seed0。`inference_step` wrapper 的 CUDA autocast 参数为 disabled，不构成 GPU需求。
- **RGB输出含义：**已存 checkpoint_load 为 `rgb_head=True`。有预测颜色不代表调用了扩散视频模型；不得把该输出渲染成示意图后宣称完整 VMem 视频。

## 4. 射线、坐标和相机信息来源

`src/dust3r/datasets/base/base_multiview_dataset.py:13–23` 的训练构造以 `inv(first_c2w) @ target_c2w` 表示目标相机；`viser_utils.py:453–465` 则直接接受其当前 viewer/model 坐标中的 c2w。

代码的六维表示不是 Plücker：令相机为 `[R,t]`，像素 `p=[u,v,1]`，代码实际计算

`origin = t; encoded_direction = normalize(R @ inv(K) @ p + t)`。

这里**确实包含平移 t**；不能在适配时悄悄改成通常的 `normalize(R @ inv(K) @ p)`。这份源码审计不推断作者为何选择这个表示，也不把它当作创新。最小 probe 应精确复现官方训练/GUI共同写法，并用纯人工 K/pose 做独立公式检查。若日后研究标准几何射线，应单独提出分布变化实验。

- 历史模型输出的 c2w 在模型预测坐标系；不是已校准的米制外部世界轨迹。新 probe 可取此次20历史推理中最后历史帧的 c2w，再按预先固定规则作小偏移。所有偏移必须标明预测尺度/轴，不叫真实厘米移动。
- 推荐本轮固定 pseudo K，按官方 `generate_pseudo_intrinsics:447–451` 用 `f=sqrt(224^2+224^2)`，`cx=cy=112`，不从目标照片估计焦距。它是有效、可追溯的接口输入，不是 TUM 真标定。也可只用历史重建估K，但将引入额外算法，应另记录。
- 既往 query c2w 是目标 RGB 输入产生的预测；即使存成 JSON/NPZ，也不能因此声称它在生成之前可用。目标 GT pose 则是外部答案，若进入轨迹就需把任务称为给定真轨迹条件评估，不能伪装自主预测。本轮均不读取。
- 本轮无需用真实相机 K 去迁就图像裁剪。若后续做实测目标对齐，必须明确 `load_images` 的先resize到512×384、再等比resize、再中心crop224流程（`utils/image.py:228–247`），同步变换K并保持坐标约定，不能直接拿640×480标定数值。

## 5. 与 VMem 的接口差异

固定 `vendor/vmem_snapshot/modeling/pipeline.py`：

- `get_context_info(target_c2ws):505–...` 接受目标相机轨迹来选择历史；635–646 对目标平均pose做变换，并用历史 surfel Ks 均值的0.65倍进行投影检索。此处无真实目标RGB输入。
- `_generate_frames_for_trajectory:1195–...` 接受 `c2ws_tensor, Ks_tensor`，1245–1268把目标相机和K与检索的历史条件组装，再调用生成器。`get_cond:1120–...` 另有相机坐标轴翻转、尺度调整和 **Plücker** 编码，和 CUT3R `[origin,encoded_direction]` 不是可直接互换的6通道张量。
- `__call__:1408–1429` 是初始图像加完整相机/K轨迹。目标轨迹可外给，后续生成帧再进入记忆更新。现有离线 query RGB 几何诊断只模拟其中一部分数据处理，不等价于这个自回归生成入口。
- 因此 ray-only probe 能补“目标RGB不可用时可否执行几何查询”这一接口缺口，但单独不打通 VMem checkpoint/生成器、选图效果或视频质量链路。

## 6. 可实作的最小 probe 与成功/失败门

冻结新 runner、manifest、20历史文件身份、官方源码/权重/adapter身份、4个目标pose确定规则、固定pseudo K、输出路径及预算；由不同作者前审后才运行。建议只用 S6 block0 的前20历史图，不输入四张旧 query。四个目标为最后历史预测pose、其预定 x正/x负/y正小偏移（尺度规则由根在运行前固定），每次使用同一个 anchor。

```python
history_outputs, state_args = inference(history_views_20, model, 'cpu')
anchor = state_args[-1]
anchor_reference = tuple(t.detach().clone() for t in anchor)
# poses 来自这次 history 输出；K 为冻结 pseudo K；不用任何旧 query/GT。
for pose in frozen_rule(history_outputs):
    view = make_official_ray_view(pose, K, H=224, W=224)
    output = inference_step(view, anchor, model, 'cpu')
    # 保存全部 pred 数组、pose/K/ray身份和输入读取台账。
    # 每次核五个 anchor 张量 finite/shape/dtype/exact，不写回 query。
```

成功门：历史加载恰好20、目标RGB/GT/旧query预测读取0；四个schema/masks符合冻结值；所有输出required keys、shape和finite通过；全部state精确不变；四个固定输入都保留，不按图片好看挑选。若同一输出出现只是记录，不设事后差值阈值裁成“有效视角感知”。有限输出也不意味着几何准确。任一失败保存完整目录和traceback；不要修参数后覆盖失败证据。

独立核验至少检查 ray 数值公式与shape、4目标pose规则、输入读取边界、state精确值、输出保存和metadata一致。可额外在不运行模型的纯人工检查中确认更换NaN占位图不引入图像编码器读取；未经实际检查不能只靠flag宣称隔离。

下一步：根实现新 runner，当前审计作者可做不同作者的运行前审查；执行者之后还需结果独立复核。尚未证明创新算法，尚未生成完整视频。
