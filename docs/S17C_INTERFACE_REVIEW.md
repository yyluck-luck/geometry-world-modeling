# S17C 独立接口与数值边界前审

审查范围：VMem 固定源码中的 `extern/CUT3R/surfel_inference.run_inference_from_pil`，同一 Bonn 实拍索引 0/1 的预定两图组件。当前证据为源码阅读与人工数组检查，**没有读取权重或实拍，没有运行模型或全局优化器**。本文件不是 S17C 运行结果，也不是尚未完成 runner 的代码冻结批准。实际审查时间、源码与脚本身份见 `work/S17C_independent_preparation/review_receipt.json`。

采用 Supervisor `idea-evaluator` 的致命缺口约束与本地 Claude `sci-scientific-critical-thinking` 的证据/混杂区分：原接口跑通只支持组件完整性，不支持新方法、几何精度或视频质量。这里应用的是已有技能规则，不调用 Claude 模型。root 负责主账，独立审查仅写本报告和专用准备目录。

## 1. 首要范围区别

VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 的 `modeling/pipeline.py` 在 `construct_and_store_scene` 中，把已有 `self.c2ws` 的第 1、2 列取反后传入 `poses`；已有 `surfel_depths` 非空时也传入。优化器的 `preset_pose` 冻结给定相机，并关闭 pairwise scale normalization；`preset_depth` 冻结传入的旧深度。此相机来自 VMem 自身状态，不在此认作 Bonn 传感器真值。

**S17C 拟用 `poses=None, depths=None`，属于官方 wrapper 的无先验建图/全局对齐入口。** 它允许优化相机和深度，保留默认尺度归一化，和 VMem 正式构图调用的约束不同。不得写成完整 pipeline 同约束复现。未来给定 S17B 预测相机是另一个输入合同，不能伪装成真实相机；本轮不临时加入。

本轮还没有 surfel 转换/融合、历史检索、主生成器、VAE、CLIP、GT 评分、渲染视频或视频评测。wrapper 名含 surfel 也不证明已经运行 surfel memory。

## 2. 原调用和预定接口

| 项目 | 原源码事实与 S17C 必须保留的约定 |
|---|---|
| 输入 | 两张已授权 Bonn RGB，固定原索引 0/1；无新增照片、GT、ray query |
| 图像转换 | `prepare_input_from_pil`：EXIF transpose → RGB → 长边 512，缩小时 LANCZOS → 居中 16 倍数裁切 → ImgNorm |
| 尺寸 | 原生 640×480 → 512×384，无额外裁切；各 tensor `[1,3,384,512]`，true_shape `[[384,512]]` |
| flags | idx 0/1，image true、ray false、update true、reset false；相机占位 identity 不等于给定相机约束 |
| views | 原 wrapper `revisit=1, update=True`；`prepare_input_from_pil` 当前实现不使用传入 raymaps/revisit/update 改变内容，不能据签名夸大支持 |
| 网络 | 原 `src.dust3r.inference.inference(views, model, cpu)` 一次；内部 `torch.no_grad`，autocast 关闭；不重跑原模型 |
| 边 | 以第 0 张为 anchor 的定向星形图；两图仅 `(0,1)`，非 `(1,0)` 或双向对称输入 |
| 点/权重 | 边 i 端使用 frame0 `pts3d_in_self_view` 和 `conf_self`；j 端使用 frame1 `pts3d_in_other_view` 和 `conf` |
| 对齐 | `GlobalAlignerMode.PointCloudOptimizer`，`init='mst'`, `schedule='linear'`, `lr=.01`, `niter=400` |
| 真正 niter 来源 | `configs/inference/inference.yaml:35–36` → `pipeline.py` 的构图调用；wrapper 默认 300、construct 默认 1000 均不是此配置的实际值 |
| 输出 | 返回五 key 的 dict：`point_clouds`, `colors`, `depths`, `confidences`, `camera_info` |
| 保存/显示 | `save_flag=False, visualize=False`；runner 自己记录 NPZ，不触发原 PNG/GIF/viser 输出 |

