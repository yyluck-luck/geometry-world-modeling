# S17C：VMem嵌入CUT3R无先验建图与全局对齐组件

状态：运行前协议，真实执行与结果尚未发生。原始两张照片已在 S15A 使用；本阶段新增的是 VMem 自带 CUT3R 分支及其原生全局对齐的真实前向，不能称作未见图片评测、新算法、训练完成或完整视频。无论成功失败，都保留目录和中间数组。

## 研究问题和边界

这一阶段要确认：本机能否使用作者公开的完整 512 DPT 权重，通过 VMem 原函数，从两张照片得到经过相机/深度联合几何优化的稠密数组。它比单独 CUT3R 预测多了真实的 VMem 几何消费者，但仍没有创建 Surfel 对象、合并地图、选择记忆图片或调用视频生成器。

固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`。隔离副本及原文证据见 [接口方案](../work/S17C_interface_preparation/INTERFACE_PLAN.md)、[source_plan](../work/S17C_interface_preparation/source_plan.json)。只接受三处记录过的源码差异：`pos_embed.py` 的 CPU RoPE 分派、新增 `rope_cpu.py`（有符号位置，内部 FP32，返回输入 dtype），以及 `model.py` 显式 `weights_only=True`。原 `run_inference_from_pil`、`prepare_input_from_pil`、`prepare_output`、全局优化及清理函数不改。observer 仅包装、计数和保存，原函数每次委托一次、返回原对象。

本次使用 `poses=None, depths=None`，因此是“无先验”建图。原 VMem pipeline 会向这一入口提供已知姿态及已存深度；本次不冒充其完整在线状态。优化后的相机也不要求等于网络直接输出的相机头。正深度要求仅对相机坐标深度成立，世界坐标 Z 可以为负。

## 固定输入与执行

只允许 S15A Bonn 原 index 0/1，顺序不变，原生 RGB 640×480。SHA256 依次是 `7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39`、`77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae`。每张只由本进程打开/解码一次；PIL 处理后的 tensor 另存，验证颜色时不用再读照片。

权重是作者公开 `liguang0115/cut3r` 的 `cut3r_512_dpt_4_64.pth`，revision `b14faf986da0df405cff1b41e60e2975c4da2745`，必须完整 `3,173,761,006` B 且 SHA256 `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`。下载与完整校验回执由 root 冻结；partial 不能加载。安全反序列化只允许已审 S17B 的七个明确 globals，拒绝额外 globals，加载报告必须 all keys matched。

实际调用固定为：

```python
run_inference_from_pil(
    pil_images, model, poses=None, depths=None,
    lr=0.01, niter=400, device="cpu", size=512,
    visualize=False, save_flag=False,
    output_dir=fresh_output / "native_unused_output",
)
```

CPU 8 线程、模型 FP32、seed 0。在导入原 wrapper 后重设 Python、NumPy、Torch、OpenCV 随机种子，避免原文件 `random.seed(42)` 覆盖本次约定。原注意力中的 q/k FP16 转换及签名 RoPE 输入精度保持。数据按原 `prepare_input_from_pil` 长边 512 处理，得到 384×512；不使用 224 裁切替代。输入为两个更新历史帧，没有真实 ray/query。官方 `_encode_views` 仍会实际编码一个全零 dummy ray，须如实计为 1 次，不写成零算子调用。

整段入口不得放在 `torch.inference_mode` 下。原模型 inference 自有 no-grad；场景优化必须可微。只使用原函数创建的 Adam，优化场景参数，验证 optimizer 参数对象与网络参数对象不交叉，网络参数无梯度、仍 eval。不额外训练任何网络。

依赖安装在新 overlay，原 `.venv-cut3r` 不改。环境 agent 的实际安装与 import smoke 必须完成并冻结，接受的状态精确为 `PASS_IMPORT_ONLY_NO_MODEL`；这不代表模型运行成功。不能把最初 22 wheel 计划当作完整环境：首轮发现 `viz.py` 顶层另依赖 viser/sklearn，失败回执保留。runner 只消费已安装依赖，设置离线标记，不下载。运行时 NumPy 1.26.4、Torch 2.7.0、SciPy 1.16.2 必须来自原环境，不能被 overlay 替换。所有加载的嵌入源码模块必须位于隔离目录、登记在 manifest，且 SHA 匹配，拒绝独立 CUT3R/original VMem 混入。

## 原生对齐与记录

两帧形成原星形边 `[(0,1)]`。优化使用 frame0 的 self pointmap/conf_self 与 frame1 的 other pointmap/conf，不能用两个 self-depth 拼接冒充。原 `PointCloudOptimizer` 保持 MST 初始化、PnP 默认 10 次、`base_scale=.5`、`norm_pw_scale=True`、固定中心主点。保存实际 named parameters 的名字、形状、dtype、requires_grad。MST/PnP 返回情况也保存；PnP 返回 None 后原代码可回落 identity，有限矩阵不能被解释为定位成功。

原全局优化固定 400 次，线性学习率从 .01 到第399轮 `.0000259975`，原 Adam betas(.9,.9)。每次分别记录原 `global_alignment_iter` 调用和实际 `optimizer.step`，最终两者都须为400。每轮记录返回 loss、lr、UTC 和累计 step。该 loss 是当轮更新前的 loss，最后返回不是更新后最终目标。

为支持独立重算，在清理前额外执行且只执行一次 `torch.no_grad()` 场景目标求值，记 `postfinal_objective`；不 backward、不 step。总 scene forward/objective 调用401次，其中400次来自原优化，1次只读。此目标是带原始 log(confidence) 权重的逐点三维欧氏距离，不是 xyz 绝对值和。

清理沿原 `clean_pointcloud()` 默认 `tol=.001,bad_conf=0`，保留 i→j 顺序、in-place confidence 更新、torch.round 偶数舍入规则。前后相机、点、深度、focal、pp、颜色、pair transform/adaptor 必须逐元素完全相同；confidence 可降到0。无置信度过滤、无裁深度、无尺度/姿态真值拟合。

## 输出接口

运行入口 [run_s17c_embedded_geometry.py](../scripts/run_s17c_embedded_geometry.py)，CLI `--manifest ABS --output FRESH_DIR`。manifest schema `s17c-embedded-two-frame-geometry-manifest-v1`；顶层有 `python,runner,identities,source_root,source_commit,source_plan,overlay,dependency_plan,environment_receipt,import_smoke,checkpoint,history_images,control_files,overlay_files,contract`。所有 identity 为绝对 canonical path→SHA256。source_plan SHA固定 `e90ee3c071912ac594d6b41ed88be23321baae3bac60a221522d67cee4eb482d`，按其原198文件和3patch覆盖后得到确切隔离身份。control_files 与 overlay_files 明确列出，不能附加 GT/未来 RGB/轨迹或旧模型输出。

`contract` 的全部必需键值以源码 `EXPECTED_CONTRACT` 为可执行版本：2 history / 0 query、CPU8、seed0、512、384×512、FP32、400轮、lr.01、无pose/depth先验、无可视化/原生写图、600秒、32GiB RSS、外部监控必需、0主生成器/GT/video、1次 postfinal 只读目标。外 caller 负责资源终止与输出 seal；退出成功必须同时符合 caller 回执。

| 文件 | 数组与含义 |
|---|---|
| `predictions.npz` | `frame0_`/`frame1_` ×6原始头；pts3d_in_self_view、pts3d_in_other_view、rgb 为[1,384,512,3]，conf_self/conf为[1,384,512]，camera_pose为[1,7]；FP32 |
| `state.npz` | 最终5状态：state_feat/init_state_feat[1,768,768]、state_pos[1,768,2]int64、mem/init_mem[1,256,1536] |
| `history_poses.npz` | history_pose_encodings[2,7]、history_poses[2,4,4]，来自原始相机头，不是最终优化相机 |
| `processed_inputs.npz` | frame0_img/frame1_img，各[1,3,384,512]，原归一化输入 |
| `scene_constructed.npz` / `scene_after_mst.npz` | 构造后/初始化后10类场景数组，见下一段 |
| `scene_before_clean.npz` / `scene_after_clean.npz` | 最终优化、清理前后10类场景数组 |
| `final_result.npz` | 原返回拼接后 point_clouds/colors[2,384,512,3]、depths/confidences[2,384,512]、focal[2,1]、pp[2,2]、R[2,3,3]、t[2,3]；逐元素核对 scene_after_clean |
| `pnp_N.npz` | 当第N次 PnP 返回成功时，原返回 pose；失败仅记录 JSON，不发明姿态 |
| `optimization_trace.jsonl` | 400真实循环行，iteration、loss_before_step、lr、UTC、optimizer_steps |
| `run_metadata.json` | 状态、实际阶段时间/资源/调用计数、输入/源码SHA、所有array identity、优化与清理说明、错误及 traceback |

每份 scene NPZ 固定 `world_points[2,384,512,3],depths[2,384,512],confidence[2,384,512],poses[2,4,4],focal[2,1],pp[2,2],intrinsics[2,3,3],pw_poses[1,4,4],adaptors[1,3],colors[2,384,512,3]`。其中 pw_poses 已含 pair scale；不把它的左上3×3当单位旋转。

shape/有限性/相机深度及focal为正/旋转合法是运行完整性门，不是准确率。世界点、相机、尺度全部没有传感器评价。独立几何/clean 数值容差另见 [固定数值合同](S17C_INDEPENDENT_NUMERICAL_CONTRACT.md)，不得看真实结果后放宽。

## 失败、成本与后续

实际进程总界600秒和32GiB RSS是停止条件，非资源预测。原生400轮是否能在界内完成尚未测量。失败尽量保存 `scene_failure.npz`、已得原始数组、所有成功轮及错误；硬终止以最新已落盘阶段和 caller 为准，不能声称捕获到被杀死后的内存。资源超限/依赖错误与科学假设无关，仍保留。

作者人工自检只使用编造数组、scalar nn.Module 和 tiny fake scene，验证 observer 委托次数/400小步/401目标/返回对象/恢复以及正深度、反射、NaN、输入合同拒绝边界；不加载模型权重/原生照片/GT。不同作者随后源码前审与独立数值验证。root 冻结 manifest 并确认 S17B 已释放资源后才实际启动 S17C；本文件本身不是运行授权已执行证明。

结果报告必须继续标明组件范围。即便成功，也仍缺真实 VMem 主生成器与完整视频消费者；不能把这项工程验证包装成创新效果。