嵌入源码有混合 `src.dust3r.*` / `dust3r.*` 导入；最终 runner 必须记录实际每个已加载模块文件 SHA，并确保都来自隔离副本，不能仅凭 sys.path 优先级声称隔离成功。

原 wrapper 的无效 `ray_map` 占位为 `[1,6,H,W]`，而模型有通用 BHWC→BCHW 的 permute。该形状对真正 ray 输入不能直接推广；此合同所有 ray_mask=False，模型使用自己构造的零 dummy `[1,6,H,W]` 一次并乘零，原占位不会进入有效 ray 编码。必须保留有效 ray 计数为零与 dummy hook 一次的区别，不顺便修改接口来掩盖原行为。

## 3. 优化和输出语义

1. MST 根据点和置信初始化；两图第一相机先 identity，另一相机由 `fast_pnp` 初始化，默认 `niter_PnP=10`；失败时原实现可回落 identity。**不是直接使用 CUT3R `camera_pose` head 作为最终相机**。应观察并记录原 PnP 调用及返回成功状态，不能把 fallback 后 finite 视为定位成功。
2. 默认 `dist='l1'`；残差由原边预测点与由优化后的深度/内参/相机重新构成的世界点比较。两端分别除以各自 total area 后相加，权重是原置信的 `log`。此目标下降不等于对传感器 GT 更准。
3. 默认 `optimize_pp=False`，主点固定 `(W/2,H/2)`，即 `(256,192)`。焦距为每图一个正值、fx=fy；深度通过指数参数化为正。相机为 **camera-to-world**；点/平移/深度使用模型任意尺度，不报告米制精度。
4. `norm_pw_scale=True, base_scale=.5` 是无先验入口的默认值。给定相机时原实现关闭这一归一化，故不能直接拿两入口的原始绝对坐标作精度比较。
5. Adam `betas=(.9,.9)`；400 个 step 的索引为 0..399，学习率为 `.01 + (1e-6-.01)*i/400`。最后实际 step 为 `.0000259975`，不会恰好到 `1e-6`。
6. `global_alignment_iter` 先算 loss，再 backward/step，返回的是该 step 更新前 loss。最终 wrapper 的返回 loss 是第 399 步更新前目标；若另存第 400 次更新后的 objective，需要单独命名和一次无更新计算，不能认为二者必等或重跑优化。
7. clean 在优化后运行，**仅降低 `scene.im_conf`，不改变 points/depths/poses/focals**。原损失权重已预计算，不能拿 clean 后 conf 重新算原优化目标。
8. clean 按 source i、target j 顺序执行。将世界点用 `inverse(c2w_j)` 投到 j，相机 z>0、像素在界内且 `z_projected < .999*depth_j`、当前 `res[i] < res[j]` 才降至 0。取整使用 Torch `.round()`（ties-to-even），不是此前实验的 `floor(x+.5)`；`res` 随循环改动，独立复算需保留顺序。它是原方法的跨视角过滤规则，不是可见性/遮挡真值证明。

预定主输出应逐图完整保留，不能根据 clean confidence 删除点：

| 字段 | 各图/总体 shape | 语义与独立检查 |
|---|---|---|
| point_clouds[i] | `[1,384,512,3]` | 优化后世界坐标；独立由 depth、focal、pp、c2w 重构 |
| depths[i] | `[1,384,512]` | 相机 z，不是欧氏距离；正数、有限性与完整分母 |
| confidences[i] | `[1,384,512]` | 已 clean，`get_conf(mode='none')` 未取 log；允许 0，非概率 |
| colors[i] | `[1,384,512,3]` | `scene.imgs` 来自归一化输入反变换，RGB `[0,1]`，**不是预测 rgb head** |
| camera_info.focal | `[2,1]` | 正焦距 fx=fy |
| camera_info.pp | `[2,2]` | 默认中心 `(256,192)`，不另加 `.5` |
| camera_info.R/t | `[2,3,3]` / `[2,3]` | 优化后 c2w 的旋转/平移；正交性、det≈1，不能要求等于 raw pose head |

raw 六 heads×两帧与五 state 可用只委托 observer 额外保存，和以上优化输出分文件命名。它们的真正 shape/dtype/identity 由最终 runner 合同和实际输出核验；不得拿 S17B 保存结果替代 S17C 的真实调用。

## 4. 透明适配边界

执行作者正在准备 isolated_vmem_source，拟改嵌入 `pos_embed.py` 并新增 signed CPU `rope_cpu.py`，以及唯一 `model.py` 的 `torch.load(weights_only=False)`→`True`。RoPE 的内部 FP32/接口 dtype 行为要单独记录，不能无证据声称与作者 CUDA 核 bitwise 等价；依据既有 S17 CPU 人工预检，不代表完整模型已经适配成功。

安全加载必须绑定完整官方权重 SHA、ZIP 完整性和有限的 OmegaConf 类型 allowlist；不应因为缺依赖而改回任意反序列化。公开权重尚未完成时不得提前加载。S17C 独立 source/overlay 不修改待运行 S17B 的 runner、adapter 或基础环境。

其余原 wrapper/forward/优化/clean 函数保留。observer 应只包裹并原样返回结果；存储时 detach/cpu/clone，不改 flags、张量值、优化器 step 次数、原参数和模块 RNG。依赖 overlay 不应默默覆盖已有 Torch/NumPy/SciPy 等基础版本。最终须核实际 loaded module 文件，记录所有改动补丁；此时作者 runner 尚在准备，因此不在这里提前签署执行 PASS。

## 5. 不同作者独立核验的最小合同

- 冻结前核 source diff、checkpoint 与两图身份、Python/依赖路径、固定 CLI 和 600s/32GiB 合同；外监控是资源约束，不称 OS 硬隔离。输出 fresh 目录，失败产物保留。
- 运行 observer 记录输入两图转换/flags、一次真实 forward、有效 ray=0、dummy=1、边 `(0,1)` 与两端 head 绑定、全局 400 次真实 step/学习率/loss、MST/PnP 返回、优化参数名/shape/requires_grad、clean 前后置信/几何快照，以及最终 module 来源。模型权重没有被 optimizer 使用；这属于 scene 优化，不是模型训练。
- 正式核验只读封存的预测/scene/输入 tensor 数值快照与 metadata。不要再读新 RGB/GT，不重跑 CUT3R。SHA 覆盖并确认保存身份；任何不完整字段不得自动填入默认成功值。
- NumPy/SciPy 独立由 `X_cam=((u-ppx)z/f,(v-ppy)z/f,z)`、`X_world=R*X_cam+t` 复算所有输出点；逆变换检查 z 与像素 grid。禁止偷偷调尺度/旋转对齐来让身份检查通过。
- 独立从输入归一化 tensor 验 RGB 反变换；从原 frame0 conf_self/frame1 conf 验 clean 前最大聚合（单边时就是对应 head）。再按相同循环顺序/取整/严格不等式复算 clean 后置信并核几何未改。保存 valid/outside/behind/cleaned 的完整统计。
- 若保存原 optimizer 参数/中间目标，按原 log 权重及两端 area 重算目标；前后目标和 loss 列表 finite 不代表必须每步单调下降，不增设事后择优截断。数学容差需在真实执行前由最终 schema 固定并标明 float32 累加顺序差别。

## 6. 已完成的小人工检查

`work/S17C_independent_preparation/check_interface_math.py` 从固定原源码 AST 仅提取 `geotrf`、`rgb`、`linear_schedule`、`_fast_depthmap_to_pts3d`、`clean_pointcloud`，不 import 完整模型。由不同作者 NumPy 手算或直接列期望，检验相机 z 反投影、非平凡 c2w 旋转平移及逆变换、严格深度/置信过滤、geometry 不变、`.5` ties-to-even/outside 保留、RGB 反归一化、400 step 终点和尺寸算术。

真实运行回执 `work/S17C_independent_preparation/artificial_v1/receipt.json` 为 **PASS_ARTIFICIAL_ONLY**。它运行的是九项小型人工断言，不是九个科研实验；没有模型、真实图像、权重、GT 或全局优化。只说明所测约定可按原代码重现。下一步由执行作者完成 runner，独立前审其 observer/字段与本合同一致后，再交 root 冻结和实际运行。
